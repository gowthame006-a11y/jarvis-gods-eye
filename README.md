# Jarvis + God’s Eye

Offline command assistant, persistent personal tasks, task completion, synthetic vehicle simulation, coordinate visualization and activity history.

## Run
Requires Python 3.10+; no third-party dependencies.

```bash
git clone https://github.com/gowthame006-a11y/jarvis-gods-eye.git
cd jarvis-gods-eye
python server.py
```

Open http://127.0.0.1:8000. On first run, the terminal prints a generated password for the `employee` and `manager` demo accounts. The database preserves records across restarts; sessions expire after eight hours and reset on restart. To use a chosen password on initial setup, set `DEMO_PASSWORD` before the first run. Changing that variable does not reset an existing database. `PORT` and `APP_DB` are optional environment variables.

## Verify
```bash
python -m unittest discover -s tests -v
```

## Architecture
`server.py`: HTTP JSON API, PBKDF2 password hashes and bearer sessions. `domain.py`: project rules and SQLite schema. `static/index.html`: responsive dashboard and API client. SQLite writes commit after each successful operation. No credentials or private data are committed.

## Scope and limitations
Runnable local portfolio application, not a production deployment. Server binds to localhost. Before public hosting, add HTTPS, rate limits, persistent session storage, user provisioning, backups and an approved deployment configuration. No external AI, GPS, camera or social-media APIs are connected. Demo role accounts are created once. BrandLens uses an explainable English sentiment baseline; Jarvis uses deterministic commands and synthetic shared vehicle data. Leave policies count calendar days, use annual allowances and reject cross-year requests.

## API
POST `/api/login` accepts username/password and returns a token. Pass `Authorization: Bearer <token>` for GET `/api/dashboard` and project POST operations documented in `domain.py`. POST `/api/logout` revokes the session. API failures return JSON errors.

## Demo walkthrough
Sign in, add a record through the main form, refresh to confirm persistence, and sign out. For leave approval, create a request as employee, then sign in as manager and approve it. For BrandLens, use Load sample then Analyze and save. For Jarvis, send `add task Prepare demo`, then advance the simulation.

## Docker
`docker build -t jarvis-gods-eye .` then `docker run --rm -p 127.0.0.1:8000:8000 -v jarvis-gods-eye-data:/data -e APP_DB=/data/app.sqlite3 jarvis-gods-eye`. Read first-run credentials from container logs.
