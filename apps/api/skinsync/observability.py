"""Request IDs, structured JSON logs (no PII), Prometheus metrics, security headers."""

from __future__ import annotations

import json
import logging
import re
import secrets
import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS = Counter("skinsync_http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("skinsync_http_request_seconds", "HTTP latency", ["method", "route"],
                    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5, 10))
CACHE = Counter("skinsync_cache_total", "Cache lookups", ["cache", "result"])
JOBS = Counter("skinsync_jobs_total", "Background jobs", ["type", "outcome"])
UPLOAD_FAIL = Counter("skinsync_upload_rejections_total", "Rejected uploads", ["code"])

_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+)")
_RID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def mask(text: str) -> str:
    return _EMAIL.sub(r"\1***@\2", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"), "level": record.levelname,
               "logger": record.name, "msg": mask(record.getMessage())}
        for key in ("request_id", "route", "status", "duration_ms", "method"):
            if hasattr(record, key):
                out[key] = getattr(record, key)
        if record.exc_info:
            out["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(out)


def setup_logging(level: str = "INFO") -> None:
    h = logging.StreamHandler()
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [h]
    root.setLevel(level)


access = logging.getLogger("skinsync.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _RID.match(incoming) else secrets.token_hex(8)
        request.state.request_id = rid
        start = time.perf_counter()
        response: Response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        dur = time.perf_counter() - start
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        LATENCY.labels(request.method, path).observe(dur)
        response.headers["X-Request-ID"] = rid
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Cache-Control", "no-store")
        access.info("request", extra={"request_id": rid, "route": path, "method": request.method,
                                      "status": response.status_code, "duration_ms": round(dur * 1000, 1)})
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
