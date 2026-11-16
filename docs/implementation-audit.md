# Implementation audit

Date: 2026-11-03. Auditor: Claude (coding agent).

## 1. Starting point

There was **no existing repository**. The workspace (`/home/claude`) contained only tool caches. Nothing
existed to preserve or refactor: no frontend, backend, database, migrations, auth, models, datasets,
integrations, environment files, tests or deployment config. Everything in this repo was created in this
session.

Source documents (copied into `docs/`):

| File | Role |
|---|---|
| `SPEC.md` (SkinSync spec) | Product name, [SOURCE]/[PROPOSED] split, FR/NFR/UC/US/SC IDs |
| `SPEC_SKINIQ_MASTER.md` (198 sections) | Detailed UX, taxonomy, tests C01–C07, schema list |
| `IMPLEMENTATION_PROMPT.md` | Execution rules, release gates, reporting format |
| `BUILD_PROMPT.md` | Fixed project decisions: Docker Compose, OBF data, mock skin model, local OCR, INR, no runtime LLM |

Conflicts between them are recorded in `docs/architecture-decisions/`.

## 2. Environment found

| Capability | Status | Consequence |
|---|---|---|
| PostgreSQL 16 server + `psql`, `pg_trgm`, `unaccent` | Available (started locally) | Schema verified against real Postgres |
| Redis 7 server | Available | Not yet used (no Python client installed) |
| Tesseract 5.3.4 + `pytesseract` | Available | OCR adapter verified with real OCR |
| Pillow, OpenCV, NumPy, Pydantic 2, PyYAML, pytest, Starlette, uvicorn | Available | Domain core built and tested |
| OpenCV face cascade / any face model | **Missing** | Face-presence check reports `not_performed` (never a silent pass) |
| Docker daemon | **Missing** (client only) | Compose stack can be written but not run here |
| pypi.org / files.pythonhosted.org | **Blocked by egress policy (403)** | Cannot install FastAPI, SQLAlchemy, Alembic, psycopg, redis-py, rq, argon2-cffi, boto3, hypothesis |
| registry.npmjs.org | **Blocked by egress policy (403)** | Cannot install Next.js, React Query, Tailwind, Playwright test deps |
| world/static.openbeautyfacts.org | **Blocked by egress policy (403)** | Cannot import any real product data |

Unblock path: allow those domains under claude.ai Settings → Capabilities, or run the build on a machine
with normal internet access.

## 3. Gap analysis against the spec

Status vocabulary (from the implementation prompt): **Implemented**, **Implemented with a development
adapter**, **Awaiting external credentials**, **Awaiting dataset**, **Awaiting human scientific review**,
**Not implemented**. Per-requirement detail is in `requirements-traceability.md`.

| Area | Status | Notes |
|---|---|---|
| Ingredient parsing + normalization | Implemented (domain) | Not yet persisted through an API |
| Compatibility engine | Implemented (domain) | Pure, deterministic, tested C01–C07 |
| Knowledge loaders + validation | Implemented (domain + DB guards) | Real rule files are empty: **awaiting human scientific review** |
| Alternatives ranking | Implemented (domain) | No real price source: every real price is "unavailable" |
| Image validation + sanitising | Implemented (domain) | Face check not performed (no model) |
| Skin model | Implemented with a development adapter | Mock, labelled demo everywhere; real model **awaiting model weights** |
| Concern mapping | Implemented (domain) | Table empty: **awaiting human scientific review** |
| OCR | Implemented (domain, real Tesseract) | Worker/queue not built |
| Database schema | Implemented (SQL, verified on Postgres 16) | Alembic wrapper pending package access |
| HTTP API, auth, sessions, CSRF, rate limiting | Not implemented | Blocked: FastAPI / psycopg / argon2 / redis-py unavailable |
| Workers / queue | Not implemented | Blocked: rq / redis-py unavailable |
| OBF importer | Not implemented | Blocked: OBF unreachable and its current export format cannot be verified |
| Frontend (all pages) | Not implemented | Blocked: npm registry unavailable |
| Docker Compose, CI, Prometheus | Not implemented | Docker daemon unavailable; to write next |
| E2E, accessibility, performance tests | Not implemented | Need the frontend and API first |

## 4. Architectural problems found

None in existing code (there was none). Design risks identified up front:

1. The empty knowledge base means real comparisons will mostly return "Data incomplete" or "Insufficient
   evidence". That is the honest output, not a bug. The UI must explain it.
2. OBF coverage of Indian products is thin, so a team CSV import path is required.
3. Without a real skin model, the skin pipeline can only be demonstrated with labelled mock output.

---

## Final state (2026-11-05)

The blockers above were resolved on 2026-11-04 when the package registries and Open Beauty Facts were
allowed (ADR 0004 superseded). Everything in section 3 marked "Blocked" or "Not implemented" has since been
built: HTTP API (57 endpoints), auth, workers, OBF importer, the full Next.js frontend, Docker Compose, CI
and observability. Current per-requirement status: `requirements-traceability.md`. Remaining gaps:
`FINAL_REPORT.md` section I.
