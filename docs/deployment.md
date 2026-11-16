# Deployment

> The Compose files were validated with `docker compose config`; the images were **not built or run** in
> the environment used to write this (no Docker daemon). Do a full `make up` dry run before relying on it.

## Environments

| Env | How | Notes |
|---|---|---|
| Development | `cp .env.example .env && make up && make seed` | Mailpit at http://localhost:8025, demo data on |
| Staging | same as prod with its own `.env` | Run CI E2E against it |
| Production | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` | `SKINSYNC_ENV=prod`; API refuses dev secrets, insecure cookies, demo mode |

## First run

```bash
cp .env.example .env            # then set POSTGRES_PASSWORD, SKINSYNC_SECRET_KEY, SKINSYNC_IMAGE_ENCRYPTION_KEY, admin password
make up                         # builds api, worker, web; starts postgres, redis, caddy, mailpit
make seed                       # bootstrap knowledge version, admin user, demo data (if enabled)
make import-obf                 # download the Open Beauty Facts export and import skincare products
open http://localhost
```

The API container runs `alembic upgrade head` and the knowledge bootstrap on start.

## Production checklist

1. Domain in `SITE_ADDRESS` (Caddy obtains TLS automatically), `PUBLIC_BASE_URL=https://…`, `SKINSYNC_COOKIE_SECURE=true`.
2. Strong secrets: generate per `.env.example`. Store them in the host's secret store, not in git.
3. Real SMTP (`SKINSYNC_SMTP_HOST`/`PORT`) for verification and reset email.
4. `SKINSYNC_DEMO_MODE=false`. Publish a reviewed knowledge version before advertising comparisons.
5. Backups: `make backup` nightly (pg_dump custom format) plus a copy of the `storage` volume.
6. Monitoring: `make observability` (Prometheus + Grafana with the provisioned SkinSync dashboard), or point
   your own Prometheus at `api:8000/api/v1/metrics` (not exposed through Caddy).

## Recovery

* **Database**: `docker compose exec -T postgres pg_restore -U skinsync -d skinsync --clean < backups/<file>.dump`
* **Bad migration**: restore the pre-migration dump (Alembic `downgrade` drops the schema and is for dev only).
* **Bad knowledge version**: in Admin → Knowledge versions, roll back to the previous version (re-publishes it).
* **Leaked secret key**: rotate `SKINSYNC_SECRET_KEY` (signs everyone out); rotating the image key makes
  stored images unreadable, so delete them first (they are short-lived by design).

## Free hosting alternative

Without a server: Vercel (web), Render or Railway (API + worker), Neon or Supabase Postgres, Upstash Redis.
Set `API_INTERNAL_URL` on the web service and `SKINSYNC_CORS_ORIGINS` on the API. Not tested here.
