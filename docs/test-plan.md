# Test plan

## Levels

| Level | Tool | What | How to run |
|---|---|---|---|
| Unit | pytest | Normalisation, rule engine (C01–C07), alternatives ranking, image validation, concern mapping, OCR adapter | `cd apps/api && python -m pytest -q tests/test_*.py` |
| Property | pytest + seeded random | Engine never returns "no notable interaction" when anything is unresolved; symmetry; bounds; determinism | `tests/test_compatibility.py` |
| Database | psql + SQL assertions | Integrity triggers and constraints (13 checks) | `tests/test_schema_sql.py` |
| Integration | FastAPI TestClient against real PostgreSQL + Redis, jobs inline | Every workflow, auth, CSRF, IDOR, rate limits, deletion, resilience | `tests/api/` (needs `PGHOST`/`PGUSER`, Redis on 6379) |
| End-to-end | Playwright 1.63 + axe-core | Guest and signed-in journeys, admin, headers/CSP, WCAG 2.1 AA checks, mobile journey | `cd apps/web && npx playwright test` against a running stack |
| Performance | `scripts/loadtest.py` | NFR-01 p95 targets | see `PERFORMANCE.md` |
| Security | Bandit, Ruff (S rules), pip-audit, npm audit; gitleaks + Trivy in CI | Static and dependency checks | `make lint`; CI |

## Gates (CI, `.github/workflows/ci.yml`)

Lint → Bandit → pip-audit → backend tests with ≥ 80% coverage → **100% branch coverage of the
compatibility engine** → OpenAPI schema up to date → web type-check, npm audit, build → E2E → secret scan
→ image build and Trivy scan. Any failure blocks the merge.

## Results on 2026-11-05 (this environment)

| Check | Result |
|---|---|
| Backend tests | **119 passed** |
| Backend coverage | **81%** overall; compatibility engine **100% lines and branches** |
| E2E | **14 passed** (13 desktop + 1 mobile), axe: no serious or critical violations on 15 pages |
| Ruff | clean |
| Bandit (medium+) | clean (B608 reviewed and documented in `security.md`) |
| pip-audit | no known vulnerabilities |
| npm audit | 0 vulnerabilities |
| Load test | all three NFR-01 targets met (`PERFORMANCE.md`) |
| Docker build, gitleaks, Trivy | **not run**: no Docker daemon in this environment |
| Real-device camera capture | **not tested**: headless browser only |

## Not covered

* Skin model accuracy: no model or dataset (see `model-evaluation.md`).
* OCR on real packaging photos: no labelled photo set.
* S3/MinIO storage backend: written, not exercised (local encrypted storage is tested).
* Email delivery through a real SMTP server (Mailpit configuration provided; tests use an in-memory outbox).
