# SkinSync — Build Prompt for Claude Code

> **How to use:** create an empty repo, put the spec file in it as `docs/SPEC.md`, then paste everything below the line into Claude Code (or another coding agent) as your first message. The agent works in phases and stops after each one for you to review.

---

You are building **SkinSync**, a complete, production-quality web application, from an empty repository. The full product specification is in `docs/SPEC.md`. **Read it completely before writing any code.** It is the source of truth. This prompt adds the project decisions the spec left open, hard constraints, the build plan, and the quality bar. If this prompt and the spec conflict, the spec's [SOURCE] sections win, then this prompt, then the spec's [PROPOSED] sections.

## 0. Ground rules for you (the agent)

1. **Do not hallucinate.** Never invent ingredient interactions, evidence, citations, prices, product data, API endpoints of third-party services, or library APIs. If you are unsure how a library or external service works, read its official documentation or the installed package source before using it. Pin dependencies to their **current stable versions** at build time (check them; do not guess version numbers from memory).
2. **Ask before guessing** on anything that changes the architecture or data semantics. For small choices, pick the simplest option consistent with spec §1.2 and record it in `ASSUMPTIONS.md` (decision, reason, how to change it).
3. **Work in phases (section 6).** At the end of each phase: all tests pass, `docker compose up` works, `PROGRESS.md` is updated (done / not done / known issues / next), then **stop and summarize for me** before starting the next phase.
4. **Never leave silent stubs.** Anything incomplete must be listed in `PROGRESS.md` and marked in code with `TODO(skinsync):`. No fake "it works" output.
5. **Every feature ships with tests** traced to the FR/NFR/US/SC IDs in the spec (put the ID in the test name or docstring).
6. Keep commits small and meaningful (Conventional Commits).

## 1. Project decisions (fixed — do not change without asking)

| Area | Decision |
|---|---|
| Deployment | **Docker Compose**, runs fully on one machine with one command, for demo and grading. No paid services, no required API keys. |
| Region | India first: currency **INR**, `en-IN` formatting, data protection designed with India's DPDP Act in mind (consent, purpose limitation, deletion). |
| Auth | Email + password only (no social sign-in in v1). 18+ terms checkbox at signup. |
| Product data | **Open Beauty Facts (OBF)** — see section 2. |
| Skin analysis | **Mock model adapter** behind the real interface — see section 3. |
| OCR / barcode | **Local and free:** Tesseract OCR on the server, in-browser barcode scanning — see section 4. |
| LLMs | **No LLM at runtime.** All explanations come from deterministic templates attached to rules. |
| Prices | OBF has no prices. Price features are built fully, but with no price source configured every price shows **"Price unavailable"**. Never invent prices. |

## 2. Open Beauty Facts data (product and ingredient source)

- OBF is a crowd-sourced, open cosmetics database under the **Open Database License (ODbL)**: attribution and share-alike apply. Read OBF's current terms of use and data-reuse page before implementing, and follow them.
- **Import from the official bulk data export** documented on the OBF data page (verify the current export format and URL there), not by crawling the API. Use the live API only for single-barcode lookups when a scanned product is not in the local DB, with a descriptive `User-Agent` (app name + contact email from env), caching, and backoff. Respect whatever rate limits OBF currently documents.
- Build an idempotent importer (`make import-obf`, runnable as a worker job) that:
  - Streams the export (it is large), filters to skincare-relevant categories (configurable list in a YAML file), and supports a `--limit` and a `--country` filter for fast dev imports.
  - Maps OBF records to `Product` + `ProductVersion` (barcode, name, brand, categories, raw ingredient text, OBF last-modified as `observedAt`, image URL as a remote reference only).
  - Records **provenance on every row**: `source="openbeautyfacts"`, source ID/barcode, import run ID, imported-at, licence.
  - Creates a new `ProductVersion` only when the ingredient text actually changes (hash it), so formulation history is real.
  - Sets `completeness` from what is actually present (missing ingredient list → incomplete, never "empty = safe").
  - Logs counts: read, skipped, inserted, updated, failed.
- Keep OBF-derived data in clearly separated, source-tagged records. Add an **Attribution / Data sources page** and footer credit, and document the ODbL share-alike obligation in `docs/DATA_LICENSING.md`.
- OBF coverage of Indian products may be thin. Also build a **CSV/JSON import format** for team-curated products (document the schema in `docs/DATA_FORMATS.md`) so the team can add products manually; same provenance rules.

### 2.1 Knowledge the app needs that OBF does NOT provide

The following must come from **team-reviewed files**, never from you. Build the loaders, schemas, validation and admin UI for each; ship them **empty or as a template**:

1. **Ingredient master / alias table** (canonical INCI name, aliases, function class). Seed canonical names only from strings actually seen in imported OBF data plus a team-supplied file; leave `functionClass` null where unknown.
2. **Interaction rules + evidence records** (`knowledge/rules.yaml`, `knowledge/evidence.yaml`): define a strict, documented schema (rule code, severity, condition over ingredients or function classes, explanation template, linked evidence IDs, evidence citation, source type, strength from the spec's controlled scale). The loader rejects rules without evidence. Rules import as a **draft KnowledgeVersion**; only an admin can publish.
3. **Concern mapping table** (observation → concern category → recommended ingredient classes).
4. **Price observations** (CSV import format only).

With no published rules, comparisons must correctly return **"Insufficient evidence"** — that is the honest output, and it is a test case.

**For tests only:** use synthetic fixtures with obviously fake ingredient names (e.g. `TEST_ACTIVE_A`, `TEST_EXFOLIANT_B`) and fake citations marked `FIXTURE`. These must never be loadable into the real knowledge store (separate path, separate loader flag, test asserts this).

## 3. Skin analysis (mock adapter, real pipeline)

- Build the **entire real pipeline**: consent → upload → validation → private storage → async job → adapter call → observations → concern mapping → recommendations → result with explainability panel → delete.
- **Real image validation** (FR-07), server-side: magic-byte file-type check (JPEG/PNG/WebP only), max size and max dimensions, full decode with Pillow (reject decompression bombs), blur check (variance of Laplacian), brightness/exposure check, optional face-presence check with an OpenCV cascade bundled in the package. Thresholds in config; each rejection gives a specific, actionable message.
- `SkinModelAdapter` interface: `analyze(image) -> {observations[{characteristic, confidence, severity}], model_version}`. Output is validated with Pydantic before domain logic uses it.
- `MockSkinModelAdapter`: deterministic (seeded from the image hash), returns only the cosmetic characteristics listed in config, `model_version="mock-0.1"`. **Every mock result is visibly labelled "Demo model — not a real analysis"** in the UI, API response, and stored record. Selecting the adapter is an env var, so a real model can be dropped in later.
- Medical boundary text from spec §2.3 shown on every analysis screen. No condition names anywhere in observation vocabulary.

## 4. OCR and barcode

- Barcode: scan in the browser (use the native `BarcodeDetector` where supported with a maintained JS library such as ZXing as fallback — check the current package), plus image upload. Look up locally first, then OBF API, then offer "request product".
- Label OCR: server-side **Tesseract** (installed in the worker image) via an `OCRAdapter` returning text, word positions and confidence. Preprocess (grayscale, deskew, threshold). Low confidence → status `pending_review`, show extracted text for the user to correct, and flag for admin review. Never present low-confidence OCR as certain.
- If the OCR worker is down, search and comparison must keep working (NFR-03) — there is a test that stops the worker and proves it.

## 5. Architecture and stack

Follow spec §4 (modular monolith). Concretely:

- **Frontend:** Next.js (App Router) + React + TypeScript (strict), Tailwind CSS, accessible component primitives (e.g. Radix-based), React Hook Form + Zod, TanStack Query for server state. API types generated from the backend OpenAPI schema (no hand-written duplicates).
- **Backend:** Python FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic migrations, all under `/api/v1`. Domain services as separate packages: product, ingredient, compatibility, skin_analysis, recommendation, alternative, routine, shelf, search, share, admin, auth. Services never import each other's ORM models directly — they talk through service interfaces.
- **Data:** PostgreSQL (with `pg_trgm` for typo-tolerant search and `unaccent`), Redis (cache, rate limits, job queue), MinIO (S3-compatible, private buckets) for images.
- **Workers:** a Redis-backed job queue (choose a maintained Python library and justify in ASSUMPTIONS.md) for OCR, skin analysis, OBF import, cleanup/retention jobs.
- **Dev mail:** Mailpit for signup verification and password reset emails.
- **Reverse proxy:** Caddy or Nginx in front of web + API, serving security headers.
- **Repo layout:** `apps/web`, `apps/api`, `apps/worker` (can share the API package), `knowledge/`, `docs/`, `infra/`, `scripts/`, `Makefile` (`make up`, `make test`, `make seed`, `make import-obf`, `make lint`).
- One `docker-compose.yml` for dev; a `docker-compose.prod.yml` override for a production-like build (no hot reload, no debug, non-root containers).

### Domain rules you must implement exactly

- **Compatibility engine (spec §12.2)** is a pure, deterministic function `evaluate(product_version_a, product_version_b, knowledge_version) -> ComparisonResult`. No I/O inside it, no randomness, no ML. Same inputs → byte-identical output (test with property-based tests). Unresolved ingredients lower confidence and completeness and appear in the result. Overall status uses only the spec's graded labels; the clear case reads exactly "No notable interaction identified in the current knowledge base for the formulations supplied."
- **Confidence and evidence strength are separate fields** everywhere (API, DB, UI).
- Results store the ProductVersion IDs, KnowledgeVersion ID and (for skin) model version used. Saved results show an **"Outdated"** badge when any of these is superseded, with a refresh action.
- **Personalization only re-ranks and filters**; a test proves it never changes a compatibility result.
- **Explainability panel** (spec §9G) is one reusable component (What was used / How confident / Evidence strength / What's missing) used on every result screen.
- Every flow implements the full state matrix in spec §18 (loading, empty, partial, error, success).

## 6. Build phases (stop after each)

0. **Foundation:** repo, Compose stack (web, api, worker, postgres, redis, minio, mailpit, proxy), health checks, CI pipeline, lint/format/type-check, base UI system with the spec's colour and type direction, error envelope, request IDs, structured logging.
1. **Catalogue:** schema + migrations for the full domain model (spec §8 + provenance fields), OBF importer, CSV importer, search (FR-01), product and ingredient pages, browse pages, SEO metadata.
2. **Normalization:** ingredient parsing and normalization (spec §12.1) with confidence and source, unresolved flagging, alias management (FR-03, US-003).
3. **Compatibility (the core — get it right):** knowledge loaders, KnowledgeVersion lifecycle, rule engine, evidence, comparison API + UI with the explainability panel, caching with correct invalidation (FR-02/04/05, SC-01).
4. **Accounts:** signup, email verification, login, logout, refresh, password reset, profile, consent settings, guest-result carry-over on signup, account deletion (FR-20, US-010).
5. **Shelf and routines:** My Shelf, routine builder (AM/PM, keyboard-accessible reordering), routine check with pairwise compatibility and duplicate actives (FR-17/18, SC-04).
6. **Alternatives:** feature extraction, candidate retrieval, hard filters, weighted ranking with visible per-dimension reasons, all five modes, price states (FR-14/15/16, SC-03).
7. **Scan and OCR:** barcode, label OCR, confirm-and-correct, review queue (FR-12/13, US-005).
8. **Skin analysis:** full pipeline with mock adapter, concern mapping, recommendations, retention and delete-now (FR-06–11, SC-02).
9. **Sharing:** revocable share tokens, public read-only views, skin analyses never shareable by default (FR-19).
10. **Admin:** flag queue, OCR/normalization review, rule and evidence authoring, version publish with blocking checks, rollback/retire, audit log (UC11/UC12, SC-05).
11. **Hardening:** full security review (section 7), accessibility audit, performance tests against NFR targets, documentation, final demo seed.

## 7. Security requirements (NFR-02, NFR-08) — all mandatory

**Authentication and sessions**
- Passwords hashed with **Argon2id**; enforce minimum length and check against a common-password list; no maximum below 64 chars.
- Session via short-lived access token + rotating refresh token in **`HttpOnly`, `Secure`, `SameSite=Lax` cookies** (never localStorage). Refresh-token reuse detection revokes the session family.
- **CSRF protection** on all state-changing requests (double-submit token or equivalent).
- Login rate limiting per IP and per account, progressive delays, generic error messages (no account enumeration on login, signup, or reset).
- Email verification and password-reset tokens: random, single-use, stored **hashed**, short expiry.
- Re-authentication required for account deletion and email/password change.

**Authorization**
- Role-based access (registered, admin) enforced on the **server** for every endpoint; object-level ownership checks on every user resource (test that user A cannot read/modify user B's shelf, routines, history, analyses, shares — IDOR tests).
- Admin routes on a separate router with its own dependency; admins created only via a CLI command, never via signup.

**Input, output and API**
- Pydantic validation on every input with explicit length/size limits; reject unknown fields.
- ORM / parameterized queries only; no string-built SQL.
- Output encoding by default (React); no `dangerouslySetInnerHTML` except sanitized admin content (use a sanitizer).
- Strict CORS allowlist from env. Rate limiting (Redis) on all public endpoints, stricter on auth, upload, OCR, and share creation.
- Consistent error envelope that never leaks stack traces, SQL, or internal paths in non-dev environments.
- Security headers at the proxy: strict **Content-Security-Policy** (nonces for Next.js scripts), HSTS (prod), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` (camera only on scan/analyze pages), `frame-ancestors 'none'`.

**Uploads and images**
- Validate by magic bytes, not extension; re-encode images server-side; **strip all EXIF/metadata** (including GPS) before storage.
- Store in private MinIO buckets; access only via **short-lived signed URLs** after an ownership check. Encrypt skin images at rest (server-side encryption or app-level AES-GCM with a key from env).
- Default retention: raw skin images deleted after analysis unless the user explicitly saves them; a scheduled cleanup job enforces this. "Delete now" removes the object and DB references immediately (test it).
- User images are never used for training; no opt-in exists in v1.

**Secrets and infrastructure**
- All secrets via env vars; `.env.example` committed with placeholders, real `.env` git-ignored. App refuses to start in prod mode with default/weak secrets.
- Containers run as non-root, minimal base images, read-only filesystems where practical; Postgres/Redis/MinIO not exposed to the host in the prod override.
- Dependency and code scanning in CI: `pip-audit`, `npm audit` (or equivalent), Bandit, a secret scanner, and container image scanning with a free tool (e.g. Trivy). CI fails on high-severity findings.

**Privacy and logging**
- Logs are structured JSON with request IDs and **no PII, no tokens, no image data**. Emails masked.
- Audit log for admin actions and security events (login, failed login, password change, deletion, share create/revoke).
- Consent records stored with timestamp and policy version. Cookie banner only for non-essential cookies; analytics off until consent.
- Account deletion removes or anonymizes all personal data, analyses, images and share tokens; produce a deletion test that checks every table and the bucket.
- Write `docs/SECURITY.md` (threat model using STRIDE for: auth, uploads, sharing, admin publish, OBF import) and `docs/PRIVACY.md` (what is stored, why, for how long, how to delete).

## 8. Metrics, observability and quality targets

**Operational metrics**
- Prometheus `/metrics` on the API and worker (request count, latency histograms per route, error rate, job queue depth, job duration and failures, cache hit rate). Include Prometheus + Grafana in an optional Compose profile (`--profile observability`) with a provisioned dashboard.
- Health and readiness endpoints that check DB, Redis, MinIO; degraded (not failed) when only OCR/model workers are down.
- Error monitoring: optional Sentry-compatible DSN from env; app runs fine without it.

**Product analytics (privacy-respecting)**
- Self-hosted, cookieless analytics (e.g. Umami) in an optional Compose profile, loaded only after consent. Track funnel events only (search, compare started/completed, analysis started/completed, alternatives viewed, signup after result, save, share) — no personal data, no skin data.

**Performance targets (NFR-01) — verified by automated tests**
- Product search p95 < 1.5 s; cached comparison p95 < 2 s; alternatives p95 < 3 s, on the seeded dataset. Add a load-test script (k6 or Locust) and record results in `docs/PERFORMANCE.md`.
- Frontend: Lighthouse performance ≥ 85 and accessibility ≥ 95 on landing, product, compare and result pages (Lighthouse CI).
- Proper DB indexes (trigram on names, FK indexes, composite indexes for history queries); explain-analyze slow queries.

**Testing (spec §19)**
- Backend: pytest unit + integration (real Postgres/Redis via Compose or testcontainers), property-based tests for the rule engine and normalization (Hypothesis), **100% branch coverage on the compatibility engine**, ≥ 80% overall backend coverage.
- Frontend: component tests (Vitest + Testing Library), **Playwright E2E** for every workflow and every state in spec §18, plus automated accessibility checks (axe) in E2E.
- Resilience tests: stop the worker → search and compare still work; OBF API unreachable → local search still works; MinIO down → clear error, no crash.
- Security tests: IDOR, auth bypass, CSRF, rate limits, upload of malicious files (polyglot, oversized, decompression bomb), share-token revocation, skin-analysis share refusal.
- A traceability table `docs/TRACEABILITY.md`: every FR/NFR/US/SC → implementing module → test(s).

## 9. Accessibility and UX

- WCAG 2.1 AA: semantic HTML, keyboard access for everything (including routine reordering and camera flows, which also offer upload), visible focus, labels, `aria-live` for async job status, contrast-checked palette, status never shown by colour alone.
- Mobile-first for scan and photo capture; responsive for tablet/desktop.
- Follow spec §11 for tone, visual direction and the result-screen template. Dark mode is optional; skip it unless time allows.

## 10. Seed and demo

- `make seed` loads: a small OBF import (`--limit`), the empty knowledge templates, one admin user (credentials from env, printed once), and a demo registered user.
- `make seed-demo` additionally loads the **synthetic fixture** rules into a separate *demo* KnowledgeVersion labelled "DEMO — fictional, not scientific" so the comparison UI can be shown end to end. The UI shows this label on every result produced with it. It can never be the default published version in prod mode.

## 11. Documentation to deliver

`README.md` (one-command setup, prerequisites, troubleshooting), `ASSUMPTIONS.md`, `PROGRESS.md`, `docs/ARCHITECTURE.md` (with diagrams in Mermaid), `docs/API.md` (link to generated OpenAPI), `docs/DATA_FORMATS.md`, `docs/DATA_LICENSING.md`, `docs/SECURITY.md`, `docs/PRIVACY.md`, `docs/PERFORMANCE.md`, `docs/TRACEABILITY.md`, `docs/ADMIN_GUIDE.md` (how to author, review and publish a knowledge version).

## 12. Definition of done (whole project)

- `git clone && cp .env.example .env && make up && make seed` gives a working site at `http://localhost`.
- All spec §19 acceptance criteria pass, CI is green, security scans have no high-severity findings, accessibility and performance targets are met and recorded.
- No invented scientific claims, interactions or prices anywhere in the codebase or seed data outside clearly labelled test/demo fixtures.

**Start now with Phase 0.** First read `docs/SPEC.md` fully, then reply with: (a) a short plan for Phase 0, (b) any questions where the spec and this prompt leave an architectural decision genuinely open. Then build Phase 0 and stop.
