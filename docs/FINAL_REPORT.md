# SkinSync: final engineering report

Date: 2026-11-05. Everything marked **verified** was executed in the build environment (Linux,
PostgreSQL 16, Redis 7, Tesseract 5.3, Node 22 for builds, headless Chromium). Anything not executed is
said to be not executed.

## Summary

The software is complete and tested end to end: a FastAPI backend (57 endpoints), a worker, a Next.js
frontend (37 routes), PostgreSQL schema with database-enforced integrity rules, and a real product
catalogue imported from Open Beauty Facts. **The scientific content is not complete.** Four interaction
rules and five evidence records (real, checked citations) have been **drafted by Claude for human review**;
they stay unpublished and the system blocks publishing them until a reviewer marks them reviewed. No
reviewed concern mappings, ingredient functions or real prices exist. Skin analysis uses an **experimental,
unvalidated** image-measurement adapter. The system says all of this in every result instead of guessing. A
fictional, clearly labelled demo dataset demonstrates the whole experience, and random prices badged
"TEST PRICE — not real" can be loaded in dev/test to try the cheaper/premium flows.

## A. Product delivery

| Workflow | Status |
|---|---|
| Search products (typo tolerant, by brand, category, ingredient) | Verified (API + E2E) |
| Product and ingredient pages with provenance, versions, completeness | Verified |
| Compare two products, or a product and a typed ingredient list | Verified (API + E2E) |
| "Why was this flagged?", evidence, confidence vs evidence, explainability panel | Verified |
| Find alternatives: similar, cheaper, premium, ingredient-focused, routine-compatible | Verified (API + E2E) |
| Analyze skin: consent, upload/camera, validation, async result, delete | Verified with the **demo model** |
| Scan: barcode lookup (typed + camera code), label OCR with confirm/correct | API verified; camera scanning not tested on a real device |
| Accounts: sign-up, email verification, sign-in, reset, profile, privacy, deletion | Verified |
| My Shelf, routines (keyboard reordering), routine analysis, history, outdated flags | Verified |
| Share links (revocable; skin analyses refused) | Verified |
| Admin: data quality, review queue, knowledge import/review/publish/rollback, audit log, failed jobs | Verified |
| SEO: metadata, canonical URLs, sitemap, robots, Product JSON-LD, noindex on thin/private pages | Verified (sitemap/robots in E2E) |

Routes: `/`, `/compare`, `/compare/[id]`, `/analyze`, `/analyze/[id]`, `/alternatives`, `/alternatives/[id]`,
`/products`, `/products/[slug]`, `/products/[slug]/alternatives`, `/ingredients`, `/ingredients/[slug]`,
`/brands/[slug]`, `/scan`, `/shelf`, `/routines`, `/routines/[id]`, `/history`, `/profile`,
`/settings/privacy`, `/share/[token]`, `/auth/{signin,signup,verify,forgot,reset}`, `/admin`,
`/how-it-works`, `/methodology`, `/safety`, `/privacy`, `/terms`, `/about`, `/data-sources`, sitemap, robots.

## B. Backend delivery

* **API:** 57 paths (`docs/api.md`, `apps/api/openapi.json`).
* **Domain services:** ingredients, knowledge, compatibility, alternatives, images, skin, OCR (pure);
  catalog, knowledge, comparisons, recommend (database).
* **Database:** 37 tables, 2 Alembic migrations of reviewed SQL, 13 SQL integrity assertions
  (`docs/er.md`, `docs/data-dictionary.md`).
* **Workers:** RQ worker for skin analysis and OCR, hourly retention cleanup, retries, idempotency keys.

## C. Three-pipeline status

| Pipeline | Input → processing → output | Integration | Tests | Limitations |
|---|---|---|---|---|
| A. Skin | photo + skin type + consent → validation, encryption, worker, model adapter, concern mapping, product retrieval, routine filter → observations, recommendations, limitations | End to end, browser to database | API pipeline test, E2E SC-02 | Heuristic adapter is experimental/unvalidated (mock for demo); concern mappings are demo-only |
| B. Compatibility | two products or typed list → current formulations, normalisation, rules, evidence, confidence → five-category result | End to end; cached; versions stamped; outdated detection | C01–C07, property, determinism, API, E2E SC-01 | No real rules: real products return "insufficient evidence" / "data incomplete" |
| C. Alternatives | product + mode → features, candidates, filters, weighted dimensions, prices → ranked list with reasons | End to end; links to Compare | 16 unit, 5 API, E2E SC-03 | Real products have no real prices; with dev/test random TEST prices the cheaper/premium paths run, labelled |

Cross-pipeline links verified in E2E: compare → alternatives; alternatives → compare; skin → product →
alternatives; shelf → compare; routine → pairwise compatibility.

## D. AI/ML status

| Component | Status |
|---|---|
| Real skin model integration | **None.** No weights supplied |
| Verified inference | Mock adapter (does not look at skin, demo) and **experimental heuristic adapter** `heuristic-0.1` (colour/texture statistics, default; labelled "not validated"; verified only on synthetic images) |
| Datasets | **None** supplied; no evaluation possible (`docs/model-evaluation.md`) |
| OCR | Tesseract, verified on rendered labels; not evaluated on real packaging photos |
| Face-presence check | OpenCV YuNet (MIT), **advisory**: never rejects a photo; not verified on real faces |
| LLMs | Not used anywhere |

## E. Data status

| Data | Status |
|---|---|
| Products | 2,557 real skincare products from Open Beauty Facts (ODbL); 1,711 with ingredient lists; 51 tagged India |
| Ingredients | 700 names observed in OBF data, **unreviewed**, no functions |
| Recognition | average 76% of listed ingredients recognised; 244 formulations fully recognised |
| Interaction rules, evidence | **7 draft rules, 10 evidence records** (3 rules from the team CSV after checking its citations; 25 CSV rows pending a source, `knowledge/review/`) (AI-drafted, real citations, verified at source); version `kv-…-draft`, **publish blocked** until human review (`knowledge/RESEARCH_NOTES.md`) |
| Concern mappings | **0 real records**: awaiting human scientific review |
| Ingredient master entries | 20 AI-drafted entries (re-matched into existing products by `reresolve`) (names/aliases active; function classes inactive until reviewed) |
| Prices | **0 real observations** (no licensed source). Dev DB has 2,557 random **TEST** prices (`seed-test-prices`), badged, hidden in staging/prod, removable |
| Demo data | 13 fictional products, 13 fictional ingredients, 3 rules, 4 evidence records, 10 mappings, fictional prices; isolated and labelled |
| Licensing | ODbL attribution shipped; share-alike obligations documented (`docs/data-governance.md`) |

## F. Testing (actually executed)

| Suite | Result |
|---|---|
| Backend pytest (unit, property, SQL, API integration on real PostgreSQL + Redis) | **142 passed** |
| Coverage | 81% overall; compatibility engine **100% lines and branches** |
| Playwright E2E against the production build | **14 passed** (13 desktop, 1 mobile) |
| Accessibility (axe, WCAG 2.1 A/AA) on 15 pages | No serious or critical violations (two contrast failures found and fixed) |
| Production build | 37 routes, success |
| Ruff, Bandit (medium+, with documented B608 skip), pip-audit, npm audit | All clean (re-run 2026-11-05) |
| Experimental skin adapter | 12 unit tests on synthetic images + 1 API test; UI labels checked by screenshot. **Never run on real face photos** |
| Load test (NFR-01) | search p95 774 ms, cached compare 151 ms, alternatives 978 ms: all pass |
| Docker Compose stack on macOS (Apple Silicon, Docker Desktop) | **Runs** (2026-11-23); first run found and fixed an API startup crash (container path) |
| GitHub Actions CI: lint, Bandit, pip-audit, tests + coverage, web build, E2E, gitleaks, image builds, Trivy | **All 4 jobs green** (2026-11-23). Fixes needed on the way: Trivy action version, data-independent E2E tests, OS updates and removal of pip/npm from runtime images |
| Manual screen-reader test, real phone camera, Lighthouse | **Not executed** |

Bugs found and fixed during verification include: fuzzy matching treating different chemicals as the
same; an ownership bypass through an exposed query parameter; sign-up revealing registered emails; refresh
token revocation being rolled back; a refresh deadlock; two WCAG contrast failures; alternatives too slow
(5.5 s → 0.98 s p95).

## G. Running the application

See `README.md`. Short version with Docker:

```bash
cp .env.example .env && make up && make seed && make import-obf   # then open http://localhost
```

Mac step by step: `docs/MAC_DOCKER_GUIDE.md`.

Without Docker: README "Run without Docker" (venv, `alembic upgrade head`, CLI seed commands,
`uvicorn`, `python -m skinsync.worker`, `npm run dev`).

## H. Deployment

`docs/deployment.md`: Caddy (automatic HTTPS) in front of web and API; PostgreSQL, Redis, worker;
production override with read-only containers and no published database ports; the API refuses to start
with dev secrets, insecure cookies or demo mode. Required settings are in `.env.example`. Backups via
`make backup`; restore and rollback steps documented. **Known blocker:** the container path is
unverified until run on a Docker host.

## I. Remaining limitations

1. **Scientific content:** the 4 drafted rules need a qualified reviewer; no concern mappings or reviewed
   ingredient functions yet. This is the main gap between "software complete" and "product useful".
2. **Skin model:** experimental heuristics (uncalibrated thresholds, crude skin-colour mask that can miss
   some skin tones and very red areas, never tested on real faces) or the demo mock. A real model needs
   weights, a consented dataset and the evaluation in `model-evaluation.md`.
3. **Prices:** no real source; the TEST prices are random and must be removed (`make remove-test-prices`)
   before anyone treats the dev database as real.
4. **Indian coverage:** 51 imported products; the team CSV import exists for curation.
5. **Unverified infrastructure:** S3/MinIO storage backend, real SMTP, a production deployment.
6. **Not tested:** real-device camera capture, manual screen-reader pass, Lighthouse scores.
7. **Security gaps:** no MFA; no email-change flow; Sentry-style error reporting not integrated (Prometheus
   metrics and a Grafana dashboard are provided).
8. **Minor UI:** on the skin result, a long recommendation rationale can push its "Alternatives" button to a
   new line.
