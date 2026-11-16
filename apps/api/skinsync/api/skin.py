"""Skin analysis (UC01, FR-06..FR-11, SC-02). Private by default; never shareable."""

from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Connection

from .. import db, jobs, storage
from ..config import get_settings
from ..domain.images import MAX_BYTES, ImageRejected, validate_and_sanitize
from ..domain.skin import MEDICAL_BOUNDARY
from ..errors import AppError, not_found
from ..observability import UPLOAD_FAIL
from ..security import CurrentUser, optional_user, rate_limit, token_hash

router = APIRouter(tags=["skin"])


async def read_limited(f: UploadFile, limit: int = MAX_BYTES) -> bytes:
    data = await f.read(limit + 1)
    if len(data) > limit:
        raise AppError(413, "FILE_TOO_LARGE", f"The file is larger than {limit // 1024 // 1024} MB.",
                       {"guidance": "Use a smaller photo."})
    return data


@router.post("/skin-analyses", status_code=202, dependencies=[Depends(rate_limit("skin", 10, 3600))])
async def create(request: Request, image: UploadFile = File(...),
                 skin_type: Literal["dry", "oily", "combination", "normal", "sensitive", "unsure"] = Form("unsure"),
                 consent: bool = Form(...), keep_image: bool = Form(False),
                 user: CurrentUser | None = Depends(optional_user)):
    if not consent:
        raise AppError(422, "CONSENT_REQUIRED", "Please agree to how your photo is handled before uploading.")
    if keep_image and user is None:
        raise AppError(422, "SIGN_IN_TO_KEEP", "Sign in to keep a photo; guest photos are always deleted.")
    data = await read_limited(image)
    try:
        clean = validate_and_sanitize(data)
    except ImageRejected as r:
        UPLOAD_FAIL.labels(r.code).inc()
        return JSONResponse(status_code=422, content={"code": r.code, "message": r.message,
                                                      "details": {"guidance": r.guidance},
                                                      "request_id": request.state.request_id})
    del data
    s = get_settings()
    key = storage.put_encrypted("skin", clean.jpeg_bytes)
    poll = secrets.token_urlsafe(24) if user is None else None
    with db.transaction() as conn:
        consent_id = None
        if user:
            consent_id = db.scalar(conn, """INSERT INTO consents (user_id, purpose, policy_version, granted)
                                            VALUES (:u, 'skin_image_processing', :v, true) RETURNING id""",
                                   u=user.id, v=s.policy_version)
        retention = timedelta(days=30) if keep_image else timedelta(hours=s.skin_image_retention_hours)
        up = db.scalar(conn, """INSERT INTO uploads (user_id, purpose, object_key, sha256, byte_size, encrypted, delete_after)
                                VALUES (:u, 'skin_image', :k, :h, :b, true, :d) RETURNING id""",
                       u=user.id if user else None, k=key, h=clean.sha256, b=len(clean.jpeg_bytes),
                       d=datetime.now(UTC) + retention)
        aid = str(db.scalar(conn, """INSERT INTO skin_analyses (user_id, guest_token_hash, upload_id, skin_type, status,
                                        consent_id, keep_image) VALUES (:u, :g, :up, :st, 'queued', :c, :k) RETURNING id""",
                                u=user.id if user else None, g=token_hash(poll) if poll else None, up=up, st=skin_type,
                                c=consent_id, k=keep_image))
    try:
        job_id = jobs.enqueue(jobs.run_skin_analysis, aid, job_type="skin_analysis",
                              user_id=user.id if user else None, target_id=aid)
    except Exception:
        raise AppError(503, "ANALYSIS_UNAVAILABLE",
                       "Skin analysis is temporarily unavailable. Search and comparison still work.") from None
    return {"id": aid, "job_id": job_id, "status": "queued", "poll_token": poll,
            "quality": {"face_check": clean.quality.face_check}}


def _authorise(conn, analysis_id: str, request: Request, user: CurrentUser | None) -> dict:
    import uuid

    try:
        uuid.UUID(analysis_id)
    except ValueError as e:
        raise not_found("Analysis") from e
    a = db.row(conn, "SELECT * FROM skin_analyses WHERE id = :i", i=analysis_id)
    if not a:
        raise not_found("Analysis")
    if a["user_id"] is not None:
        if user is None or str(a["user_id"]) != user.id:
            raise not_found("Analysis")
        return a
    poll = request.headers.get("x-poll-token", "")
    if not poll or not a["guest_token_hash"] or not hmac.compare_digest(bytes(a["guest_token_hash"]), token_hash(poll)):
        raise not_found("Analysis")
    return a


@router.get("/skin-analyses/{analysis_id}")
def read(analysis_id: str, request: Request, user: CurrentUser | None = Depends(optional_user),
         conn: Connection = Depends(db.get_conn)):
    a = _authorise(conn, analysis_id, request, user)
    job = db.row(conn, "SELECT status, progress, error_code FROM jobs WHERE target_id = :t ORDER BY created_at DESC LIMIT 1",
                 t=a["id"])
    out = {"id": str(a["id"]), "status": a["status"], "skin_type": a["skin_type"],
           "progress": job["progress"] if job else 0, "error_code": a["rejection_code"],
           "image_stored": a["upload_id"] is not None, "keep_image": a["keep_image"],
           "created_at": a["created_at"].isoformat(), "medical_boundary": MEDICAL_BOUNDARY,
           "shareable": False}
    if a["status"] == "completed":
        out.update(result=a["result"], model_version=a["model_version"], is_demo_model=a["is_demo_model"],
                   demo_label=(a["result"] or {}).get("model_label")
                   or ("Demo model — not a real analysis" if a["is_demo_model"] else None))
    if a["status"] == "failed":
        out["message"] = ("Skin analysis is not available right now. Please try again later."
                          if a["rejection_code"] == "ANALYSIS_UNAVAILABLE"
                          else "The analysis could not be completed. Please try again.")
    return out


@router.delete("/skin-analyses/{analysis_id}")
def delete(analysis_id: str, request: Request, user: CurrentUser | None = Depends(optional_user),
           conn: Connection = Depends(db.get_conn)):
    """Removes the analysis, observations, recommendations, original image and its upload row."""
    a = _authorise(conn, analysis_id, request, user)
    if a["upload_id"]:
        up = db.row(conn, "SELECT * FROM uploads WHERE id = :u", u=a["upload_id"])
        if up:
            storage.backend().delete(up["object_key"])
            db.execute(conn, "DELETE FROM uploads WHERE id = :u", u=up["id"])
    db.execute(conn, "DELETE FROM jobs WHERE target_id = :t", t=a["id"])
    db.execute(conn, "DELETE FROM skin_analyses WHERE id = :i", i=a["id"])
    return {"deleted": True}


@router.delete("/skin-analyses/{analysis_id}/image")
def delete_image(analysis_id: str, request: Request, user: CurrentUser | None = Depends(optional_user),
                 conn: Connection = Depends(db.get_conn)):
    a = _authorise(conn, analysis_id, request, user)
    if a["upload_id"]:
        up = db.row(conn, "SELECT * FROM uploads WHERE id = :u", u=a["upload_id"])
        if up:
            storage.backend().delete(up["object_key"])
            db.execute(conn, "DELETE FROM uploads WHERE id = :u", u=up["id"])
    return {"image_deleted": True}
