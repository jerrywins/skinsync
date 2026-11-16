"""skin_analyses.keep_image

Revision ID: 0002
Revises: 0001
"""
from pathlib import Path

from alembic import op

revision = "0002"
down_revision = "0001"
SQL = Path(__file__).resolve().parents[2] / "migrations" / "0002_skin_keep_image.sql"


def upgrade() -> None:
    op.get_bind().connection.driver_connection.execute(SQL.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("ALTER TABLE skin_analyses DROP COLUMN keep_image")
    op.execute("ALTER TABLE ocr_results DROP COLUMN guest_token_hash")
