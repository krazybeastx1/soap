# INSTRUCTIONS

Setup, run, and organizer notes for the **SOAP Company Token Queue** CTF
challenge. Intended for both players (setup) and organizers (deployment,
key/flag rotation).

---

## 1. Project structure

```
soap/
├── app.py                       # Flask entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── flag.txt                     # Flag served to admin role (organizer only)
├── private.pem                  # RS256 signing key (organizer only)
├── public.pem                   # RS256 verifying key (public — shipped to players)
│
├── blueprints/
│   ├── auth_bp.py               # /, /queue, /api/queue/regenerate, /login, /logout
│   ├── dashboard_bp.py          # /dashboard
│   └── profile_bp.py            # /profile  ← challenge endpoint
│
├── templates/
│   ├── base.html
│   ├── queue.html               # /queue — animated waiting page
│   ├── login.html               # /login — queue-number form
│   ├── dashboard.html           # /dashboard
│   ├── profile.html             # /profile
│   └── error.html
│
├── static/
│   ├── css/  (style, queue, login, dashboard, profile)
│   ├── js/   (queue, login, dashboard)
│   └── images/  (favicon.svg, logo.svg)
│
└── utils/
    ├── auth.py                  # JWT mint (RS256) + alg-confusion verify (HS256)
    ├── queue.py                 # SOAP-NNNNNN issuance + cookie wiring
    └── helpers.py               # PEM/flag loaders
```

---

## 2. Application flow

```
Visitor
  → /queue          random SOAP-NNNNNN issued, JWT minted into HttpOnly cookie
  → 5s countdown
  → /login          visitor enters their queue number
  → /dashboard      corporate landing
  → /profile        JWT claims shown; flag revealed only when role=admin
```

---

## 3. Quick start

### Option A — Docker (recommended)

```bash
docker compose up --build
```

Open http://localhost:5000.

To run on a different port, edit `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"   # host:container
```

### Option B — Local Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Listens on `http://0.0.0.0:5000` by default. Override with `PORT=8080 python app.py`.

---

## 4. Configuration

| Variable      | Default                  | Purpose                          |
| ------------- | ------------------------ | -------------------------------- |
| `PORT`        | `5000`                   | Port the Flask app binds to      |
| `SOAP_SECRET` | `soap-company-default`   | Flask session signing key        |

The JWT keys (`private.pem`, `public.pem`) and flag (`flag.txt`) live in
the project root and are loaded at process start. Hot-reload is not
supported — restart the container/process to pick up changes.

---

## 5. Endpoints

| Method | Path                       | Notes                                              |
| ------ | -------------------------- | -------------------------------------------------- |
| GET    | `/`                        | Redirects to `/queue`                              |
| GET    | `/queue`                   | Issues a queue number + JWT cookie                 |
| POST   | `/api/queue/regenerate`    | Re-issues a queue number + JWT cookie              |
| GET    | `/login`                   | Queue-number login form                            |
| POST   | `/login`                   | Submits queue number, redirects to `/dashboard`    |
| GET    | `/dashboard`               | Corporate dashboard (requires valid JWT cookie)    |
| GET    | `/profile`                 | Shows JWT claims; flag if `role=admin`             |
| GET    | `/logout`                  | Clears cookies, redirects to `/queue`              |

Static assets are served from `/static/...`.

---

## 6. Organizer notes

### Replacing the flag

Edit `flag.txt`, then redeploy:

```bash
docker compose up --build -d
```

### Rotating JWT keys

Generate a new RS256 keypair (the queue issue flow expects a 2048-bit RSA
key, PEM format):

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

Replace both files in the project root, then redeploy. Players need the
new `public.pem`.

### Changing the secret

Set `SOAP_SECRET` in the host environment or in `docker-compose.yml`:

```yaml
environment:
  - SOAP_SECRET=<random-32-bytes-hex>
```

### Resetting between runs

The queue is in-memory (random `SOAP-NNNNNN` per request). The
`private.pem`/`public.pem`/`flag.txt` are the only files that persist
state worth preserving. To fully reset, redeploy the image.

### What to ship to players

- `public.pem`
- The running URL
- A walkthrough of the queue + login flow (no solution)

### What to keep server-side

- `private.pem`
- `flag.txt`
- `WRITEUP.md` — full exploitation walkthrough (organizer only — do **not**
  ship to players; delete before each event if needed)
- `INSTRUCTIONS.md` (this file)

---

## 7. Troubleshooting

**Port already in use** — change the host port mapping in
`docker-compose.yml` or set `PORT=<n> python app.py`.

**`Permission denied` on private key** — the file is mode 600 on the
host. Inside the container this is fine; if you copied the file
elsewhere, run `chmod 600 private.pem`.

**Static assets 404** — the `static/` directory must sit next to
`app.py`. Don't move it.

**`Invalid Queue Number` on every login attempt** — cookies are
HttpOnly. Headless players must use a browser session that preserves
cookies between `/queue` and `/login`, or `curl --cookie-jar` /
`--cookie` between the two requests.
