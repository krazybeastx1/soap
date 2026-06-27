# Burp Suite Instructions for JWT Algorithm Confusion

## Setup
1. Start the vulnerable app: `python app.py`
2. Configure your browser to use Burp Suite as proxy (usually 127.0.0.1:8080)
3. Visit http://localhost:5000 in your browser

## Steps

### 1. Obtain a legitimate token
- Click "Login as testuser" or enter any username and click Login
- In Burp, intercept the POST to `/login`
- Forward the request and capture the response
- Copy the JWT token from the JSON response: `{"token":"<JWT>"}`

### 2. Send to Intruder for manipulation
- Right-click the response → "Send to Intruder"
- In Intruder tab, go to Positions
- Clear § markers, then add § around the token value in the JSON:
  ```
  {"token":"§jwt_token_here§"}
  ```
- Go to Payloads tab
- Load payloads: You can use a simple list with one payload (the token) or use multiple payloads for brute force (not needed)
- Actually easier: use the "Repeater" tab for manual editing:
  - Right-click the response → "Send to Repeater"
  - In Repeater, edit the JSON to change the token later

### 3. Decode and modify token
- In Repeater, you have the response. Extract the token.
- Go to any JWT decoder (e.g., https://jwt.io) or use Burp's built-in decoder:
  - Select the token → right-click → "Decode as" → "Base64"
  - You'll see header and payload.
- Alternatively, use Burp Sequencer or just manually edit:
  - Copy token to editor
  - Split by '.': `header.payload.signature`
  - Decode header and payload (base64url)
  - Modify payload: change `"sub"` to `"admin"` and `"role"` to `"admin"`
  - Change header: `"alg"` from `"RS256"` to `"HS256"`
  - Re-encode header and payload (base64url-safe base64url encode with -, / with _, remove padding =
- Now you need to sign with HS256 using the public key as secret.
  - You can do this with Burp Sequencer? Not directly. Use external tool or Python.
  - Simpler: Use the provided public key to sign.

### 4. Sign with HS256 using public key
- Save the public key from `public.pem` (copy the content)
- Use Python in Burp's interpreter or external:
```python
import jwt
public_key = open('public.pem').read()
header = '{"alg":"HS256","typ":"JWT"}'
payload = '{"sub":"admin","role":"admin","expiry":...}'
# Encode header and payload
import base64, json
def enc(x): return base64.urlsafe_b64encode(json.dumps(x).encode()).rstrip(b'=')
# Then sign:
token = jwt.encode(json.loads(payload), public_key, algorithm='HS256')
# But need to include header; jwt.encode will set alg from param.
```
- Or use jwt.io website: set algorithm to HS256, paste public key as secret, edit payload.

### 5. Replace token and forward
- In Repeater, replace the token in the Authorization header or in the JSON if the endpoint expects token in body (our app expects Authorization: Bearer <token>)
- Actually our `/profile` expects Authorization header.
- So create a new GET request to `/profile`:
  - GET http://localhost:5000/profile
  - Header: Authorization: Bearer <your_forged_token>
- Send and observe response containing flag.

### 6. Automate with Intruder (optional)
- If you want to brute force the signature (not needed), you can use Intruder with payloads from a wordlist, but here we have the key.

## Tips
- The public key is PEM format; when using as HMAC secret, use the entire file content including headers.
- Ensure you use URL-safe base64url encoding without padding for header and payload.
- Verify your forged token on jwt.io (set algorithm to HS256, secret as public key) to ensure signature verifies.

## Expected Result
If successful, response from `/profile`:
```json
{"message":"Welcome admin! Flag: HTB{jwt_alg_confusion_123}"}
```

## Alternative: Use Burp JS Engine
You can write a small JavaScript extension to sign, but manual is fine for learning.

Happy hacking!
