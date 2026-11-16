"""Products, brands, categories, ingredients, normalisation, barcode lookup, data reports."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.engine import Connection

from .. import db
from ..config import get_settings
from ..domain.alternatives import price_state
from ..errors import AppError, not_found
from ..ingest.obf import load_category_map
from ..security import CurrentUser, optional_user, rate_limit
from ..services import catalog
from .common import Strict, page

router = APIRouter(tags=["catalog"])


def _price_view(p: dict | None) -> dict:
    from datetime import date

    from ..domain.alternatives import PriceObservation

    if not p:
        return {"state": "unavailable", "label": "Price unavailable"}
    obs = PriceObservation(amount=float(p["amount"]), currency=p["currency"], seller=p["seller"], source=p["source"],
                           observed_at=p["observed_at"].date(), available=p["available"])
    st = price_state(obs, date.today())
    view = {"state": st.value, "amount": float(p["amount"]), "currency": p["currency"], "seller": p["seller"],
            "source": p["source"], "observed_at": p["observed_at"].date().isoformat(),
            "is_test": p["source"] == catalog.TEST_PRICE_SOURCE}
    view["label"] = "Price unavailable" if st.value == "unavailable" else \
        f"Observed {view['observed_at']}" + (" (may be out of date)" if st.value == "stale" else "")
    if view["is_test"]:
        view["label"] = "TEST PRICE — not real (random value for testing)"
    return view


def _summary(p: dict, price: dict | None = None) -> dict:
    return {"id": str(p["id"]), "slug": p["slug"], "name": p["name"], "brand": p["brand"], "brand_slug": p["brand_slug"],
            "category": p["category"], "image_url": p["image_url"], "is_demo": p["is_demo"],
            "version_id": str(p["version_id"]) if p.get("version_id") else None,
            "completeness": float(p["completeness"]) if p.get("completeness") is not None else 0.0,
            "has_ingredients": bool(p.get("has_ingredients")), "price": _price_view(price)}


@router.get("/products", dependencies=[Depends(rate_limit("search", 120, 60))])
def list_products(q: str | None = Query(None, max_length=120), brand: str | None = Query(None, max_length=80),
                  category: str | None = Query(None, max_length=40), ingredient: str | None = Query(None, max_length=120),
                  limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=5000),
                  conn: Connection = Depends(db.get_conn)):
    items, total = catalog.search(conn, q, brand, category, ingredient, limit, offset,
                                  include_demo=get_settings().demo_mode)
    prices = catalog.latest_prices(conn, [i["id"] for i in items])
    return page(limit, offset, total, [_summary(i, prices.get(str(i["id"]))) for i in items])


@router.get("/products/barcode/{code}")
def by_barcode(code: str, conn: Connection = Depends(db.get_conn)):
    if not code.isdigit() or not 6 <= len(code) <= 14:
        raise AppError(422, "INVALID_BARCODE", "That does not look like a product barcode.")
    rows = db.rows(conn, f"""SELECT {catalog.PRODUCT_COLS}, pv.id AS version_id, pv.completeness,
                               pv.raw_ingredients IS NOT NULL AS has_ingredients
                             FROM product_identifiers pi JOIN products p ON p.id = pi.product_id
                             LEFT JOIN brands b ON b.id = p.brand_id
                             LEFT JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                             WHERE pi.value = :c""", c=code)
    if not rows:
        return {"status": "not_found", "candidates": []}
    return {"status": "found" if len(rows) == 1 else "ambiguous", "candidates": [_summary(r) for r in rows]}


@router.get("/products/{ref}")
def product_detail(ref: str, conn: Connection = Depends(db.get_conn)):
    p = catalog.find_product(conn, ref)
    v = catalog.current_version(conn, p["id"])
    ingredients = []
    if v:
        for r in catalog.version_ingredients(conn, v["id"]):
            ingredients.append({"position": r["position"], "raw": r["raw_name"], "ingredient_id": r["ingredient_id"],
                                "inci_name": r["inci_name"], "function_classes": r["function_classes"] or [],
                                "method": r["method"], "confidence": float(r["confidence"]),
                                "review_status": r["review_status"], "stated_role": r["stated_role"],
                                "is_key_active": r["is_key_active"],
                                "name_reviewed": bool(r["ingredient_reviewed"])})
    versions = db.rows(conn, """SELECT id, version_label, observed_at, completeness, is_current, source, verification
                                FROM product_versions WHERE product_id = :p ORDER BY created_at DESC""", p=p["id"])
    prices = db.rows(conn, """SELECT amount, currency, seller, source, available, observed_at FROM price_observations
                              WHERE product_id = :p AND (:allow_test OR source <> :test_src)
                              ORDER BY observed_at DESC LIMIT 10""", p=p["id"],
                     allow_test=catalog.test_prices_allowed(), test_src=catalog.TEST_PRICE_SOURCE)
    barcodes = [r["value"] for r in db.rows(conn, "SELECT value FROM product_identifiers WHERE product_id = :p",
                                            p=p["id"])]
    unresolved = sum(1 for i in ingredients if i["ingredient_id"] is None)
    return {
        "id": str(p["id"]), "slug": p["slug"], "name": p["name"], "brand": p["brand"], "brand_slug": p["brand_slug"],
        "category": p["category"], "market": p["market"], "image_url": p["image_url"], "is_demo": p["is_demo"],
        "barcodes": barcodes,
        "provenance": {"source": p["source"], "source_ref": p["source_ref"],
                       "retrieved_at": p["retrieved_at"].isoformat(),
                       "licence": "ODbL-1.0" if p["source"] == "openbeautyfacts" else None,
                       "source_url": f"https://world.openbeautyfacts.org/product/{p['source_ref']}"
                       if p["source"] == "openbeautyfacts" else None},
        "current_version": None if not v else {
            "id": str(v["id"]), "label": v["version_label"], "observed_at": v["observed_at"].isoformat(),
            "completeness": float(v["completeness"]), "verification": v["verification"],
            "has_ingredient_list": v["raw_ingredients"] is not None, "raw_ingredients": v["raw_ingredients"],
            "source": v["source"]},
        "ingredients": ingredients,
        "unresolved_count": unresolved,
        "versions": [{"id": str(x["id"]), "label": x["version_label"], "observed_at": x["observed_at"].isoformat(),
                      "completeness": float(x["completeness"]), "is_current": x["is_current"]} for x in versions],
        "prices": [_price_view(x) for x in prices] or [_price_view(None)],
        "indexable": bool(v and v["raw_ingredients"] and float(v["completeness"]) >= 0.6 and not p["is_demo"]),
    }


@router.get("/brands/{slug}")
def brand(slug: str, limit: int = Query(50, ge=1, le=100), conn: Connection = Depends(db.get_conn)):
    b = db.row(conn, "SELECT id, name, slug FROM brands WHERE slug = :s", s=slug)
    if not b:
        raise not_found("Brand")
    items, total = catalog.search(conn, None, slug, None, None, limit, 0, include_demo=get_settings().demo_mode)
    return {"name": b["name"], "slug": b["slug"], "total": total, "products": [_summary(i) for i in items]}


@router.get("/categories")
def categories(conn: Connection = Depends(db.get_conn)):
    _, cats = load_category_map()
    counts = {r["category"]: r["n"] for r in db.rows(conn, "SELECT category, count(*) AS n FROM products GROUP BY 1")}
    return [{"id": c["id"], "label": c["label"], "parent": c["parent"], "count": counts.get(c["id"], 0)} for c in cats]


@router.get("/ingredients", dependencies=[Depends(rate_limit("search", 120, 60))])
def list_ingredients(q: str | None = Query(None, max_length=120), limit: int = Query(30, ge=1, le=100),
                     offset: int = Query(0, ge=0, le=5000), conn: Connection = Depends(db.get_conn)):
    where, params = "(:demo OR NOT i.is_demo)", {"demo": get_settings().demo_mode, "lim": limit, "off": offset}
    order = "i.inci_name"
    if q:
        params["q"] = q.strip().lower()
        where += """ AND (EXISTS (SELECT 1 FROM ingredient_aliases a WHERE a.ingredient_id = i.id
                                  AND (a.alias_key % :q OR a.alias_key LIKE '%' || :q || '%')))"""
        order = "(lower(i.inci_name) = :q) DESC, similarity(lower(i.inci_name), :q) DESC, i.inci_name"
    total = db.scalar(conn, f"SELECT count(*) FROM ingredients i WHERE {where}", **params)
    items = db.rows(conn, f"""SELECT i.id, i.inci_name, i.function_classes, i.source, i.reviewed_at IS NOT NULL AS reviewed,
                                (SELECT count(*) FROM product_ingredients pi JOIN product_versions pv
                                   ON pv.id = pi.product_version_id AND pv.is_current
                                 WHERE pi.ingredient_id = i.id) AS product_count
                              FROM ingredients i WHERE {where} ORDER BY {order} LIMIT :lim OFFSET :off""", **params)
    return page(limit, offset, total, [{**i, "function_classes": i["function_classes"] or []} for i in items])


@router.get("/ingredients/{ingredient_id}")
def ingredient_detail(ingredient_id: str, conn: Connection = Depends(db.get_conn)):
    i = db.row(conn, "SELECT * FROM ingredients WHERE id = :i", i=ingredient_id)
    if not i:
        raise not_found("Ingredient")
    aliases = [a["alias"] for a in db.rows(conn, "SELECT alias FROM ingredient_aliases WHERE ingredient_id = :i ORDER BY 1",
                                           i=ingredient_id)]
    products = db.rows(conn, f"""SELECT {catalog.PRODUCT_COLS}, pv.id AS version_id, pv.completeness,
                                   true AS has_ingredients, pi.position
                                 FROM product_ingredients pi JOIN product_versions pv ON pv.id = pi.product_version_id
                                   AND pv.is_current JOIN products p ON p.id = pv.product_id
                                 LEFT JOIN brands b ON b.id = p.brand_id
                                 WHERE pi.ingredient_id = :i AND (:demo OR NOT p.is_demo)
                                 ORDER BY pi.position, p.name LIMIT 24""", i=ingredient_id, demo=get_settings().demo_mode)
    count = db.scalar(conn, """SELECT count(*) FROM product_ingredients pi JOIN product_versions pv
                                 ON pv.id = pi.product_version_id AND pv.is_current WHERE pi.ingredient_id = :i""",
                      i=ingredient_id)
    kv_id = db.scalar(conn, "SELECT id FROM knowledge_versions WHERE status='published' AND is_demo = :d", d=i["is_demo"])
    evidence, rules = [], []
    if kv_id:
        from ..services import knowledge

        kv, _ = knowledge.load(conn, kv_id)
        classes = set(i["function_classes"] or [])
        seen = set()
        for r in kv.rules:
            terms = (*r.side_a, *r.side_b)
            if any(t.ingredient == ingredient_id or (t.function_class and t.function_class in classes) for t in terms):
                rules.append({"code": r.code, "interaction_type": r.interaction_type.value, "severity": r.severity.value,
                              "summary": r.mechanism_summary})
                for e in kv.evidence_for(r):
                    if e.id not in seen:
                        seen.add(e.id)
                        evidence.append({"id": e.id, "claim": e.claim, "citation": e.citation,
                                         "source_type": e.source_type.value, "strength": e.strength.value})
    return {
        "id": i["id"], "inci_name": i["inci_name"], "aliases": aliases, "function_classes": i["function_classes"] or [],
        "considerations": i["considerations"], "is_demo": i["is_demo"],
        "source": i["source"], "reviewed": i["reviewed_at"] is not None,
        "data_status": None if i["reviewed_at"] else (
            "This ingredient name was observed in product data and has not been reviewed. "
            "Its functions and considerations are not yet recorded."),
        "product_count": count, "products": [_summary(p) for p in products], "evidence": evidence,
        "related_rules": rules, "knowledge_version": kv_id,
    }


class NormalizeIn(Strict):
    text: str = Field(min_length=1, max_length=8000)


@router.post("/ingredients/normalize", dependencies=[Depends(rate_limit("normalize", 60, 60))])
def normalize(body: NormalizeIn, conn: Connection = Depends(db.get_conn)):
    from ..domain.ingredients import normalize_list

    items = normalize_list(body.text, catalog.load_master(conn))
    return {"items": [i.model_dump(mode="json") for i in items],
            "resolved": sum(1 for i in items if i.resolved), "total": len(items)}


class ReportIn(Strict):
    target_type: Literal["product", "product_version", "ingredient", "price", "evidence"]
    target_ref: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=3, max_length=1000)


@router.post("/reports", status_code=201, dependencies=[Depends(rate_limit("report", 10, 3600))])
def report(body: ReportIn, user: CurrentUser | None = Depends(optional_user), conn: Connection = Depends(db.get_conn)):
    fid = catalog.raise_flag(conn, body.target_type, body.target_ref, "user_report", "user",
                             {"message": body.message}, user.id if user else None)
    return {"flag_id": fid, "status": "open"}
