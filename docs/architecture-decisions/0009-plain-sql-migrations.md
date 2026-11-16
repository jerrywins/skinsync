# ADR 0009: Reviewed SQL migrations run by Alembic; SQLAlchemy Core instead of an ORM mirror

**Status:** Accepted. **Date:** 2026-11-04

The schema relies on triggers, partial indexes and CHECK constraints that are clearest in SQL. Migrations
are plain `.sql` files executed by Alembic revisions, and tested directly with SQL assertions.
Repositories use SQLAlchemy Core `text()` with bound parameters rather than mirroring 37 tables as ORM
classes. Every interpolated fragment is a server constant (reviewed list in `security.md`).
