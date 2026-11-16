# API

* Base path `/api/v1`. Interactive docs at `/api/docs` (disabled when `SKINSYNC_ENV=prod`); schema at
  `/api/openapi.json` and committed as `apps/api/openapi.json` (57 paths). Frontend types are generated
  from it: `cd apps/web && npm run gen:api`.
* Every response carries `X-Request-ID`. Errors: `{code, message, details, request_id}`.
* Unsafe methods need the CSRF header `X-CSRF-Token` matching the `ss_csrf` cookie (`GET /auth/csrf`).
* Async jobs (skin analysis, OCR) return `202` with an id; guests also get a `poll_token` to send as
  `X-Poll-Token`.

| Family | Endpoints |
|---|---|
| Health | `GET /health`, `GET /ready`, `GET /metrics` |
| Auth | `GET /auth/csrf`, `POST /auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/verify-email`, `/auth/resend-verification`, `/auth/request-password-reset`, `/auth/reset-password` |
| Account | `GET /me`, `DELETE /me`, `PUT /me/profile`, `POST /me/consents`, `POST /me/claim` |
| Catalogue | `GET /products`, `GET /products/{slug or id}`, `GET /products/barcode/{code}`, `GET /brands/{slug}`, `GET /categories`, `GET /ingredients`, `GET /ingredients/{id}`, `POST /ingredients/normalize`, `POST /reports` |
| Compare | `POST /comparisons`, `GET /comparisons/{id}`, `POST /comparisons/{id}/save` |
| Alternatives | `POST /alternatives/search`, `GET /alternatives/{id}`, `POST /alternatives/{id}/save` |
| Skin | `POST /skin-analyses`, `GET /skin-analyses/{id}`, `DELETE /skin-analyses/{id}`, `DELETE /skin-analyses/{id}/image` |
| Scan | `POST /scan/label`, `GET /scan/label/{id}`, `POST /scan/label/{id}/confirm` |
| Shelf, routines, history | `GET/POST /shelf`, `DELETE /shelf/{product}`, `GET/POST /routines`, `GET/PUT/DELETE /routines/{id}`, `POST /routines/{id}/analyze`, `GET /history`, `DELETE /history/{kind}/{id}` |
| Sharing | `POST /shares`, `GET /shares`, `DELETE /shares/{id}`, `GET /public/shares/{token}` |
| Analytics | `POST /events` (allow-listed names, consent required) |
| Admin | `GET /admin/flags`, `PATCH /admin/flags/{id}`, `POST /admin/ingredient-mappings`, `POST /admin/ingredients`, `GET/POST /admin/knowledge-versions`, `GET /admin/knowledge-versions/{id}`, `POST /admin/knowledge-versions/{id}/transition`, `GET /admin/audit`, `GET /admin/jobs`, `GET /admin/data-quality` |

Differences from the spec sketch: skin analysis uses one multipart `POST /skin-analyses` (image + skin type
+ consent) instead of create-then-upload, and recommendations are part of the analysis result rather than
a separate endpoint.
