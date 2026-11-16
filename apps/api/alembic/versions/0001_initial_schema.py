"""Initial schema: executes migrations/0001_initial_schema.sql.

The SQL file is the reviewed source of truth (tested by tests/sql/schema_constraints.sql).
It is executed on the raw psycopg connection so plpgsql bodies and '%' are passed untouched.

Revision ID: 0001
"""
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None

SQL = Path(__file__).resolve().parents[2] / "migrations" / "0001_initial_schema.sql"


def upgrade() -> None:
    op.get_bind().connection.driver_connection.execute(SQL.read_text(encoding="utf-8"))


def downgrade() -> None:
    # Rollback strategy: drop and recreate the public schema (dev/test only).
    # Production rollback = restore the pre-migration backup (docs/deployment.md).
    op.get_bind().connection.driver_connection.execute(
        "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    )
