"""Label OCR scan (UC05, FR-12/13, US-005). OCR is never ground truth: the user confirms."""

from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db, jobs, storage
from ..domain.images import ImageRejected, validate_and_sanitize
from ..domain.ingredients import normalize_list
from ..errors import AppError, not_found
from ..security import CurrentUser, optional_user, rate_limit, token_hash
from ..services import catalog
from .common import Strict
from .skin import read_limited

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("/label", status_code=202, dependencies=[Depends(rate_limit("ocr", 20, 3600))])
async def scan_label(request: Request, image: UploadFile = File(...), user: CurrentUser | None = Depends(optional_user)):
    data = await read_limited(image)
    try:
        clean = validate_and_sanitize(data, require_face=False, check_quality=False)
    except ImageRejected as r:
        return JSONResponse(status_code=422, content={"code": r.code, "message": r.message,
                                                      "details": {"guidance": r.guidance},
                                                      "request_id": request.state.request_id})
    key = storage.put_encrypted("label", clean.jpeg_bytes)
    poll = secrets.token_urlsafe(24)
    with db.transaction() as conn:
        up = db.scalar(conn, """INSERT INTO uploads (user_id, purpose, object_key, sha256, byte_size, encrypted, delete_after)
                                VALUES (:u, 'label_image', :k, :h, :b, true, :d) RETURNING id""",
                       u=user.id if user else None, k=key, h=clean.sha256, b=len(clean.jpeg_bytes),
                       d=datetime.now(UTC) + timedelta(hours=1))
        oid = str(db.scalar(conn, """INSERT INTO ocr_results (upload_id, user_id, raw_text, mean_confidence, engine, status,
                                       guest_token_hash) VALUES (:u, :usr, '', 0, 'queued', 'pending_review', :g)
                                     RETURNING id""", u=up, usr=user.id if user else None, g=token_hash(poll)))
    try:
        jobs.enqueue(jobs.run_ocr, oid, job_type="ocr", user_id=user.id if user else None, target_id=oid)
    except Exception:
        raise AppError(503, "OCR_UNAVAILABLE",
                       "Label scanning is temporarily unavailable. You can search by name or type the ingredients.") from None
    return {"id": oid, "status": "queued", "poll_token": poll}


def _own(conn, ocr_id: str, request: Request, user: CurrentUser | None) -> dict:
    import uuid

    try:
        uuid.UUID(ocr_id)
    except ValueError as e:
        raise not_found("Scan") from e
    r = db.row(conn, "SELECT * FROM ocr_results WHERE id = :i", i=ocr_id)
    if not r:
        raise not_found("Scan")
    if r["user_id"] is not None and user is not None and str(r["user_id"]) == user.id:
        return r
    poll = request.headers.get("x-poll-token", "")
    if poll and r["guest_token_hash"] and hmac.compare_digest(bytes(r["guest_token_hash"]), token_hash(poll)):
        return r
    raise not_found("Scan")


def _view(conn, r: dict) -> dict:
    status = "processing" if r["engine"] == "queued" else ("failed" if r["engine"] == "failed" else r["status"])
    text = r["corrected_text"] or r["raw_text"]
    items = [i.model_dump(mode="json") for i in normalize_list(text, catalog.load_master(conn))] if text else []
    return {"id": str(r["id"]), "status": status, "raw_text": r["raw_text"], "mean_confidence": float(r["mean_confidence"]),
            "engine": r["engine"], "needs_review": r["status"] == "pending_review",
            "notice": "Text read from a photo can contain mistakes. Check each ingredient before using it.",
            "ingredients": items}


@router.get("/label/{ocr_id}")
def get_scan(ocr_id: str, request: Request, user: CurrentUser | None = Depends(optional_user),
             conn: Connection = Depends(db.get_conn)):
    return _view(conn, _own(conn, ocr_id, request, user))


class ConfirmIn(Strict):
    text: str = Field(min_length=1, max_length=8000)


@router.post("/label/{ocr_id}/confirm")
def confirm(ocr_id: str, body: ConfirmIn, request: Request, user: CurrentUser | None = Depends(optional_user),
            conn: Connection = Depends(db.get_conn)):
    r = _own(conn, ocr_id, request, user)
    db.execute(conn, "UPDATE ocr_results SET corrected_text = :t, status = 'confirmed' WHERE id = :i",
               t=body.text, i=r["id"])
    master = catalog.load_master(conn)
    items = normalize_list(body.text, master)
    ids = {i.canonical_id for i in items if i.resolved}
    candidates = []
    if ids:
        for c in db.rows(conn, """SELECT p.id, p.slug, p.name, b.name AS brand, p.is_demo,
                                    count(*) FILTER (WHERE pi.ingredient_id = ANY(:ids)) AS shared,
                                    count(*) AS total
                                  FROM products p JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                                  JOIN product_ingredients pi ON pi.product_version_id = pv.id
                                  LEFT JOIN brands b ON b.id = p.brand_id
                                  GROUP BY p.id, b.name HAVING count(*) FILTER (WHERE pi.ingredient_id = ANY(:ids)) > 0
                                  ORDER BY count(*) FILTER (WHERE pi.ingredient_id = ANY(:ids))::float
                                           / (count(*) + :n - count(*) FILTER (WHERE pi.ingredient_id = ANY(:ids))) DESC
                                  LIMIT 5""", ids=list(ids), n=len(ids)):
            sim = c["shared"] / (c["total"] + len(ids) - c["shared"])
            candidates.append({"product_id": str(c["id"]), "slug": c["slug"], "name": c["name"], "brand": c["brand"],
                               "is_demo": c["is_demo"], "ingredient_match": round(sim, 3)})
    return {"id": str(r["id"]), "status": "confirmed", "ingredients": [i.model_dump(mode="json") for i in items],
            "resolved": len(ids), "total": len(items),
            "product_candidates": candidates,
            "candidate_notice": "These products have similar ingredient lists. Confirm one only if it is your product."}
