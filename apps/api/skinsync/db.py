"""Database access. All SQL is parameterised through SQLAlchemy `text()` bindings.

The schema lives in plain SQL (migrations/), so repositories use SQLAlchemy Core with
bound parameters rather than an ORM mirror of 37 tables. String-built SQL is forbidden.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)
    return _engine


def reset_engine(url: str | None = None) -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = create_engine(url, pool_pre_ping=True) if url else None


@contextmanager
def transaction() -> Iterator[Connection]:
    with get_engine().begin() as conn:
        yield conn


def get_conn() -> Iterator[Connection]:
    """FastAPI dependency: one transaction per request, committed on success."""
    with get_engine().begin() as conn:
        yield conn


def rows(conn: Connection, sql: str, **params: Any) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(text(sql), params)]


def row(conn: Connection, sql: str, **params: Any) -> dict | None:
    r = conn.execute(text(sql), params).first()
    return dict(r._mapping) if r else None


def scalar(conn: Connection, sql: str, **params: Any) -> Any:
    return conn.execute(text(sql), params).scalar()


def execute(conn: Connection, sql: str, **params: Any) -> int:
    return conn.execute(text(sql), params).rowcount
