"""Liveness, readiness (DB, Redis, storage) and Prometheus metrics."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import db, storage
from ..observability import metrics_response
from ..security import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    checks = {}
    try:
        with db.transaction() as conn:
            db.scalar(conn, "SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    try:
        get_redis().ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "down"
    try:
        storage.backend()
        checks["storage"] = "ok"
    except Exception:
        checks["storage"] = "down"
    try:
        from rq import Worker

        checks["workers"] = "ok" if Worker.count(connection=get_redis()) > 0 else "none_running"
    except Exception:
        checks["workers"] = "unknown"
    # Workers being down degrades OCR/skin analysis only; search and comparison still work (NFR-03).
    if checks["database"] != "ok":
        status, code = "down", 503
    elif any(v != "ok" for v in checks.values()):
        status, code = "degraded", 200
    else:
        status, code = "ok", 200
    return JSONResponse({"status": status, "checks": checks}, status_code=code)


@router.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()
