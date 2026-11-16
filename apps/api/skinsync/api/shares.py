"""Revocable public share links (FR-19, US-009). Skin analyses can never be shared.

The URL token is random; only its SHA-256 is stored. Public views contain no personal data.
"""

from __future__ import annotations

import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db
from ..config import get_settings
from ..errors import AppError, not_found
from ..security import CurrentUser, audit, rate_limit, require_user, token_hash
from ..services import catalog, comparisons
from .common import Strict

router = APIRouter(tags=["shares"])


class ShareIn(Strict):
    target_type: Literal["comparison", "alternative_search", "routine", "product", "skin_analysis"]
    target_id: str = Field(min_length=1, max_length=60)


def _owner_check(conn, t: str, tid: str, uid: str) -> None:
    table = {"comparison": "comparisons", "alternative_search": "alternative_searches", "routine": "routines"}.get(t)
    if t == "product":
        catalog.find_product(conn, tid)
        return
    import uuid

    try:
        uuid.UUID(tid)
    except ValueError as e:
        raise not_found("Item") from e
    if not db.scalar(conn, f"SELECT 1 FROM {table} WHERE id = :i AND user_id = :u", i=tid, u=uid):
        raise not_found("Item")


@router.post("/shares", status_code=201, dependencies=[Depends(rate_limit("share", 30, 3600))])
def create(body: ShareIn, request: Request, user: CurrentUser = Depends(require_user),
           conn: Connection = Depends(db.get_conn)):
    if body.target_type == "skin_analysis":
        raise AppError(403, "SHARE_REFUSED", "Skin analyses are private and cannot be shared.")
    tid = body.target_id
    if body.target_type == "product":
        tid = str(catalog.find_product(conn, tid)["id"])
    _owner_check(conn, body.target_type, tid, user.id)
    tok = secrets.token_urlsafe(18)
    db.execute(conn, "INSERT INTO shares (token_hash, user_id, target_type, target_id) VALUES (:h, :u, :t, :i)",
               h=token_hash(tok), u=user.id, t=body.target_type, i=tid)
    audit(conn, user.id, "share.created", f"{body.target_type}:{tid}", request_id=request.state.request_id)
    return {"token": tok, "url": f"{get_settings().public_base_url}/share/{tok}"}


@router.get("/shares")
def mine(user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    rows = db.rows(conn, """SELECT encode(token_hash, 'hex') AS share_id, target_type, target_id, created_at, revoked_at
                            FROM shares WHERE user_id = :u ORDER BY created_at DESC""", u=user.id)
    return {"items": [{**r, "target_id": str(r["target_id"]), "created_at": r["created_at"].isoformat(),
                       "revoked_at": r["revoked_at"].isoformat() if r["revoked_at"] else None} for r in rows]}


@router.delete("/shares/{share_id}")
def revoke(share_id: str, request: Request, user: CurrentUser = Depends(require_user),
           conn: Connection = Depends(db.get_conn)):
    try:
        h = bytes.fromhex(share_id)
    except ValueError as e:
        raise not_found("Share") from e
    if not db.execute(conn, "UPDATE shares SET revoked_at = now() WHERE token_hash = :h AND user_id = :u AND revoked_at IS NULL",
                      h=h, u=user.id):
        raise not_found("Share")
    audit(conn, user.id, "share.revoked", share_id[:16], request_id=request.state.request_id)
    return {"revoked": True}


@router.get("/public/shares/{token}")
def view(token: str, conn: Connection = Depends(db.get_conn)):
    s = db.row(conn, "SELECT * FROM shares WHERE token_hash = :h", h=token_hash(token[:64]))
    if not s or s["revoked_at"] is not None:
        raise AppError(404, "SHARE_UNAVAILABLE", "This link has been removed or does not exist.")
    t, tid = s["target_type"], str(s["target_id"])
    if t == "skin_analysis":  # unreachable: blocked by API and a DB trigger; defence in depth
        raise AppError(404, "SHARE_UNAVAILABLE", "This link has been removed or does not exist.")
    if t == "comparison":
        data = comparisons.get(conn, tid, None, via_share=True)
        data.pop("claim_token", None)
        data["saved"] = None
    elif t == "alternative_search":
        from .alternatives import load_search

        data = load_search(conn, tid, None, via_share=True)
    elif t == "routine":
        from .me import _routine_view

        r = db.row(conn, "SELECT * FROM routines WHERE id = :i", i=tid)
        if not r:
            raise AppError(404, "SHARE_UNAVAILABLE", "This link has been removed or does not exist.")
        data = _routine_view(conn, r)
    else:
        p = catalog.find_product(conn, tid)
        data = {"id": str(p["id"]), "slug": p["slug"], "name": p["name"], "brand": p["brand"]}
    return {"type": t, "created_at": s["created_at"].isoformat(), "data": data, "read_only": True}
