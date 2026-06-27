from flask import Flask, request, jsonify, render_template_string
import jwt
import datetime

app = Flask(__name__)

# Load keys
with open('private.pem', 'r') as f:
    PRIVATE_KEY = f.read()
with open('public.pem', 'r') as f:
    PUBLIC_KEY = f.read()

# Simple HTML login page
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>
    <h2>Login</h2>
    <form id="loginForm">
        <input type="text" id="username" placeholder="Username" required>
        <button type="submit">Login</button>
    </form>
    <div id="result"></div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            const data = await response.json();
            if (response.ok) {
                document.getElementById('result').innerHTML = 
                    `<p>Token: <code>${data.token}</code></p>` +
                    `<p>Decode it at https://jwt.io to see the header and payload.</p>` +
                    `<p>Try to forge an admin token by changing the algorithm to HS256 and signing with the public key.</p>`;
            } else {
                document.getElementById('result').innerHTML = `<p>Error: ${data.error}</p>`;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return LOGIN_PAGE

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', 'guest')
    # Normal user token (not admin)
    payload = {
        'sub': username,
        'role': 'user',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
    return jsonify({'token': token})

@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    try:
        # Get header without verification to see algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get('alg')
        
        # Vulnerable verification: trust the algorithm from header
        if alg == 'RS256':
            # Verify with RS256 using public key
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        elif alg == 'HS256':
            # VULNERABILITY: Treat public key as HMAC secret
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=['HS256'])
        else:
            return jsonify({'error': 'Unsupported algorithm'}), 401

        if payload.get('role') == 'admin':
            with open('flag.txt', 'r') as f:
                flag = f.read().strip()
            return jsonify({'message': f'Welcome admin! Flag: {flag}'})
        else:
            return jsonify({'message': f'Hello {payload.get("sub")}'}), 200
    except jwt.InvalidTokenError as e:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
