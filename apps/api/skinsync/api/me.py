"""Registered-user features. Every query is scoped by user_id (object-level authorisation)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db, storage
from ..config import get_settings
from ..domain.compatibility import evaluate_routine
from ..domain.enums import CompatibilityStatus, FindingType
from ..errors import AppError, not_found
from ..security import REFRESH_COOKIE, CurrentUser, audit, end_session, require_user, verify_password
from ..services import catalog, comparisons, knowledge
from .common import Strict

router = APIRouter(tags=["me"])

SKIN_TYPES = Literal["dry", "oily", "combination", "normal", "sensitive", "unsure"]


# ---------------------------------------------------------------- account
@router.get("/me")
def me(user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    p = db.row(conn, "SELECT skin_type, preferences FROM profiles WHERE user_id = :u", u=user.id) or {}
    consents = db.rows(conn, """SELECT DISTINCT ON (purpose) purpose, granted, policy_version, recorded_at
                                FROM consents WHERE user_id = :u ORDER BY purpose, recorded_at DESC""", u=user.id)
    return {"id": user.id, "email": user.email, "role": user.role, "email_verified": user.email_verified,
            "profile": {"skin_type": p.get("skin_type"), "preferences": p.get("preferences") or {}},
            "consents": {c["purpose"]: c["granted"] for c in consents}}


class Preferences(Strict):
    budget_max_inr: int | None = Field(None, ge=0, le=1_000_000)
    preferred_brands: list[str] = Field(default_factory=list, max_length=30)
    avoided_brands: list[str] = Field(default_factory=list, max_length=30)
    avoided_ingredients: list[str] = Field(default_factory=list, max_length=60)
    fragrance_free: bool = False
    routine_complexity: Literal["minimal", "standard", "detailed"] | None = None


class ProfileIn(Strict):
    skin_type: SKIN_TYPES | None = None
    preferences: Preferences = Preferences()


@router.put("/me/profile")
def update_profile(body: ProfileIn, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    db.execute(conn, """INSERT INTO profiles (user_id, skin_type, preferences) VALUES (:u, :s, CAST(:p AS jsonb))
                        ON CONFLICT (user_id) DO UPDATE SET skin_type = EXCLUDED.skin_type,
                          preferences = EXCLUDED.preferences, updated_at = now()""",
               u=user.id, s=body.skin_type, p=body.preferences.model_dump_json())
    return {"saved": True}


class ConsentIn(Strict):
    purpose: Literal["skin_image_processing", "analytics"]
    granted: bool


@router.post("/me/consents")
def consent(body: ConsentIn, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    db.execute(conn, "INSERT INTO consents (user_id, purpose, policy_version, granted) VALUES (:u, :p, :v, :g)",
               u=user.id, p=body.purpose, v=get_settings().policy_version, g=body.granted)
    return {"recorded": True}


class ClaimIn(Strict):
    claim_tokens: list[str] = Field(max_length=20)


@router.post("/me/claim")
def claim(body: ClaimIn, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    return {"claimed": sum(1 for t in body.claim_tokens if comparisons.claim(conn, t, user.id))}


class DeleteIn(Strict):
    password: str = Field(min_length=1, max_length=256)
    confirm: Literal["DELETE"]


@router.delete("/me")
def delete_account(body: DeleteIn, request: Request, response: Response, user: CurrentUser = Depends(require_user),
                   conn: Connection = Depends(db.get_conn)):
    """FR-20 / US-010: re-authenticate, then delete every personal row and every stored image."""
    h = db.scalar(conn, "SELECT password_hash FROM users WHERE id = :u", u=user.id)
    if not verify_password(h, body.password):
        raise AppError(401, "INVALID_CREDENTIALS", "Password is incorrect.")
    keys = [r["object_key"] for r in db.rows(conn, "SELECT object_key FROM uploads WHERE user_id = :u", u=user.id)]
    for k in keys:
        storage.backend().delete(k)
    audit(conn, user.id, "account.deleted", f"user:{user.id}", new={"images_deleted": len(keys)},
          request_id=request.state.request_id)
    db.execute(conn, "DELETE FROM users WHERE id = :u", u=user.id)  # cascades to every personal table
    end_session(conn, response, request.cookies.get(REFRESH_COOKIE))
    return {"deleted": True, "images_deleted": len(keys)}


# ---------------------------------------------------------------- shelf
class ShelfIn(Strict):
    product_id: str = Field(min_length=1, max_length=200)
    status: Literal["owned", "wishlist"] = "owned"
    note: str | None = Field(None, max_length=1000)


@router.get("/shelf")
def shelf(q: str | None = None, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    items = db.rows(conn, f"""SELECT s.status, s.note, s.added_at, {catalog.PRODUCT_COLS}, pv.id AS version_id,
                                pv.completeness, pv.raw_ingredients IS NOT NULL AS has_ingredients
                              FROM shelf_items s JOIN products p ON p.id = s.product_id
                              LEFT JOIN brands b ON b.id = p.brand_id
                              LEFT JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                              WHERE s.user_id = :u AND (CAST(:q AS text) IS NULL
                                OR lower(p.name || ' ' || coalesce(b.name, '')) LIKE '%' || lower(CAST(:q AS text)) || '%')
                              ORDER BY s.added_at DESC""", u=user.id, q=q)
    from .catalog import _summary

    return {"items": [{**_summary(i), "status": i["status"], "note": i["note"], "added_at": i["added_at"].isoformat(),
                       "missing_data": not i["has_ingredients"]} for i in items]}


@router.post("/shelf", status_code=201)
def add_to_shelf(body: ShelfIn, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    p = catalog.find_product(conn, body.product_id)
    n = db.execute(conn, """INSERT INTO shelf_items (user_id, product_id, status, note) VALUES (:u, :p, :s, :n)
                            ON CONFLICT DO NOTHING""", u=user.id, p=p["id"], s=body.status, n=body.note)
    if n == 0:
        raise AppError(409, "ALREADY_ON_SHELF", f"{p['name']} is already on your shelf.")
    return {"added": True, "product_id": str(p["id"])}


@router.delete("/shelf/{product_id}")
def remove_from_shelf(product_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    p = catalog.find_product(conn, product_id)
    if not db.execute(conn, "DELETE FROM shelf_items WHERE user_id = :u AND product_id = :p", u=user.id, p=p["id"]):
        raise not_found("Shelf item")
    return {"removed": True}


# ---------------------------------------------------------------- routines
class RoutineStepIn(Strict):
    product_id: str = Field(min_length=1, max_length=200)
    step_kind: Literal["cleanser", "toner", "treatment", "serum", "eye_care", "moisturizer", "sunscreen", "mask",
                       "other"] | None = None
    frequency: str | None = Field(None, max_length=60)
    note: str | None = Field(None, max_length=1000)


class RoutineIn(Strict):
    name: str = Field(min_length=1, max_length=120)
    time_of_day: Literal["morning", "evening"]
    steps: list[RoutineStepIn] = Field(default_factory=list, max_length=20)


def _own_routine(conn, routine_id: str, user_id: str) -> dict:
    import uuid

    try:
        uuid.UUID(routine_id)
    except ValueError as e:
        raise not_found("Routine") from e
    r = db.row(conn, "SELECT * FROM routines WHERE id = :i AND user_id = :u", i=routine_id, u=user_id)
    if not r:
        raise not_found("Routine")
    return r


def _write_steps(conn, routine_id, steps: list[RoutineStepIn]) -> list[str]:
    warnings, seen = [], set()
    db.execute(conn, "DELETE FROM routine_items WHERE routine_id = :r", r=routine_id)
    for i, s in enumerate(steps, start=1):
        p = catalog.find_product(conn, s.product_id)
        if p["id"] in seen:
            warnings.append(f"{p['name']} appears more than once in this routine.")
        seen.add(p["id"])
        db.execute(conn, """INSERT INTO routine_items (routine_id, step_order, product_id, step_kind, frequency, note)
                            VALUES (:r, :o, :p, :k, :f, :n)""", r=routine_id, o=i, p=p["id"], k=s.step_kind,
                   f=s.frequency, n=s.note)
    return warnings


def _routine_view(conn, r: dict) -> dict:
    steps = db.rows(conn, f"""SELECT ri.step_order, ri.step_kind, ri.frequency, ri.note, {catalog.PRODUCT_COLS},
                                pv.id AS version_id, pv.completeness, pv.raw_ingredients IS NOT NULL AS has_ingredients
                              FROM routine_items ri JOIN products p ON p.id = ri.product_id
                              LEFT JOIN brands b ON b.id = p.brand_id
                              LEFT JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                              WHERE ri.routine_id = :r ORDER BY ri.step_order""", r=r["id"])
    from .catalog import _summary

    return {"id": str(r["id"]), "name": r["name"], "time_of_day": r["time_of_day"], "is_active": r["is_active"],
            "updated_at": r["updated_at"].isoformat(),
            "steps": [{"order": s["step_order"], "step_kind": s["step_kind"], "frequency": s["frequency"],
                       "note": s["note"], "product": _summary(s)} for s in steps]}


@router.get("/routines")
def routines(user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    rs = db.rows(conn, "SELECT * FROM routines WHERE user_id = :u ORDER BY time_of_day, created_at", u=user.id)
    return {"items": [_routine_view(conn, r) for r in rs]}


@router.post("/routines", status_code=201)
def create_routine(body: RoutineIn, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    if db.scalar(conn, "SELECT count(*) FROM routines WHERE user_id = :u", u=user.id) >= 20:
        raise AppError(409, "TOO_MANY_ROUTINES", "You can keep up to 20 routines.")
    rid = db.scalar(conn, "INSERT INTO routines (user_id, name, time_of_day) VALUES (:u, :n, :t) RETURNING id",
                    u=user.id, n=body.name, t=body.time_of_day)
    warnings = _write_steps(conn, rid, body.steps)
    return {**_routine_view(conn, db.row(conn, "SELECT * FROM routines WHERE id = :i", i=rid)), "warnings": warnings}


@router.get("/routines/{routine_id}")
def get_routine(routine_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    return _routine_view(conn, _own_routine(conn, routine_id, user.id))


@router.put("/routines/{routine_id}")
def update_routine(routine_id: str, body: RoutineIn, user: CurrentUser = Depends(require_user),
                   conn: Connection = Depends(db.get_conn)):
    r = _own_routine(conn, routine_id, user.id)
    db.execute(conn, "UPDATE routines SET name=:n, time_of_day=:t, updated_at=now() WHERE id=:i",
               n=body.name, t=body.time_of_day, i=r["id"])
    warnings = _write_steps(conn, r["id"], body.steps)
    return {**_routine_view(conn, db.row(conn, "SELECT * FROM routines WHERE id = :i", i=r["id"])),
            "warnings": warnings}


@router.delete("/routines/{routine_id}")
def delete_routine(routine_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    r = _own_routine(conn, routine_id, user.id)
    db.execute(conn, "DELETE FROM routines WHERE id = :i", i=r["id"])
    return {"deleted": True}


@router.post("/routines/{routine_id}/analyze")
def analyze_routine(routine_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    """SC-04: pairwise compatibility, duplicated actives/ingredients, missing data. Missing data is never 'clear'."""
    r = _own_routine(conn, routine_id, user.id)
    steps = db.rows(conn, """SELECT ri.step_order, p.id AS product_id, p.name, p.is_demo, pv.id AS version_id
                             FROM routine_items ri JOIN products p ON p.id = ri.product_id
                             LEFT JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                             WHERE ri.routine_id = :r ORDER BY ri.step_order""", r=r["id"])
    if len(steps) < 2:
        raise AppError(422, "ROUTINE_TOO_SHORT", "Add at least two products to check a routine.")
    missing = [s["name"] for s in steps if s["version_id"] is None]
    forms = [catalog.formulation_for_version(conn, s["version_id"]) for s in steps if s["version_id"]]
    prods = [catalog.find_product(conn, s["product_id"]) for s in steps if s["version_id"]]
    kv_id = comparisons.knowledge_for(conn, prods)
    kv, _ = knowledge.load(conn, kv_id)
    pairs = evaluate_routine(forms, kv)
    # duplicated ingredients across products (factual, no scientific claim)
    where: dict[str, set[str]] = {}
    for f in forms:
        for i in f.ingredients:
            if i.resolved and i.stated_role == "listed":
                where.setdefault(i.inci_name, set()).add(f.product_name)
    shared = sorted(((n, sorted(ps)) for n, ps in where.items() if len(ps) > 1), key=lambda x: (-len(x[1]), x[0]))
    dup_actives = sorted({f.title for _, _, res in pairs for f in res.findings if f.type == FindingType.SHARED_KEY_ACTIVE})
    statuses = [res.status for _, _, res in pairs]
    rank = [CompatibilityStatus.STRONG_CAUTION, CompatibilityStatus.CAUTION, CompatibilityStatus.DATA_INCOMPLETE,
            CompatibilityStatus.INSUFFICIENT_EVIDENCE, CompatibilityStatus.NO_NOTABLE_INTERACTION]
    overall = min(statuses, key=rank.index) if statuses else CompatibilityStatus.DATA_INCOMPLETE
    if missing and overall == CompatibilityStatus.NO_NOTABLE_INTERACTION:
        overall = CompatibilityStatus.DATA_INCOMPLETE
    from ..domain.enums import STATUS_LABELS

    return {
        "routine_id": str(r["id"]), "status": overall.value, "status_label": STATUS_LABELS[overall],
        "knowledge_version": kv_id, "knowledge_is_demo": kv.is_demo,
        "pairs": [{"a": forms[i].product_name, "b": forms[j].product_name, "a_order": i + 1, "b_order": j + 1,
                   "result": res.model_dump(mode="json")} for i, j, res in pairs],
        "duplicated_key_actives": dup_actives,
        "shared_ingredients": [{"ingredient": n, "products": ps} for n, ps in shared[:30]],
        "missing_data": [f"{n} has no formulation on record and was not checked." for n in missing] +
                        [f"{f.product_name}: {sum(1 for i in f.ingredients if not i.resolved)} unrecognised ingredient(s)"
                         for f in forms if any(not i.resolved for i in f.ingredients)],
        "sequencing": ("Sequencing guidance requires reviewed knowledge, which is not yet available."
                       if not kv.rules else "Step order is shown as you set it; rules above apply regardless of order."),
    }


# ---------------------------------------------------------------- history
@router.get("/history")
def history(kind: Literal["all", "comparison", "skin_analysis", "alternative_search"] = "all",
            user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    out = []
    if kind in ("all", "comparison"):
        for c in db.rows(conn, """SELECT c.*, pa.name AS a_name, pb.name AS b_name FROM comparisons c
                                  JOIN product_versions va ON va.id = c.product_version_a JOIN products pa ON pa.id = va.product_id
                                  JOIN product_versions vb ON vb.id = c.product_version_b JOIN products pb ON pb.id = vb.product_id
                                  WHERE c.user_id = :u AND c.saved ORDER BY c.created_at DESC LIMIT 100""", u=user.id):
            out.append({"type": "comparison", "id": str(c["id"]), "title": f"{c['a_name']} + {c['b_name']}",
                        "status": c["status"], "created_at": c["created_at"].isoformat(),
                        "outdated": comparisons.outdated_reasons(conn, c)})
    if kind in ("all", "skin_analysis"):
        for s in db.rows(conn, """SELECT id, status, created_at, model_version, is_demo_model FROM skin_analyses
                                  WHERE user_id = :u ORDER BY created_at DESC LIMIT 100""", u=user.id):
            out.append({"type": "skin_analysis", "id": str(s["id"]), "title": "Skin analysis", "status": s["status"],
                        "created_at": s["created_at"].isoformat(), "is_demo_model": s["is_demo_model"],
                        "outdated": []})
    if kind in ("all", "alternative_search"):
        for a in db.rows(conn, """SELECT s.id, s.mode, s.created_at, s.reference_version, p.name FROM alternative_searches s
                                  JOIN products p ON p.id = s.reference_product
                                  WHERE s.user_id = :u AND s.saved ORDER BY s.created_at DESC LIMIT 100""", u=user.id):
            cur = db.scalar(conn, "SELECT is_current FROM product_versions WHERE id = :v", v=a["reference_version"])
            out.append({"type": "alternative_search", "id": str(a["id"]), "title": f"Alternatives to {a['name']}",
                        "status": a["mode"], "created_at": a["created_at"].isoformat(),
                        "outdated": [] if cur else ["The reference product has a newer formulation."]})
    out.sort(key=lambda x: x["created_at"], reverse=True)
    return {"items": out}


@router.delete("/history/{kind}/{item_id}")
def delete_history(kind: Literal["comparison", "alternative_search"], item_id: str,
                   user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    import uuid

    try:
        uuid.UUID(item_id)
    except ValueError as e:
        raise not_found("Item") from e
    table = {"comparison": "comparisons", "alternative_search": "alternative_searches"}[kind]
    if not db.execute(conn, f"DELETE FROM {table} WHERE id = :i AND user_id = :u", i=item_id, u=user.id):
        raise not_found("Item")
    db.execute(conn, "UPDATE shares SET revoked_at = now() WHERE target_id = :i AND revoked_at IS NULL", i=item_id)
    return {"deleted": True}
