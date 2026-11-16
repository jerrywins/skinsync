"""Background jobs (RQ on Redis): skin analysis, label OCR, retention cleanup.

POST -> 202 + job/resource id -> queue -> worker -> status in DB -> client polls.
In tests (SKINSYNC_QUEUE_SYNC=1) jobs run inline so the real code path is exercised.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

from . import db, storage
from .config import get_settings
from .domain.ingredients import normalize_list
from .domain.ocr import TesseractOCRAdapter
from .domain.skin import ModelOutput, SkinType, get_adapter, map_concerns
from .observability import JOBS

log = logging.getLogger("skinsync.jobs")
JOB_TIMEOUT_S = 120
MAX_RETRIES = 2


def enqueue(fn, *args, job_type: str, user_id: str | None, target_id: str) -> str:
    with db.transaction() as conn:
        job_id = str(db.scalar(conn, """INSERT INTO jobs (type, user_id, target_id, idempotency_key)
                                        VALUES (:t, :u, :g, :k) ON CONFLICT (idempotency_key) DO UPDATE
                                        SET idempotency_key = EXCLUDED.idempotency_key RETURNING id""",
                                   t=job_type, u=user_id, g=target_id, k=f"{job_type}:{target_id}"))
    if os.environ.get("SKINSYNC_QUEUE_SYNC") == "1":
        fn(*args, job_id)
        return job_id
    from rq import Queue, Retry

    from .security import get_redis

    try:
        Queue("skinsync", connection=get_redis()).enqueue(fn, *args, job_id, job_id=job_id, job_timeout=JOB_TIMEOUT_S,
                                                          retry=Retry(max=MAX_RETRIES, interval=[5, 30]))
    except Exception:
        with db.transaction() as conn:
            db.execute(conn, "UPDATE jobs SET status='failed', error_code='QUEUE_UNAVAILABLE' WHERE id=:j", j=job_id)
        raise
    return job_id


def _job(conn, job_id, status, progress=None, error=None):
    db.execute(conn, """UPDATE jobs SET status = CAST(:s AS job_status), progress = coalesce(:p, progress),
                          error_code = :e,
                          started_at = CASE WHEN :s = 'processing' THEN coalesce(started_at, now()) ELSE started_at END,
                          completed_at = CASE WHEN :s IN ('completed','failed','cancelled') THEN now() END,
                          retry_count = CASE WHEN :s = 'processing' AND started_at IS NOT NULL
                                             THEN least(retry_count + 1, 5) ELSE retry_count END
                        WHERE id = :j""", s=status, p=progress, e=error, j=job_id)


# ---------------------------------------------------------------- skin analysis
def run_skin_analysis(analysis_id: str, job_id: str) -> None:
    with db.transaction() as conn:
        a = db.row(conn, "SELECT * FROM skin_analyses WHERE id = :i FOR UPDATE", i=analysis_id)
        if not a or a["status"] in ("completed", "rejected"):
            _job(conn, job_id, "cancelled" if not a else "completed")
            return  # deleted meanwhile, or already done (idempotent)
        db.execute(conn, "UPDATE skin_analyses SET status='analyzing' WHERE id=:i", i=analysis_id)
        _job(conn, job_id, "processing", 10)
        up = db.row(conn, "SELECT * FROM uploads WHERE id = :u", u=a["upload_id"]) if a["upload_id"] else None
    try:
        if not up:
            raise RuntimeError("IMAGE_MISSING")
        image = storage.get_decrypted(up["object_key"])
        out: ModelOutput = get_adapter(get_settings().skin_model_adapter).analyze(image)
        ModelOutput.model_validate(out.model_dump())  # validate adapter output before domain use
        del image
        with db.transaction() as conn:
            from .services import knowledge, recommend

            kv_id = knowledge.active_version_id(conn, demo=out.is_demo) or knowledge.active_version_id(conn, demo=False)
            kv, cmap = knowledge.load(conn, kv_id)
            result = map_concerns(out, SkinType(a["skin_type"]), cmap, kv.evidence)
            products = recommend.products_for(conn, result, a["user_id"], demo=out.is_demo)
            payload = result.model_dump(mode="json")
            payload["products"] = products
            payload["knowledge_version"] = kv_id
            payload["knowledge_is_demo"] = kv.is_demo
            payload["model_label"] = out.label
            for o in out.observations:
                db.execute(conn, """INSERT INTO skin_observations (analysis_id, characteristic, confidence, severity)
                                    VALUES (:a, :c, :cf, :s) ON CONFLICT DO NOTHING""",
                           a=analysis_id, c=o.characteristic, cf=o.confidence, s=o.severity.value)
            for rank, p in enumerate(products, start=1):
                db.execute(conn, """INSERT INTO recommendations (analysis_id, rank, observation, concern_category,
                                      product_id, observation_confidence, evidence_strength, rationale)
                                    VALUES (:a, :r, :o, :c, :p, :oc, CAST(:es AS evidence_strength), :ra)""",
                           a=analysis_id, r=rank, o=p["observation"], c=p["concern_category"], p=p["product_id"],
                           oc=p["observation_confidence"], es=p["evidence_strength"], ra=p["rationale"])
            db.execute(conn, """UPDATE skin_analyses SET status='completed', model_version=:m, is_demo_model=:d,
                                  knowledge_version=:k, result=CAST(:r AS jsonb), completed_at=now() WHERE id=:i""",
                       m=out.model_version, d=out.is_demo, k=kv_id, r=json.dumps(payload), i=analysis_id)
            if up and not a["keep_image"]:
                _delete_upload(conn, up)  # default: raw image deleted as soon as analysis finishes
            _job(conn, job_id, "completed", 100)
        JOBS.labels("skin_analysis", "completed").inc()
    except Exception as exc:
        code = str(exc) if str(exc) in ("ANALYSIS_UNAVAILABLE", "IMAGE_MISSING") else "MODEL_FAILURE"
        with db.transaction() as conn:
            db.execute(conn, "UPDATE skin_analyses SET status='failed', rejection_code=:c WHERE id=:i", c=code,
                       i=analysis_id)
            _job(conn, job_id, "failed", error=code)
        JOBS.labels("skin_analysis", "failed").inc()
        log.warning("skin analysis failed", extra={"status": code})


def _delete_upload(conn, up: dict) -> None:
    storage.backend().delete(up["object_key"])
    db.execute(conn, "DELETE FROM uploads WHERE id = :u", u=up["id"])


# ---------------------------------------------------------------- OCR
def run_ocr(ocr_id: str, job_id: str) -> None:
    with db.transaction() as conn:
        r = db.row(conn, "SELECT * FROM ocr_results WHERE id = :i", i=ocr_id)
        if not r or r["status"] != "pending_review" or r["engine"] != "queued":
            _job(conn, job_id, "completed" if r else "cancelled")
            return
        _job(conn, job_id, "processing", 10)
        up = db.row(conn, "SELECT * FROM uploads WHERE id = :u", u=r["upload_id"])
    try:
        res = TesseractOCRAdapter().extract(storage.get_decrypted(up["object_key"]))
        with db.transaction() as conn:
            db.execute(conn, """UPDATE ocr_results SET raw_text=:t, mean_confidence=:c, engine=:e, status=:s WHERE id=:i""",
                       t=res.raw_text, c=res.mean_confidence, e=res.engine, s=res.status, i=ocr_id)
            if res.status == "pending_review":
                from .services.catalog import raise_flag

                raise_flag(conn, "ocr_result", str(ocr_id), "low_ocr_confidence", "ocr",
                           {"mean_confidence": res.mean_confidence})
            _delete_upload(conn, up)  # label photos are not kept after extraction
            _job(conn, job_id, "completed", 100)
        JOBS.labels("ocr", "completed").inc()
    except Exception:
        with db.transaction() as conn:
            db.execute(conn, "UPDATE ocr_results SET engine='failed', status='rejected' WHERE id=:i", i=ocr_id)
            _job(conn, job_id, "failed", error="OCR_FAILURE")
        JOBS.labels("ocr", "failed").inc()


# ---------------------------------------------------------------- retention
def retention_cleanup(job_id: str | None = None) -> int:
    n = 0
    with db.transaction() as conn:
        for up in db.rows(conn, "SELECT * FROM uploads WHERE delete_after < now()"):
            _delete_upload(conn, up)
            n += 1
        db.execute(conn, "DELETE FROM skin_analyses WHERE user_id IS NULL AND created_at < now() - interval '7 days'")
        db.execute(conn, "DELETE FROM comparisons WHERE user_id IS NULL AND NOT saved AND created_at < now() - interval '30 days'"
                   " AND id NOT IN (SELECT target_id FROM shares)")
        db.execute(conn, "DELETE FROM refresh_tokens WHERE expires_at < now() - interval '1 day'")
        db.execute(conn, "DELETE FROM auth_tokens WHERE expires_at < now() - interval '1 day'")
    log.info("retention cleanup", extra={"status": n})
    return n


def normalized_from_text(conn, text: str):
    from .services.catalog import load_master

    return normalize_list(text, load_master(conn))


def now() -> datetime:
    return datetime.now(UTC)
