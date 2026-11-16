"""Product recommendations from concern mappings (FR-11, SkinIQ §18-20).

observation -> reviewed mapping -> ingredient classes -> catalogue products containing an
ingredient of that class -> user filters -> routine compatibility -> ranked, explained.

The model never names a product. If no reviewed mapping or no product with a reviewed
function class exists, the result says so instead of guessing.
"""

from __future__ import annotations

from sqlalchemy.engine import Connection

from .. import db
from ..domain.compatibility import evaluate
from ..domain.enums import CompatibilityStatus
from ..domain.skin import SkinResult
from . import catalog, knowledge

PER_CONCERN = 3


def products_for(conn: Connection, result: SkinResult, user_id, *, demo: bool) -> list[dict]:
    prefs = {}
    routine_versions = []
    if user_id:
        prefs = db.scalar(conn, "SELECT preferences FROM profiles WHERE user_id = :u", u=user_id) or {}
        routine_versions = [r["vid"] for r in db.rows(conn, """SELECT DISTINCT pv.id AS vid FROM routines r
                              JOIN routine_items ri ON ri.routine_id = r.id
                              JOIN product_versions pv ON pv.product_id = ri.product_id AND pv.is_current
                              WHERE r.user_id = :u AND r.is_active""", u=user_id)]
    avoided_brands = {b.lower() for b in prefs.get("avoided_brands", [])}
    out, used = [], set()
    kv = None
    for rec in result.recommendations:
        rows = db.rows(conn, """
            SELECT p.id, p.slug, p.name, b.name AS brand, p.image_url, p.category, pv.id AS vid, pv.completeness,
                   array_agg(DISTINCT i.inci_name) AS matching
            FROM products p JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
            JOIN product_ingredients pi ON pi.product_version_id = pv.id
            JOIN ingredients i ON i.id = pi.ingredient_id
            LEFT JOIN brands b ON b.id = p.brand_id
            WHERE p.is_demo = :demo AND i.function_classes && CAST(:classes AS text[])
            GROUP BY p.id, b.name, pv.id ORDER BY count(DISTINCT i.id) DESC, pv.completeness DESC, p.name LIMIT 25""",
                       demo=demo, classes=list(rec.ingredient_classes))
        picked = 0
        for r in rows:
            if picked >= PER_CONCERN or str(r["id"]) in used or (r["brand"] or "").lower() in avoided_brands:
                continue
            conflict = None
            if routine_versions:
                if kv is None:
                    kv, _ = knowledge.load(conn, knowledge.active_version_id(conn, demo) or
                                           knowledge.active_version_id(conn, False))
                cf = catalog.formulation_for_version(conn, r["vid"])
                for v in routine_versions:
                    st = evaluate(cf, catalog.formulation_for_version(conn, v), kv).status
                    if st in (CompatibilityStatus.CAUTION, CompatibilityStatus.STRONG_CAUTION):
                        conflict = st.value
                        break
            if conflict:
                continue  # excluded: conflicts with the user's routine in the current knowledge base
            used.add(str(r["id"]))
            picked += 1
            out.append({
                "product_id": str(r["id"]), "slug": r["slug"], "name": r["name"], "brand": r["brand"],
                "image_url": r["image_url"], "category": r["category"],
                "observation": rec.observation, "concern_category": rec.concern_category,
                "observation_confidence": rec.observation_confidence,
                "evidence_strength": rec.evidence_strength.value,
                "product_data_confidence": float(r["completeness"]),
                "matching_ingredients": sorted(x for x in r["matching"] if x),
                "rationale": (f"Contains {', '.join(sorted(x for x in r['matching'] if x)[:3])} "
                              f"({', '.join(rec.ingredient_classes)}), mapped to '{rec.concern_category}'."),
                "routine_checked": bool(routine_versions),
            })
    return out
