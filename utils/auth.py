"""JWT signing and verification helpers."""
import base64
import datetime
import hashlib
import hmac
import json
import os

import jwt

from utils.helpers import load_file

PRIVATE_KEY = load_file("private.pem")
PUBLIC_KEY = load_file("public.pem")

ALG_RS256 = "RS256"
ALG_HS256 = "HS256"
JWT_COOKIE = "soap_token"
QUEUE_COOKIE = "soap_queue"

TOKEN_LIFETIME = datetime.timedelta(hours=1)


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def issue_token(sub: str, role: str, queue: str) -> str:
    """Sign a JWT for the given subject using RS256 and the private key."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "queue": queue,
        "iat": int(now.timestamp()),
        "exp": int((now + TOKEN_LIFETIME).timestamp()),
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALG_RS256)


def _verify_hs256_manually(token: str, key: str):
    """
    Hand-rolled HS256 verify that intentionally treats the PEM public key
    as the HMAC secret. PyJWT refuses this combination, so we do it here
    to preserve the original challenge vulnerability.
    """
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        return None, "Malformed token"

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    try:
        provided_sig = _b64url_decode(signature_b64)
    except Exception:
        return None, "Malformed signature"

    expected_sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        return None, "Invalid token: signature mismatch"

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as exc:
        return None, f"Malformed token: {exc}"

    if header.get("alg") != ALG_HS256:
        return None, "Algorithm mismatch"

    if "exp" in payload:
        now = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
        if int(payload["exp"]) < now:
            return None, "Token expired"

    return payload, None


def verify_token(token: str):
    """
    Intentionally vulnerable verifier. Trusts the `alg` header from the
    incoming token. RS256 -> public key verify. HS256 -> public key as
    HMAC secret. Classic algorithm confusion: a holder of the public
    key can sign HS256 tokens that pass.
    """
    if not token:
        return None, "Missing token"

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        return None, f"Malformed token: {exc}"

    alg = header.get("alg")
    if alg == ALG_RS256:
        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALG_RS256])
            return payload, None
        except jwt.InvalidTokenError as exc:
            return None, f"Invalid token: {exc}"
    if alg == ALG_HS256:
        # Vulnerable branch: treat PEM as HMAC secret.
        return _verify_hs256_manually(token, PUBLIC_KEY)
    return None, "Unsupported algorithm"


def current_user_from_cookie():
    """Read JWT cookie from a Flask request and return its payload."""
    from flask import request

    token = request.cookies.get(JWT_COOKIE)
    if not token:
        return None
    payload, _ = verify_token(token)
    return payload
