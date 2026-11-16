# SkinSync

**Check before you layer.** An evidence-aware skincare decision tool: compare two products, find
alternatives, and see visible cosmetic features in a photo. Every result shows what it used, how confident
it is, how strong the evidence is, and what's missing. It never diagnoses and never calls anything "safe for
everyone".

> **Honest status:** the software is built and tested end to end. The scientific content is not: no
> reviewed interaction rules, evidence, concern mappings or real prices exist yet, and the skin model is a
> labelled placeholder. Real comparisons therefore answer "insufficient evidence" or "data incomplete",
> which is correct. A fictional, clearly labelled demo dataset shows the full experience. See
> `docs/FINAL_REPORT.md`.

## Run it (Docker)

On a Mac, follow the step-by-step guide in [`docs/MAC_DOCKER_GUIDE.md`](docs/MAC_DOCKER_GUIDE.md).

```bash
cp .env.example .env      # set the passwords and keys (instructions inside)
make up                   # postgres, redis, api, worker, web, caddy, mailpit
make seed                 # knowledge bootstrap, admin user, demo data (SKINSYNC_DEMO_MODE=true)
make import-obf           # optional: ~2,500 real skincare products from Open Beauty Facts (ODbL)
```
Open http://localhost. Sign-up confirmation emails appear in Mailpit at http://localhost:8025.

## Run without Docker (development)

Requires Python 3.12+, Node 24, PostgreSQL 16 (with `pg_trgm`, `unaccent`), Redis 7, Tesseract 5.

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r apps/api/requirements-dev.txt
cd apps/api
export SKINSYNC_DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/skinsync SKINSYNC_DEMO_MODE=true \
       SKINSYNC_KNOWLEDGE_DIR=$PWD/../../knowledge SKINSYNC_QUEUE_SYNC=1
alembic upgrade head
python -m skinsync.cli bootstrap && python -m skinsync.cli seed-demo
SKINSYNC_ADMIN_PASSWORD='choose-a-strong-one' python -m skinsync.cli create-admin admin@example.com
python -m skinsync.ingest.obf --file /path/to/en.openbeautyfacts.org.products.csv.gz   # optional
uvicorn skinsync.main:app --port 8000          # API docs: http://localhost:8000/api/docs
python -m skinsync.worker                       # only if SKINSYNC_QUEUE_SYNC is not set

cd ../web && npm ci && API_INTERNAL_URL=http://127.0.0.1:8000 npm run dev   # http://localhost:3000
```

## Tests

```bash
cd apps/api && python -m pytest -q                     # 119 tests; needs PostgreSQL + Redis on localhost
cd apps/web && npx playwright test                      # 14 E2E tests against a running stack
python scripts/loadtest.py --base http://127.0.0.1:8001 # latency targets (rate limiting off)
make lint                                               # ruff, bandit, tsc
```

## Repository

| Path | What |
|---|---|
| `apps/api` | FastAPI API, worker, domain logic, migrations, importer, tests |
| `apps/web` | Next.js 16 frontend, Playwright E2E |
| `knowledge/` | Reviewed rules, evidence, ingredients, concern map (empty); `demo/` is fictional |
| `infra/` | Caddy, Prometheus, Grafana |
| `docs/` | Specs, final report, architecture, UML, security, privacy, data governance, tests, ADRs |

Product data from [Open Beauty Facts](https://world.openbeautyfacts.org), available under the Open Database License.
