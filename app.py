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
    <title>Login - JWT Challenge</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
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
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 320px;
        }
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        input[type=text] {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0056b3;
        }
        #result {
            margin-top: 20px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
        }
        code {
            background: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
        }
        ul {
            text-align: left;
            padding-left: 20px;
        }
        .hint {
            color: #28a745;
            font-weight: bold;
        }
    </style>
</head>
<body>
<div class="container">
    <h2>Login</h2>
    <form id="loginForm">
        <input type="text" id="username" placeholder="Username" required>
        <button type="submit">Login</button>
    </form>
    <div id="result"></div>
</div>
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
                `<p class="hint">Hint: Decode this token at https://jwt.io to see the header and payload.</p>` +
                `<p>Then:</p>` +
                `<ul>` +
                `<li>Change the payload "sub" to "admin" and "role" to "admin"</li>` +
                `<li>Change the header "alg" from "RS256" to "HS256"</li>` +
                `<li>Sign the modified token using HS256 with the <strong>public key</strong> (found in public.pem) as the secret</li>` +
                `</ul>` +
                `<p>Use the forged token in the Authorization header to access /profile and get the flag.</p>`;
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
