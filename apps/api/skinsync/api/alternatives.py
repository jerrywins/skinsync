"""Alternatives (UC03, FR-14/15/16). Candidates are real catalogue products only."""

from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db
from ..domain.alternatives import Mode, Preferences, PriceObservation, ProductFeatures, rank_alternatives
from ..domain.compatibility import evaluate
from ..domain.enums import CompatibilityStatus
from ..domain.ingredients import normalize_key
from ..errors import AppError, not_found
from ..security import CurrentUser, optional_user, rate_limit, require_user
from ..services import catalog, comparisons, knowledge
from .common import Strict

router = APIRouter(tags=["alternatives"])
MAX_CANDIDATES = 400


def _price(p: dict | None) -> PriceObservation | None:
    if not p:
        return None
    return PriceObservation(amount=float(p["amount"]), currency=p["currency"].strip(), seller=p["seller"],
                            source=p["source"], observed_at=p["observed_at"].date(), available=p["available"])


def features(conn: Connection, product_id, price=None, identification_confidence: float = 1.0) -> ProductFeatures | None:
    p = catalog.find_product(conn, str(product_id))
    v = catalog.current_version(conn, p["id"])
    if not v:
        return None
    ings = catalog.version_ingredients(conn, v["id"])
    resolved = [i for i in ings if i["ingredient_id"]]
    fcs = sorted({fc for i in resolved for fc in (i["function_classes"] or [])})
    barcode = db.scalar(conn, "SELECT value FROM product_identifiers WHERE product_id = :p LIMIT 1", p=p["id"])
    return ProductFeatures(
        product_id=str(p["id"]), name=p["name"], brand=p["brand"] or "", category=p["category"],
        category_parent=p["category_parent"], barcode=barcode,
        ingredient_ids=tuple(i["ingredient_id"] for i in resolved),
        key_actives=tuple(i["ingredient_id"] for i in resolved if i["is_key_active"]),
        function_classes=tuple(fcs), completeness=float(v["completeness"]),
        identification_confidence=identification_confidence, price=_price(price),
    )


def features_bulk(conn: Connection, product_ids: list, prices: dict) -> dict[str, ProductFeatures]:
    """Load features for many products in two queries (instead of four per product)."""
    if not product_ids:
        return {}
    rows = db.rows(conn, """
        SELECT p.id, p.name, coalesce(b.name, '') AS brand, p.category, p.category_parent, pv.completeness,
               (SELECT pi2.value FROM product_identifiers pi2 WHERE pi2.product_id = p.id ORDER BY pi2.value LIMIT 1) AS barcode,
               array_agg(pi.ingredient_id ORDER BY pi.position) FILTER (WHERE pi.ingredient_id IS NOT NULL) AS ids,
               array_agg(pi.ingredient_id ORDER BY pi.position) FILTER (WHERE pi.ingredient_id IS NOT NULL AND pi.is_key_active) AS keys
        FROM products p JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN product_ingredients pi ON pi.product_version_id = pv.id
        WHERE p.id = ANY(:ids)
        GROUP BY p.id, b.name, pv.id""", ids=[str(i) for i in product_ids])
    master = catalog.load_master(conn)  # function classes come from the (cached) ingredient master

    def fcs(ids) -> tuple[str, ...]:
        return tuple(sorted({fc for i in ids or () if i in master.records for fc in master.records[i].function_classes}))

    return {str(r["id"]): ProductFeatures(
        product_id=str(r["id"]), name=r["name"], brand=r["brand"], category=r["category"],
        category_parent=r["category_parent"], barcode=r["barcode"], ingredient_ids=tuple(r["ids"] or ()),
        key_actives=tuple(r["keys"] or ()), function_classes=fcs(r["ids"]),
        completeness=float(r["completeness"]), price=_price(prices.get(str(r["id"]))),
    ) for r in rows}


class SearchIn(Strict):
    product_id: str = Field(min_length=1, max_length=200)
    mode: Mode = Mode.SIMILAR
    target_ingredients: list[str] = Field(default_factory=list, max_length=10)
    identification_confidence: float = Field(1.0, ge=0, le=1)  # passed through from scan/OCR identification


@router.post("/alternatives/search", dependencies=[Depends(rate_limit("alternatives", 30, 60))])
def search(body: SearchIn, user: CurrentUser | None = Depends(optional_user), conn: Connection = Depends(db.get_conn)):
    ref_p = catalog.find_product(conn, body.product_id)
    ref_v = catalog.current_version(conn, ref_p["id"])
    if ref_v is None or ref_v["raw_ingredients"] is None:
        raise AppError(422, "REFERENCE_INCOMPLETE",
                       f"{ref_p['name']} has no ingredient list on record, so alternatives cannot be compared.")
    if body.mode == Mode.ROUTINE_COMPATIBLE and user is None:
        raise AppError(401, "UNAUTHENTICATED", "Sign in and build a routine to use routine-compatible alternatives.")
    cand_ids = [r["id"] for r in db.rows(conn, """
        WITH ref AS (SELECT pi.ingredient_id FROM product_ingredients pi WHERE pi.product_version_id = :v
                     AND pi.ingredient_id IS NOT NULL)
        SELECT p.id, count(pi.ingredient_id) AS shared
        FROM products p JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
        LEFT JOIN product_ingredients pi ON pi.product_version_id = pv.id AND pi.ingredient_id IN (SELECT ingredient_id FROM ref)
        WHERE p.id <> :p AND p.is_demo = :demo AND pv.raw_ingredients IS NOT NULL
          AND (p.category = :c OR (p.category_parent IS NOT NULL AND p.category_parent = :cp))
        GROUP BY p.id ORDER BY shared DESC, p.id LIMIT :lim""",
        v=ref_v["id"], p=ref_p["id"], demo=ref_p["is_demo"], c=ref_p["category"], cp=ref_p["category_parent"],
        lim=MAX_CANDIDATES)]
    prices = catalog.latest_prices(conn, [ref_p["id"], *cand_ids])
    feats = features_bulk(conn, [ref_p["id"], *cand_ids], prices)
    ref = feats[str(ref_p["id"])].model_copy(update={"identification_confidence": body.identification_confidence})
    cands = [feats[str(c)] for c in cand_ids if str(c) in feats]

    prefs_raw, notes = {}, []
    if user:
        prefs_raw = db.scalar(conn, "SELECT preferences FROM profiles WHERE user_id = :u", u=user.id) or {}
    avoid_ing = set()
    for name in prefs_raw.get("avoided_ingredients", []):
        rec = catalog.load_master(conn).lookup_exact(normalize_key(name))
        if rec:
            avoid_ing.add(rec.id)
        else:
            notes.append(f"Avoided ingredient '{name}' is not recognised, so it could not be filtered.")
    if prefs_raw.get("fragrance_free"):
        notes.append("Fragrance-free preference not applied: fragrance status is not yet recorded for ingredients.")
    targets = set()
    master = catalog.load_master(conn)
    for t in body.target_ingredients:
        rec = master.lookup_exact(normalize_key(t)) or (master.records.get(t))
        if rec:
            targets.add(rec.id)
        else:
            notes.append(f"Target ingredient '{t}' is not recognised.")
    prefs = Preferences(avoid_ingredients=frozenset(avoid_ing),
                        avoid_brands=frozenset(prefs_raw.get("avoided_brands", [])),
                        preferred_brands=frozenset(prefs_raw.get("preferred_brands", [])),
                        target_ingredients=frozenset(targets))

    conflicts: set[str] = set()
    if body.mode == Mode.ROUTINE_COMPATIBLE:
        routine_versions = [r["vid"] for r in db.rows(conn, """SELECT DISTINCT pv.id AS vid FROM routines r
                              JOIN routine_items ri ON ri.routine_id = r.id
                              JOIN product_versions pv ON pv.product_id = ri.product_id AND pv.is_current
                              WHERE r.user_id = :u AND r.is_active""", u=user.id)]
        if not routine_versions:
            raise AppError(422, "NO_ROUTINE", "Add products to a routine first.")
        kv, _ = knowledge.load(conn, comparisons.knowledge_for(conn, [ref_p]))
        routine_forms = [catalog.formulation_for_version(conn, v) for v in routine_versions]
        for c in cands:
            cf = catalog.formulation_for_version(conn, catalog.current_version(conn, c.product_id)["id"])
            for rf in routine_forms:
                st = evaluate(cf, rf, kv).status
                if st in (CompatibilityStatus.CAUTION, CompatibilityStatus.STRONG_CAUTION):
                    conflicts.add(c.product_id)
                    break
        if not kv.rules:
            notes.append("No reviewed interaction rules exist yet, so routine compatibility cannot exclude anything.")

    res = rank_alternatives(ref, cands, body.mode, today=date.today(), prefs=prefs,
                            routine_conflicts=frozenset(conflicts))
    payload = res.model_dump(mode="json")
    payload["notes"] = notes
    payload["candidates_considered"] = len(cands)
    sid = db.scalar(conn, """INSERT INTO alternative_searches (user_id, reference_product, reference_version, mode,
                               constraints, result) VALUES (:u, :p, :v, :m, CAST(:c AS jsonb), CAST(:r AS jsonb))
                             RETURNING id""",
                    u=user.id if user else None, p=ref_p["id"], v=ref_v["id"], m=body.mode.value,
                    c=json.dumps({"targets": sorted(targets)}), r=json.dumps(payload))
    for a in res.results:
        db.execute(conn, """INSERT INTO product_alternatives (search_id, rank, product_id, score, dimensions)
                            VALUES (:s, :r, :p, :sc, CAST(:d AS jsonb))""", s=sid, r=a.rank, p=a.product_id,
                   sc=a.score, d=json.dumps([d.model_dump() for d in a.dimensions]))
    return _view(conn, str(sid), payload, ref_p, saved=False)


def _view(conn, sid, payload, ref_p, saved) -> dict:
    slugs = {str(r["id"]): (r["slug"], r["image_url"], r["category"]) for r in db.rows(
        conn, "SELECT id, slug, image_url, category FROM products WHERE id = ANY(:ids)",
        ids=[r["product_id"] for r in payload["results"]])} if payload["results"] else {}
    for r in payload["results"]:
        r["slug"], r["image_url"], r["category"] = slugs.get(r["product_id"], (None, None, None))
    return {"id": sid, "saved": saved, "reference": {"id": str(ref_p["id"]), "slug": ref_p["slug"], "name": ref_p["name"],
                                                     "brand": ref_p["brand"], "is_demo": ref_p["is_demo"],
                                                     "image_url": ref_p["image_url"]}, **payload}


def load_search(conn: Connection, search_id: str, user_id: str | None, *, via_share: bool) -> dict:
    """Internal: via_share is set only by the share service after validating a token."""
    import uuid

    try:
        uuid.UUID(search_id)
    except ValueError as e:
        raise not_found("Alternative search") from e
    s = db.row(conn, "SELECT * FROM alternative_searches WHERE id = :i", i=search_id)
    if not s or (s["user_id"] is not None and str(s["user_id"]) != user_id and not via_share):
        raise not_found("Alternative search")
    return _view(conn, str(s["id"]), s["result"], catalog.find_product(conn, str(s["reference_product"])), s["saved"])


@router.get("/alternatives/{search_id}")
def get_search(search_id: str, user: CurrentUser | None = Depends(optional_user), conn: Connection = Depends(db.get_conn)):
    return load_search(conn, search_id, user.id if user else None, via_share=False)


@router.post("/alternatives/{search_id}/save")
def save_search(search_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    load_search(conn, search_id, user.id, via_share=False)  # validates id and ownership
    s = db.row(conn, "SELECT user_id FROM alternative_searches WHERE id = CAST(:i AS uuid)", i=search_id)
    if not s or (s["user_id"] is not None and str(s["user_id"]) != user.id):
        raise not_found("Alternative search")
    db.execute(conn, "UPDATE alternative_searches SET user_id = :u, saved = true WHERE id = CAST(:i AS uuid)",
               u=user.id, i=search_id)
    return {"saved": True}
