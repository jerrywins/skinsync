# Security

Status reflects what is **implemented and tested** in this repository (see `test-cases.md`).

## Controls

| Area | Control | Where | Tested by |
|---|---|---|---|
| Passwords | Argon2id (argon2-cffi defaults), min 10 chars, 10k common-password list incl. trailing digits/symbols, not equal to email | `security.py` | `test_signup_requires_age_and_strong_password` |
| Sessions | 15-min signed access cookie + 14-day rotating opaque refresh cookie; HttpOnly, SameSite=Lax, Secure outside dev; refresh secrets stored as SHA-256 | `security.py` | `test_session_cookies_are_httponly` |
| Token theft | Atomic single-use refresh; reuse revokes the whole family (committed in its own transaction) | `rotate_refresh` | `test_refresh_rotation_and_reuse_detection` |
| CSRF | Double-submit token on every unsafe `/api/v1` request | `main.csrf_guard` | `test_csrf_required_on_state_changing_requests` |
| Enumeration | Same sign-up response for new/existing email; same sign-in error for unknown email/wrong password; email verification required | `api/auth.py` | `test_signup_does_not_reveal_existing_accounts`, `test_login_requires_verified_email_and_hides_which_part_failed` |
| Brute force | Per-IP fixed-window limits on every public route family; per-account lock after 8 failures for 15 min | `rate_limit`, `account_*` | `test_login_rate_limited` |
| One-time tokens | Verify/reset tokens random, hashed, single-use, expiring (24 h / 30 min); reset revokes all sessions | `api/auth.py` | `test_password_reset_single_use` |
| Authorisation | Server-side role checks; admin router has its own dependency; admins only via CLI | `require_admin` | `test_admin_routes_require_admin` |
| IDOR | Every user resource query is scoped by `user_id`; other users' objects return 404 | `api/me.py`, `api/*` | `test_idor_other_users_data_is_invisible` |
| Input | Pydantic models reject unknown fields; length and size limits on every field | `api/common.Strict` | `test_validation_rejects_unknown_fields` |
| SQL injection | All values are bound parameters; see the review list below | `db.py` | code review + bandit |
| Uploads | Magic-byte detection, size cap, Pillow decode, decompression-bomb pixel cap, dimension limits, re-encode to JPEG, EXIF/GPS stripped | `domain/images.py` | image tests in `test_skin_and_images.py` incl. polyglot, decompression bomb, GIF/PDF, blur, exposure, EXIF |
| Image storage | AES-256-GCM before storage, random keys, path-traversal guard, 0600 files; skin images deleted after analysis unless kept (≤ 30 days); hourly retention job | `storage.py`, `jobs.py` | `test_registered_user_keeps_image_then_deletes_it`, guest pipeline test |
| Privacy of results | Skin analyses unshareable (API + DB trigger); guests read their own async results only with a hashed poll token | `api/skin.py`, migration | `test_fr19_share_revoke_and_skin_refusal` |
| Headers | Nonce-based CSP (`strict-dynamic`, no inline scripts/styles in prod), `frame-ancestors 'none'`, nosniff, Referrer-Policy, camera allowed only on /scan and /analyze, HSTS over HTTPS (Caddy) | `apps/web/src/proxy.ts`, Caddyfile | E2E `security headers and CSP are set` |
| Errors | Uniform envelope `{code,message,details,request_id}`; no stack traces or SQL in responses | `errors.py` | `test_error_envelope_and_unknown_route` |
| Logging | JSON logs with request ids; emails masked; no tokens, passwords or images logged | `observability.py` | code review |
| Secrets | Env vars only; `.env` git-ignored; API refuses to start in staging/prod with dev secrets, insecure cookies, or demo mode | `config._prod_guard` | manual check (create-user refusal verified) |
| Containers | Non-root users; read-only root FS and tmpfs in prod override; DB/Redis not published in prod | Dockerfiles, compose.prod | not executed here (no Docker daemon) |
| Supply chain | `pip-audit`, `npm audit`, Bandit, Ruff, gitleaks, Trivy in CI | `.github/workflows/ci.yml` | pip-audit, npm audit, Bandit, Ruff run locally: clean. gitleaks/Trivy not run here |

## Reviewed SQL construction (Bandit B608)

Twelve call sites assemble SQL with f-strings. Each interpolates only server-defined text; all user
input is bound. Reviewed 2026-11-05:

* `api/catalog.py` product/barcode/ingredient queries: interpolate `catalog.PRODUCT_COLS` (constant) and a
  WHERE clause built from fixed fragments.
* `api/me.py` shelf and routine queries: `PRODUCT_COLS`. `delete_history`: table name from a dict keyed by a
  `Literal` path parameter.
* `api/shares.py` `_owner_check`: table name from a fixed dict.
* `services/catalog.search`: WHERE/ORDER fragments are fixed strings; `q`, `brand`, `cat`, `ing` are bound.

Re-review whenever a new f-string query is added.

## Threat model (STRIDE)

| Asset / flow | Threat | Mitigation |
|---|---|---|
| Auth | **S**poofing via stolen refresh token | rotation + reuse detection revokes family; HttpOnly cookies |
| Auth | **D**oS / credential stuffing | IP + account rate limits, generic errors |
| Uploads | **T**ampering: polyglot or malicious files | signature check, full decode, re-encode, never served raw |
| Uploads | **I**nformation disclosure: GPS/EXIF, image theft | metadata stripped, encrypted at rest, deleted after use, no public URLs |
| Sharing | **I**nformation disclosure of skin data | skin shares refused by API and DB trigger; revocable hashed tokens |
| Sharing | **E**levation: reading others' results | ownership checks, 404 on others' ids, unguessable ids |
| Admin publish | **T**ampering with scientific knowledge | publish requires review state, evidence on every rule, no fixture evidence; published rows immutable; audit log append-only |
| Admin publish | **R**epudiation | audit log with actor, reason, request id |
| OBF import | **T**ampering: hostile or malformed rows | CSV parsed with size limits, every row in its own transaction, names truncated, never executed; images referenced by URL only |
| OBF import | Wrong data silently accepted | unknown ingredients stay unresolved; fuzzy matches are suggestions only |

## Known gaps

* No MFA. No email change flow (email is fixed; re-auth exists for deletion).
* CSP allows `images.openbeautyfacts.org` for product photos.
* Dockerfiles, Trivy and gitleaks are written but were **not executed** in this environment.
* Face-presence check is not performed (no detector model installed); it reports `not_performed`.
