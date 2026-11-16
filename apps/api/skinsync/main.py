"""SkinSync API application."""

from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import errors
from .config import get_settings
from .observability import RequestContextMiddleware, setup_logging
from .security import check_csrf


def csrf_guard(request: Request) -> None:
    check_csrf(request)


def create_app() -> FastAPI:
    s = get_settings()
    setup_logging()
    app = FastAPI(
        title=f"{s.app_name} API",
        version="0.1.0",
        description="Evidence-aware skincare decision support. Not a medical device; no diagnosis.",
        docs_url="/api/docs" if s.env != "prod" else None,
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    errors.install(app)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID", "X-Poll-Token"],
                       expose_headers=["X-Request-ID"])

    from .api import admin, alternatives, auth, catalog, comparisons, events, health, me, scan, shares, skin

    v1 = APIRouter(prefix="/api/v1", dependencies=[Depends(csrf_guard)])
    for r in (health, auth, me, catalog, comparisons, alternatives, skin, scan, shares, events, admin):
        v1.include_router(r.router)
    app.include_router(v1)
    _publish_domain_schemas(app)
    return app


def _publish_domain_schemas(app: FastAPI) -> None:
    """Add the domain result models to OpenAPI components so the frontend generates its
    types from the backend (no hand-maintained duplicates)."""
    from fastapi.openapi.utils import get_openapi
    from pydantic.json_schema import models_json_schema

    from .domain.alternatives import AlternativesResult
    from .domain.compatibility import ComparisonResult
    from .domain.ingredients import NormalizedIngredient
    from .domain.skin import SkinResult

    def custom():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        _, defs = models_json_schema([(m, "serialization") for m in (ComparisonResult, AlternativesResult,
                                                                     SkinResult, NormalizedIngredient)],
                                     ref_template="#/components/schemas/{model}")
        schema.setdefault("components", {}).setdefault("schemas", {}).update(defs.get("$defs", {}))
        app.openapi_schema = schema
        return schema

    app.openapi = custom


app = create_app()
