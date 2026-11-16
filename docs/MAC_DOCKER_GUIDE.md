# Running SkinSync on a Mac with Docker Desktop

> **Honesty note:** the Docker images and Compose stack were written and reviewed, but **have not been
> built or run** by the author: the build environment had no Docker. Everything inside the containers
> (API, worker, database, migrations, tests) *was* run outside Docker. If a step fails, the error message
> and the "If something goes wrong" section below are the place to start.

Works on Apple Silicon (M1–M4) and Intel Macs. Everything used is free: Docker Desktop is free for
personal use, education and small businesses (under 250 employees and under $10M revenue).

## 1. Install Docker Desktop (once)

1. Download **Docker Desktop for Mac** from <https://www.docker.com/products/docker-desktop/>. Pick
   "Apple Silicon" or "Intel chip" to match  → About This Mac.
2. Open the `.dmg`, drag Docker to Applications, start it, and accept the terms.
3. Wait until the whale icon in the menu bar says **Docker Desktop is running**.
4. Recommended: Docker Desktop → Settings → Resources → give it **at least 4 GB memory**. The web build
   needs it.
5. Check in **Terminal** (Applications → Utilities → Terminal):

   ```bash
   docker --version
   docker compose version     # must print v2.x
   ```

`make` is used for short commands. If `make --version` fails, run `xcode-select --install` once, or use
the plain `docker compose …` commands shown under each step.

## 2. Get the project

Unzip `skinsync.zip`, for example into `~/Documents/skinsync`, then:

```bash
cd ~/Documents/skinsync
```

## 3. Create your settings file

```bash
cp .env.example .env
python3 -c "import secrets;print(secrets.token_urlsafe(48))"
python3 -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"
```

Open `.env` in TextEdit (`open -e .env`) and set:

| Setting | Value |
|---|---|
| `POSTGRES_PASSWORD` | any long password |
| `SKINSYNC_SECRET_KEY` | the first random string printed above |
| `SKINSYNC_IMAGE_ENCRYPTION_KEY` | the second string (ends with `=`) |
| `SKINSYNC_ADMIN_PASSWORD` | a passphrase of 12+ characters for the admin account |
| `SKINSYNC_DEMO_MODE` | `true` to load the labelled fictional demo products (recommended for a first look) |
| `SKINSYNC_SKIN_MODEL_ADAPTER` | `heuristic` (experimental, labelled) or `mock` (demo placeholder that shows the full flow with demo products) |

Save the file. Don't share it: it holds your keys.

## 4. Build and start

```bash
make up            # or: docker compose up -d --build
```

The first build downloads base images and Python/Node packages. Expect **10–20 minutes**; later starts take
seconds. Check that everything is up:

```bash
docker compose ps  # postgres, redis, api, worker, web, caddy, mailpit should be "running"/"healthy"
```

## 5. Load starting data

```bash
make seed          # knowledge bootstrap + admin account + demo data (if DEMO_MODE=true)
```

Optional extras:

```bash
make import-obf          # real products from Open Beauty Facts (large download, several minutes; ODbL)
make seed-test-prices    # RANDOM prices so "cheaper/premium" can be tried; every one is badged "TEST PRICE — not real"
make remove-test-prices  # take them out again
```

## 6. Use it

| What | Where |
|---|---|
| Website | <http://localhost> |
| Emails (sign-up verification, password reset) | <http://localhost:8025> (Mailpit; nothing is really sent) |
| Admin | sign in with `SKINSYNC_ADMIN_EMAIL` / `SKINSYNC_ADMIN_PASSWORD`, then open `/admin` |

To create a normal account: Sign up on the site, open Mailpit, click the verification link, then sign in.

The camera on `/analyze` and `/scan` works on `http://localhost` in Safari and Chrome (browsers treat
localhost as secure). From a phone on the same Wi-Fi, the camera needs HTTPS. Use photo upload there
instead.

## 7. Stop, restart, reset

```bash
make down                    # stop (data is kept)
make up                      # start again
make logs                    # follow api/worker/web logs (Ctrl+C to stop following)
docker compose down -v       # stop AND delete all data (database, uploads). Cannot be undone.
```

## 8. Run the tests against your stack (optional)

Browser tests need Node 22 on the Mac (`brew install node@22` or <https://nodejs.org>):

```bash
cd apps/web && npm ci && npx playwright install chromium
E2E_BASE_URL=http://localhost npx playwright test
```

Some E2E tests expect the demo data (`SKINSYNC_DEMO_MODE=true`, `make seed`) and the `mock` adapter.

## If something goes wrong

| Symptom | Fix |
|---|---|
| `port is already allocated` for 80 or 443 | Another web server is running (e.g. `sudo apachectl stop`), or change `ports` of `caddy` in `docker-compose.yml` to `"8080:80"` and open <http://localhost:8080> (then also set `PUBLIC_BASE_URL=http://localhost:8080` in `.env`). |
| `port is already allocated` for 5432 | A local PostgreSQL is running (Postgres.app/Homebrew). Stop it, or delete the `ports:` line under `postgres`. |
| `api` keeps restarting | `docker compose logs api`. "must be set to a strong value" means `.env` still has a `change-me` value. |
| Web build killed / exit 137 | Give Docker more memory (step 1.4). |
| Sign-up email never arrives | It's in Mailpit at <http://localhost:8025>, not your real inbox. |
| Skin analysis shows nothing | The experimental heuristic only reports features above uncalibrated thresholds and, without a detected face, at low confidence. Try `SKINSYNC_SKIN_MODEL_ADAPTER=mock` with demo mode to see the full flow. |
| Anything else | `docker compose logs <service>`; include the output if you ask for help. |
