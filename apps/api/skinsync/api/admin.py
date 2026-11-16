"""Admin and knowledge governance (UC11, UC12, SC-05). Admin role enforced server-side on
every route via the router dependency. Every change is written to the append-only audit log."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db
from ..config import get_settings
from ..domain.ingredients import normalize_key
from ..errors import AppError, not_found
from ..security import CurrentUser, audit, require_admin
from ..services import catalog, knowledge
from .common import Strict, page

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/flags")
def flags(status: Literal["open", "resolved", "dismissed"] = "open", reason: str | None = Query(None, max_length=40),
          limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), conn: Connection = Depends(db.get_conn)):
    total = db.scalar(conn, """SELECT count(*) FROM data_quality_flags WHERE status = CAST(:s AS flag_status)
                               AND (CAST(:r AS text) IS NULL OR reason = :r)""", s=status, r=reason)
    rows = db.rows(conn, """SELECT * FROM data_quality_flags WHERE status = CAST(:s AS flag_status)
                            AND (CAST(:r AS text) IS NULL OR reason = :r)
                            ORDER BY created_at DESC LIMIT :l OFFSET :o""", s=status, r=reason, l=limit, o=offset)
    for r in rows:
        r["created_at"] = r["created_at"].isoformat()
        r["resolved_at"] = r["resolved_at"].isoformat() if r["resolved_at"] else None
        r["raised_by"] = str(r["raised_by"]) if r["raised_by"] else None
        r["resolved_by"] = str(r["resolved_by"]) if r["resolved_by"] else None
        if r["target_type"] == "product_version":
            p = db.row(conn, """SELECT p.slug, p.name FROM product_versions pv JOIN products p ON p.id = pv.product_id
                                WHERE pv.id = CAST(:v AS uuid)""", v=r["target_ref"])
            r["target_label"] = p["name"] if p else None
            r["target_slug"] = p["slug"] if p else None
    return page(limit, offset, total, rows)


class FlagUpdate(Strict):
    status: Literal["resolved", "dismissed"]
    note: str = Field(min_length=3, max_length=1000)


@router.patch("/flags/{flag_id}")
def update_flag(flag_id: int, body: FlagUpdate, request: Request, admin: CurrentUser = Depends(require_admin),
                conn: Connection = Depends(db.get_conn)):
    old = db.row(conn, "SELECT status FROM data_quality_flags WHERE id = :i", i=flag_id)
    if not old:
        raise not_found("Flag")
    db.execute(conn, """UPDATE data_quality_flags SET status = CAST(:s AS flag_status), resolved_by = :u, resolved_at = now()
                        WHERE id = :i""", s=body.status, u=admin.id, i=flag_id)
    audit(conn, admin.id, f"flag.{body.status}", f"flag:{flag_id}", {"status": old["status"]}, {"status": body.status},
          body.note, request.state.request_id)
    return {"id": flag_id, "status": body.status}


class IngredientFix(Strict):
    product_version_id: str = Field(max_length=60)
    position: int = Field(ge=1, le=500)
    ingredient_id: str | None = Field(None, max_length=120)  # None = mark as genuinely unknown
    reason: str = Field(min_length=3, max_length=500)


@router.post("/ingredient-mappings")
def fix_mapping(body: IngredientFix, request: Request, admin: CurrentUser = Depends(require_admin),
                conn: Connection = Depends(db.get_conn)):
    """Confirm or correct one normalisation (US-003). Produces a new, current formulation version so
    results computed on the old mapping stay reproducible and are marked outdated."""
    old = db.row(conn, """SELECT pi.*, pv.product_id FROM product_ingredients pi
                          JOIN product_versions pv ON pv.id = pi.product_version_id
                          WHERE pi.product_version_id = CAST(:v AS uuid) AND pi.position = :p""",
                 v=body.product_version_id, p=body.position)
    if not old:
        raise not_found("Ingredient entry")
    if body.ingredient_id and not db.scalar(conn, "SELECT 1 FROM ingredients WHERE id = :i", i=body.ingredient_id):
        raise not_found("Ingredient")
    v = db.row(conn, "SELECT * FROM product_versions WHERE id = CAST(:v AS uuid)", v=body.product_version_id)
    if not v["is_current"]:
        raise AppError(409, "NOT_CURRENT", "Only the current formulation can be corrected.")
    items = db.rows(conn, "SELECT * FROM product_ingredients WHERE product_version_id = :v ORDER BY position", v=v["id"])
    n = db.scalar(conn, "SELECT count(*) FROM product_versions WHERE product_id = :p", p=v["product_id"])
    db.execute(conn, "UPDATE product_versions SET is_current = false WHERE id = :v", v=v["id"])
    import hashlib

    new_hash = hashlib.sha256(v["ingredients_hash"] + f"|fix{n}|{body.position}|{body.ingredient_id}".encode()).digest()
    resolved = sum(1 for i in items if (i["ingredient_id"] if i["position"] != body.position else body.ingredient_id))
    nv = db.scalar(conn, """INSERT INTO product_versions (product_id, version_label, raw_ingredients, ingredients_hash,
                              observed_at, market, completeness, verification, notes, source, source_ref, is_current)
                            VALUES (:p, :l, :raw, :h, :o, :m, :c, 'verified', :n, :s, :r, true) RETURNING id""",
                    p=v["product_id"], l=f"v{n + 1} (reviewed correction)", raw=v["raw_ingredients"], h=new_hash,
                    o=v["observed_at"], m=v["market"], c=round(resolved / len(items), 4) if items else 0,
                    n=f"Admin correction at position {body.position}: {body.reason}", s=v["source"], r=v["source_ref"])
    for i in items:
        if i["position"] == body.position:
            iid, method, conf, rs = body.ingredient_id, ("manual" if body.ingredient_id else "unresolved"), \
                (1.0 if body.ingredient_id else 0.0), "confirmed"
        else:
            iid, method, conf, rs = i["ingredient_id"], i["method"], i["confidence"], i["review_status"]
        db.execute(conn, """INSERT INTO product_ingredients (product_version_id, position, raw_name, ingredient_id, method,
                              confidence, review_status, stated_role, concentration_pct, is_key_active)
                            VALUES (:v, :p, :raw, :iid, CAST(:m AS norm_method), :c, CAST(:rs AS review_status), :sr,
                                    :pct, :k)""",
                   v=nv, p=i["position"], raw=i["raw_name"], iid=iid, m=method, c=conf, rs=rs, sr=i["stated_role"],
                   pct=i["concentration_pct"], k=i["is_key_active"])
    if body.ingredient_id:  # learn the alias so future imports resolve it exactly
        db.execute(conn, """INSERT INTO ingredient_aliases (alias_key, ingredient_id, alias) VALUES (:k, :i, :a)
                            ON CONFLICT (alias_key) DO NOTHING""", k=normalize_key(old["raw_name"]), i=body.ingredient_id,
                   a=old["raw_name"])
        catalog.invalidate_master()
    audit(conn, admin.id, "ingredient_mapping.corrected", f"product_version:{v['id']}",
          {"position": body.position, "ingredient_id": old["ingredient_id"]},
          {"ingredient_id": body.ingredient_id, "new_version": str(nv)}, body.reason, request.state.request_id)
    return {"new_version_id": str(nv)}


class IngredientIn(Strict):
    id: str = Field(min_length=2, max_length=110, pattern=r"^[a-z0-9-]+$")
    inci_name: str = Field(min_length=2, max_length=300)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    function_classes: list[str] = Field(default_factory=list, max_length=10)
    reason: str = Field(min_length=3, max_length=500)


@router.post("/ingredients", status_code=201)
def add_ingredient(body: IngredientIn, request: Request, admin: CurrentUser = Depends(require_admin),
                   conn: Connection = Depends(db.get_conn)):
    catalog.upsert_ingredient(conn, body.id, body.inci_name.upper(), "admin-reviewed", body.aliases,
                              body.function_classes, reviewed=True)
    db.execute(conn, "UPDATE ingredients SET reviewed_by = :u WHERE id = :i", u=admin.id, i=body.id)
    catalog.invalidate_master()
    audit(conn, admin.id, "ingredient.upserted", f"ingredient:{body.id}", None, body.model_dump(), body.reason,
          request.state.request_id)
    return {"id": body.id}


# ---------------------------------------------------------------- knowledge
@router.get("/knowledge-versions")
def versions(conn: Connection = Depends(db.get_conn)):
    rows = db.rows(conn, """SELECT k.*, (SELECT count(*) FROM interaction_rules r WHERE r.knowledge_version = k.id) AS rules,
                              (SELECT count(*) FROM evidence_records e WHERE e.knowledge_version = k.id) AS evidence,
                              (SELECT count(*) FROM concern_mappings c WHERE c.knowledge_version = k.id) AS mappings
                            FROM knowledge_versions k ORDER BY k.created_at DESC""")
    out = []
    for r in rows:
        out.append({"id": r["id"], "status": r["status"], "is_demo": r["is_demo"], "notes": r["notes"],
                    "rules": r["rules"], "evidence": r["evidence"], "mappings": r["mappings"],
                    "created_at": r["created_at"].isoformat(),
                    "published_at": r["published_at"].isoformat() if r["published_at"] else None,
                    "blockers": knowledge.publish_blockers(conn, r["id"]) if r["status"] in ("draft", "in_review") else []})
    return {"items": out}


@router.get("/knowledge-versions/{version_id}")
def version_detail(version_id: str, conn: Connection = Depends(db.get_conn)):
    if not db.scalar(conn, "SELECT 1 FROM knowledge_versions WHERE id = :i", i=version_id):
        raise not_found("Knowledge version")
    kv, cmap = knowledge.load(conn, version_id)
    return {"id": version_id, "rules": [r.model_dump(mode="json") for r in kv.rules],
            "evidence": [e.model_dump(mode="json") for e in kv.evidence.values()],
            "concern_mappings": [m.model_dump(mode="json") for m in cmap],
            "blockers": knowledge.publish_blockers(conn, version_id)}


class ImportIn(Strict):
    version_id: str = Field(min_length=3, max_length=60, pattern=r"^[a-z0-9][a-z0-9.\-]+$")


@router.post("/knowledge-versions", status_code=201)
def import_version(body: ImportIn, request: Request, admin: CurrentUser = Depends(require_admin),
                   conn: Connection = Depends(db.get_conn)):
    """Load the reviewed YAML in knowledge/ as a new DRAFT version. Fixture files are refused."""
    directory = Path(get_settings().knowledge_dir)
    res = knowledge.import_directory(conn, directory, body.version_id, actor=admin.id, allow_fixture=False)
    audit(conn, admin.id, "knowledge.imported", f"knowledge:{body.version_id}", None, res, None, request.state.request_id)
    return res


class TransitionIn(Strict):
    to: Literal["in_review", "draft", "published", "retired"]
    reason: str = Field(min_length=3, max_length=500)


@router.post("/knowledge-versions/{version_id}/transition")
def transition(version_id: str, body: TransitionIn, request: Request, admin: CurrentUser = Depends(require_admin),
               conn: Connection = Depends(db.get_conn)):
    if body.to == "retired" and not db.scalar(conn, """SELECT 1 FROM knowledge_versions WHERE status IN ('published','retired')
                                                    AND is_demo = (SELECT is_demo FROM knowledge_versions WHERE id = :i)
                                                    AND id <> :i""", i=version_id):
        raise AppError(409, "LAST_VERSION", "Publish another version before retiring the only one.")
    res = knowledge.set_status(conn, version_id, body.to, admin.id)
    audit(conn, admin.id, f"knowledge.{body.to}", f"knowledge:{version_id}", {"status": res["from"]},
          {"status": res["to"]}, body.reason, request.state.request_id)
    return res


# ---------------------------------------------------------------- operations
@router.get("/audit")
def audit_log(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), conn: Connection = Depends(db.get_conn)):
    total = db.scalar(conn, "SELECT count(*) FROM audit_log")
    rows = db.rows(conn, "SELECT * FROM audit_log ORDER BY id DESC LIMIT :l OFFSET :o", l=limit, o=offset)
    for r in rows:
        r["occurred_at"] = r["occurred_at"].isoformat()
        r["actor_id"] = str(r["actor_id"]) if r["actor_id"] else None
    return page(limit, offset, total, rows)


@router.get("/jobs")
def failed_jobs(status: Literal["failed", "queued", "processing"] = "failed", conn: Connection = Depends(db.get_conn)):
    rows = db.rows(conn, """SELECT id, type, status, error_code, retry_count, created_at, completed_at FROM jobs
                            WHERE status = CAST(:s AS job_status) ORDER BY created_at DESC LIMIT 100""", s=status)
    return {"items": [{**r, "id": str(r["id"]), "created_at": r["created_at"].isoformat(),
                       "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None} for r in rows]}


@router.get("/data-quality")
def data_quality(conn: Connection = Depends(db.get_conn)):
    return {
        "products": db.scalar(conn, "SELECT count(*) FROM products WHERE NOT is_demo"),
        "with_ingredient_list": db.scalar(conn, """SELECT count(*) FROM product_versions pv JOIN products p ON p.id = pv.product_id
                                                   WHERE pv.is_current AND pv.raw_ingredients IS NOT NULL AND NOT p.is_demo"""),
        "fully_resolved": db.scalar(conn, """SELECT count(*) FROM product_versions pv JOIN products p ON p.id = pv.product_id
                                             WHERE pv.is_current AND pv.completeness = 1 AND NOT p.is_demo"""),
        "avg_completeness": float(db.scalar(conn, """SELECT coalesce(avg(pv.completeness), 0) FROM product_versions pv
                                                     JOIN products p ON p.id = pv.product_id
                                                     WHERE pv.is_current AND pv.raw_ingredients IS NOT NULL
                                                     AND NOT p.is_demo""")),
        "ingredients_total": db.scalar(conn, "SELECT count(*) FROM ingredients WHERE NOT is_demo"),
        "ingredients_reviewed": db.scalar(conn, "SELECT count(*) FROM ingredients WHERE reviewed_at IS NOT NULL AND NOT is_demo"),
        "ingredients_with_function_class": db.scalar(conn, """SELECT count(*) FROM ingredients
                                                              WHERE cardinality(function_classes) > 0 AND NOT is_demo"""),
        "price_observations": db.scalar(conn, """SELECT count(*) FROM price_observations po JOIN products p
                                                 ON p.id = po.product_id WHERE NOT p.is_demo"""),
        "open_flags": {r["reason"]: r["n"] for r in db.rows(conn, """SELECT reason, count(*) AS n FROM data_quality_flags
                                                                    WHERE status = 'open' GROUP BY 1""")},
        "published_knowledge": knowledge.active_version_id(conn, False),
        "failed_jobs_24h": db.scalar(conn, "SELECT count(*) FROM jobs WHERE status='failed' AND created_at > now() - interval '1 day'"),
    }
