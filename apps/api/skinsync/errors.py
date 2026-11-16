"""Consistent error envelope: {code, message, details, request_id}. No stack traces leak."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("skinsync.errors")


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details or {}


def not_found(what: str = "Resource") -> AppError:
    return AppError(404, "NOT_FOUND", f"{what} not found.")


def forbidden() -> AppError:
    return AppError(403, "FORBIDDEN", "You do not have access to this resource.")


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def envelope(request: Request, status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message, "details": details or {}, "request_id": _rid(request)},
        headers={"X-Request-ID": _rid(request)},
    )


def install(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app(request: Request, exc: AppError):
        return envelope(request, exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errs = [{"loc": [str(x) for x in e.get("loc", [])], "msg": e.get("msg"), "type": e.get("type")}
                for e in exc.errors()]
        return envelope(request, 422, "VALIDATION_ERROR", "The request was not valid.", {"errors": errs})

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 401: "UNAUTHENTICATED", 403: "FORBIDDEN"}.get(
            exc.status_code, "HTTP_ERROR")
        msg = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return envelope(request, exc.status_code, code, msg)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled error", extra={"request_id": _rid(request)})
        return envelope(request, 500, "INTERNAL_ERROR", "Something went wrong on our side. Please try again.")
