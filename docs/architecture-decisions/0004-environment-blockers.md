# ADR 0004: Build order under blocked package registries

**Status:** Superseded on 2026-11-04 (package registries and Open Beauty Facts were allowed; the full stack was built). **Date:** 2026-11-03

**Context.** This session cannot reach pypi.org, the npm registry or Open Beauty Facts (egress policy 403),
and has no Docker daemon. FastAPI, SQLAlchemy, psycopg, redis-py, argon2 and Next.js are not installed.

**Decision.** Build first what can be verified here:
- the domain core as a dependency-light package (Pydantic, PyYAML, Pillow, OpenCV, pytesseract);
- the schema as plain SQL, applied and tested on the local PostgreSQL 16 via `psql`.

Do **not** write the API, worker or frontend blind: code that cannot be run here would be reported as
untested, and the spec forbids claiming it works.

**Consequence.** The domain package has no framework imports, so FastAPI routes can wrap it unchanged. The
SQL migration becomes Alembic revision 0001 (`op.execute`) once Alembic can be installed.
