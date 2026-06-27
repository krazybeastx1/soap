# JWT Algorithm Confusion Challenge

## Files
- `app.py` - Vulnerable Flask web app with static soap image page and login
- `public.pem` - RSA public key (distributed to players)
- `private.pem` - RSA private key (for reference, normally secret)
- `flag.txt` - Flag to capture
- `requirements.txt` - Python dependencies
- `Dockerfile` - Optional containerization
- `WRITEUP.md` - Detailed writeup
- `BURP.md` - Burp Suite instructions

## Setup
```bash
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000 to see the soap-themed login page.

## Challenge Description
The web app issues JWT tokens signed with RS256 using a private key. The verification code trusts the `alg` header and uses the public key as:
- RS256 verification key when `alg=RS256`
- HMAC-SHA256 secret when `alg=HS256`

This allows an attacker to:
1. Enter a username and click Login to get a token via `/login`
2. Decode it, change `sub` to admin and `role` to admin
3. Change header `alg` from RS256 to HS256
4. Re-sign using HS256 with the public key as secret
5. Present forged token in Authorization header to `/profile` to get the flag

## Exploitation Steps (via browser or Burp)
1. Visit http://localhost:5000, enter any username, click Login to obtain a token.
2. Decode the token (e.g., jwt.io) to see header `{"alg":"RS256","typ":"JWT"}` and payload.
3. Modify payload: `"sub":"admin","role":"admin"`.
4. Change header `alg` to `HS256`.
5. Re-sign using HS256 with the **public key** (found in public.pem) as the secret.
6. Set token in Authorization header and access `/profile` (e.g., using Burp Repeater or curl).

See `BURP.md` for detailed Burp Suite instructions.

## Learning Objectives
- Understand JWT structure and algorithm confusion
- Learn to inspect and modify JWT tokens
- Recognize the danger of trusting the `alg` header
- Practice using Burp Suite for token manipulation

## Difficulty
Easy-Medium: The vulnerability is clear in source but requires token manipulation.

