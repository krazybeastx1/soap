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
    <title>Soap JWT Challenge</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f0f8ff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            width: 360px;
            text-align: center;
        }
        .soap-img {
            width: 120px;
            height: 120px;
            margin-bottom: 20px;
        }
        h2 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        p.desc {
            color: #7f8c8d;
            margin-bottom: 25px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #34495e;
        }
        input[type=text] {
            width: 100%;
            padding: 12px;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            box-sizing: border-box;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background 0.3s;
        }
        button:hover {
            background: #2980b9;
        }
        #result {
            margin-top: 25px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 5px;
            font-size: 14px;
            text-align: left;
        }
        code {
            background: #bdc3c7;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        ul {
            text-align: left;
            padding-left: 20px;
            margin-top: 10px;
        }
        .hint {
            color: #27ae60;
            font-weight: bold;
            margin-top: 10px;
            display: block;
        }
    </style>
</head>
<body>
<div class="container">
    <!-- Soap SVG -->
    <svg class="soap-img" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <rect x="10" y="10" width="80" height="80" rx="15" ry="15" fill="#e8f4fc" stroke="#3498db" stroke-width="2"/>
        <circle cx="50" cy="30" r="12" fill="#3498db"/>
        <circle cx="30" cy="50" r="12" fill="#3498db"/>
        <circle cx="70" cy="50" r="12" fill="#3498db"/>
        <circle cx="50" cy="70" r="12" fill="#3498db"/>
        <text x="50" y="90" text-anchor="middle" font-family="Arial" font-size="12" fill="#2c3e50">SOAP</text>
    </svg>
    <h2>Login to Forge JWT</h2>
    <p class="desc">Enter your username to receive a token, then forge an admin token to capture the flag.</p>
    <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" id="username" placeholder="Enter username" required>
    </div>
    <button id="loginBtn">Login</button>
    <div id="result"></div>
</div>
<script>
    document.getElementById('loginBtn').addEventListener('click', async () => {
        const username = document.getElementById('username').value.trim();
        if (!username) {
            alert('Please enter a username');
            return;
        }
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        const data = await response.json();
        const resultDiv = document.getElementById('result');
        if (response.ok) {
            resultDiv.innerHTML =
                `<p>Token: <code>${data.token}</code></p>` +
                `<div class="hint">Hint: Decode this token at https://jwt.io to see the header and payload.</div>` +
                `<p>Then:</p>` +
                `<ul>` +
                `<li>Change the payload "sub" to "admin" and "role" to "admin"</li>` +
                `<li>Change the header "alg" from "RS256" to "HS256"</li>` +
                `<li>Sign the modified token using HS256 with the <strong>public key</strong> (found in public.pem) as the secret</li>` +
                `</ul>` +
                `<p>Use the forged token in the Authorization header to access /profile and get the flag.</p>`;
        } else {
            resultDiv.innerHTML = `<p>Error: ${data.error}</p>`;
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
