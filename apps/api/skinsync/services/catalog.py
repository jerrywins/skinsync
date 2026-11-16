"""Catalogue service: ingredient master, product upserts, formulation resolution, search."""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.engine import Connection

from .. import db
from ..domain.compatibility import FormulationInput
from ..domain.ingredients import IngredientMaster, IngredientRecord, NormalizedIngredient, normalize_key, normalize_list
from ..errors import AppError, not_found

_SLUG = re.compile(r"[^a-z0-9]+")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def slugify(text: str, max_len: int = 80) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return _SLUG.sub("-", t).strip("-")[:max_len].strip("-") or "item"


# ---------------------------------------------------------------- ingredient master
_cache: dict = {"at": 0.0, "master": None}


def invalidate_master() -> None:
    _cache["at"] = 0.0


def load_master(conn: Connection, max_age_s: float = 60.0) -> IngredientMaster:
    if _cache["master"] is not None and time.time() - _cache["at"] < max_age_s:
        return _cache["master"]
    ings = db.rows(conn, "SELECT id, inci_name, function_classes, source FROM ingredients")
    aliases: dict[str, list[str]] = {}
    for a in db.rows(conn, "SELECT ingredient_id, alias FROM ingredient_aliases"):
        aliases.setdefault(a["ingredient_id"], []).append(a["alias"])
    recs = [IngredientRecord(id=i["id"], inci_name=i["inci_name"], function_classes=tuple(i["function_classes"] or ()),
                             aliases=tuple(sorted(aliases.get(i["id"], []))), source=i["source"]) for i in ings]
    master = _build_master_tolerant(recs)
    _cache.update(at=time.time(), master=master)
    return master


def _build_master_tolerant(recs: list[IngredientRecord]) -> IngredientMaster:
    """Like from_records, but an alias claimed by two ingredients is dropped (and flagged
    by the admin data-quality view) rather than crashing the whole service."""
    seen: dict[str, str] = {}
    clash: set[str] = set()
    for r in recs:
        for n in (r.inci_name, *r.aliases):
            k = normalize_key(n)
            if k in seen and seen[k] != r.id:
                clash.add(k)
            seen.setdefault(k, r.id)
    cleaned = []
    for r in recs:
        keep = tuple(a for a in r.aliases if normalize_key(a) not in clash)
        cleaned.append(r.model_copy(update={"aliases": keep}) if keep != r.aliases else r)
    m = IngredientMaster()
    for r in cleaned:
        m.records[r.id] = r
        for n in (r.inci_name, *r.aliases):
            k = normalize_key(n)
            if k not in clash:
                m._index.setdefault(k, r.id)
    return m


def upsert_ingredient(conn: Connection, ing_id: str, inci: str, source: str, aliases: list[str],
                      function_classes: list[str] | None = None, is_demo: bool = False, reviewed: bool = False) -> None:
    db.execute(conn, """INSERT INTO ingredients (id, inci_name, function_classes, source, is_demo, reviewed_at)
                        VALUES (:i, :n, :f, :s, :d, CASE WHEN :r THEN now() END)
                        ON CONFLICT (id) DO UPDATE SET function_classes = CASE
                          WHEN cardinality(EXCLUDED.function_classes) > 0 THEN EXCLUDED.function_classes
                          ELSE ingredients.function_classes END""",
               i=ing_id, n=inci, f=function_classes or [], s=source, d=is_demo, r=reviewed)
    for a in {inci, *aliases}:
        db.execute(conn, """INSERT INTO ingredient_aliases (alias_key, ingredient_id, alias) VALUES (:k, :i, :a)
                            ON CONFLICT (alias_key) DO NOTHING""", k=normalize_key(a), i=ing_id, a=a)


# ---------------------------------------------------------------- products
@dataclass
class ProductRecord:
    source: str
    source_ref: str
    name: str
    brand: str
    category: str
    category_parent: str | None
    raw_ingredients: str | None
    observed_at: date
    market: str | None = None
    image_url: str | None = None
    barcode: str | None = None
    is_demo: bool = False
    key_actives: frozenset[str] = frozenset()
    verification: str = "imported"


def ingredients_hash(raw: str | None) -> bytes:
    return hashlib.sha256(normalize_key(raw or "").encode()).digest()


def _brand_id(conn: Connection, brand: str) -> int | None:
    if not brand:
        return None
    slug = slugify(brand, 60)
    return db.scalar(conn, """INSERT INTO brands (name, slug) VALUES (:n, :s)
                              ON CONFLICT (slug) DO UPDATE SET name = brands.name RETURNING id""", n=brand, s=slug)


def upsert_product(conn: Connection, rec: ProductRecord, master: IngredientMaster, run_id: str | None) -> str:
    """Insert or update a product. Returns 'inserted' | 'updated' | 'unchanged'."""
    existing = db.row(conn, "SELECT id FROM products WHERE source = :s AND source_ref = :r",
                      s=rec.source, r=rec.source_ref)
    bid = _brand_id(conn, rec.brand)
    if existing is None:
        base = slugify(f"{rec.brand} {rec.name}")
        slug = base
        if db.scalar(conn, "SELECT 1 FROM products WHERE slug = :s", s=slug):
            slug = f"{base}-{slugify(rec.source_ref, 20)}"
        pid = db.scalar(conn, """INSERT INTO products (slug, name, brand_id, category, category_parent, market, image_url,
                                   is_demo, source, source_ref, import_run_id, retrieved_at)
                                 VALUES (:slug, :n, :b, :c, :cp, :m, :img, :demo, :s, :r, :run, now()) RETURNING id""",
                         slug=slug, n=rec.name, b=bid, c=rec.category, cp=rec.category_parent, m=rec.market,
                         img=rec.image_url, demo=rec.is_demo, s=rec.source, r=rec.source_ref, run=run_id)
        status = "inserted"
    else:
        pid = existing["id"]
        db.execute(conn, """UPDATE products SET name=:n, brand_id=:b, category=:c, category_parent=:cp, market=:m,
                              image_url=:img, import_run_id=:run, retrieved_at=now(), updated_at=now() WHERE id=:id""",
                   n=rec.name, b=bid, c=rec.category, cp=rec.category_parent, m=rec.market, img=rec.image_url,
                   run=run_id, id=pid)
        status = "unchanged"
    if rec.barcode:
        kind = "ean13" if len(rec.barcode) == 13 else "upc" if len(rec.barcode) == 12 else \
            "ean8" if len(rec.barcode) == 8 else "other"
        db.execute(conn, """INSERT INTO product_identifiers (product_id, kind, value) VALUES (:p, :k, :v)
                            ON CONFLICT (kind, value) DO NOTHING""", p=pid, k=kind, v=rec.barcode)

    h = ingredients_hash(rec.raw_ingredients)
    if db.scalar(conn, "SELECT 1 FROM product_versions WHERE product_id = :p AND ingredients_hash = :h", p=pid, h=h):
        return status
    n_versions = db.scalar(conn, "SELECT count(*) FROM product_versions WHERE product_id = :p", p=pid)
    db.execute(conn, "UPDATE product_versions SET is_current = false WHERE product_id = :p AND is_current", p=pid)
    normalized = normalize_list(rec.raw_ingredients or "", master, rec.key_actives)
    completeness = (sum(1 for i in normalized if i.resolved) / len(normalized)) if normalized else 0.0
    vid = db.scalar(conn, """INSERT INTO product_versions (product_id, version_label, raw_ingredients, ingredients_hash,
                               observed_at, market, completeness, verification, source, source_ref, is_current)
                             VALUES (:p, :l, :raw, :h, :o, :m, :c, :v, :s, :r, true) RETURNING id""",
                     p=pid, l=f"v{n_versions + 1} ({rec.observed_at.isoformat()})",
                     raw=rec.raw_ingredients if (rec.raw_ingredients or "").strip() else None, h=h,
                     o=rec.observed_at, m=rec.market, c=round(completeness, 4), v=rec.verification,
                     s=rec.source, r=rec.source_ref)
    save_normalized(conn, vid, normalized)
    unresolved = [i.raw for i in normalized if not i.resolved]
    if not normalized:
        _flag(conn, "product_version", str(vid), "missing_ingredient_list", rec.source, {})
    elif unresolved:
        _flag(conn, "product_version", str(vid), "unknown_ingredient", rec.source,
              {"count": len(unresolved), "examples": unresolved[:10]})
    fuzzy = [i.raw for i in normalized if i.method.value == "fuzzy"]
    if fuzzy:
        _flag(conn, "product_version", str(vid), "fuzzy_match", "normalizer", {"examples": fuzzy[:10]})
    return "updated" if status == "unchanged" else status


def save_normalized(conn: Connection, vid, items: list[NormalizedIngredient]) -> None:
    db.execute(conn, "DELETE FROM product_ingredients WHERE product_version_id = :v", v=vid)
    for i in items:
        db.execute(conn, """INSERT INTO product_ingredients (product_version_id, position, raw_name, ingredient_id,
                              method, confidence, review_status, stated_role, concentration_pct, is_key_active)
                            VALUES (:v, :p, :raw, :iid, :m, :c, :rs, :sr, :pct, :k)""",
                   v=vid, p=i.position, raw=i.raw[:500], iid=i.canonical_id, m=i.method.value, c=i.confidence,
                   rs=i.review_status.value, sr=i.stated_role, pct=i.concentration_pct, k=i.is_key_active)


def _flag(conn, target_type, target_ref, reason, source, details):
    import json

    db.execute(conn, """INSERT INTO data_quality_flags (target_type, target_ref, reason, source, details)
                        VALUES (:t, :r, :re, :s, CAST(:d AS jsonb))""",
               t=target_type, r=target_ref, re=reason, s=source, d=json.dumps(details))


def raise_flag(conn, target_type, target_ref, reason, source, details=None, user_id=None) -> int:
    import json

    return db.scalar(conn, """INSERT INTO data_quality_flags (target_type, target_ref, reason, source, details, raised_by)
                              VALUES (:t, :r, :re, :s, CAST(:d AS jsonb), :u) RETURNING id""",
                     t=target_type, r=target_ref, re=reason, s=source, d=json.dumps(details or {}), u=user_id)


# ---------------------------------------------------------------- reads
PRODUCT_COLS = """p.id, p.slug, p.name, p.category, p.category_parent, p.market, p.image_url, p.is_demo,
                  p.source, p.source_ref, p.retrieved_at, b.name AS brand, b.slug AS brand_slug"""


def find_product(conn: Connection, ref) -> dict:
    ref = str(ref)
    if _UUID.match(ref):
        p = db.row(conn, f"SELECT {PRODUCT_COLS} FROM products p LEFT JOIN brands b ON b.id = p.brand_id WHERE p.id = :r",
                   r=ref)
    else:
        p = db.row(conn, f"SELECT {PRODUCT_COLS} FROM products p LEFT JOIN brands b ON b.id = p.brand_id WHERE p.slug = :r",
                   r=ref)
    if not p:
        raise not_found("Product")
    return p


def current_version(conn: Connection, product_id) -> dict | None:
    return db.row(conn, "SELECT * FROM product_versions WHERE product_id = :p AND is_current", p=product_id)


def version_ingredients(conn: Connection, vid) -> list[dict]:
    return db.rows(conn, """SELECT pi.*, i.inci_name, i.function_classes, i.reviewed_at IS NOT NULL AS ingredient_reviewed
                            FROM product_ingredients pi LEFT JOIN ingredients i ON i.id = pi.ingredient_id
                            WHERE pi.product_version_id = :v ORDER BY pi.position""", v=vid)


def formulation_for_version(conn: Connection, vid) -> FormulationInput:
    v = db.row(conn, """SELECT pv.*, p.name AS product_name FROM product_versions pv
                        JOIN products p ON p.id = pv.product_id WHERE pv.id = :v""", v=vid)
    if not v:
        raise not_found("Product version")
    ings = []
    for r in version_ingredients(conn, vid):
        resolved = r["ingredient_id"] is not None
        ings.append(NormalizedIngredient(
            position=r["position"], raw=r["raw_name"], canonical_id=r["ingredient_id"],
            inci_name=r["inci_name"] if resolved else None,
            function_classes=tuple(r["function_classes"] or ()) if resolved else (),
            method=r["method"] if r["method"] != "manual" else "exact", confidence=float(r["confidence"]),
            review_status=r["review_status"], stated_role=r["stated_role"],
            concentration_pct=float(r["concentration_pct"]) if r["concentration_pct"] is not None else None,
            is_key_active=r["is_key_active"],
        ))
    return FormulationInput(product_id=str(v["product_id"]), product_version_id=str(v["id"]),
                            product_name=v["product_name"], version_label=v["version_label"],
                            ingredients=tuple(ings), has_ingredient_list=v["raw_ingredients"] is not None)


def manual_formulation(conn: Connection, text: str, label: str = "Manual entry") -> FormulationInput:
    if not text or not text.strip():
        raise AppError(422, "EMPTY_INGREDIENTS", "Enter at least one ingredient.")
    master = load_master(conn)
    ings = normalize_list(text, master)
    digest = hashlib.sha256(normalize_key(text).encode()).hexdigest()[:16]
    return FormulationInput(product_id=f"manual:{digest}", product_version_id=f"manual:{digest}",
                            product_name=label, version_label="entered by user", ingredients=tuple(ings),
                            has_ingredient_list=True)


TEST_PRICE_SOURCE = "synthetic-test"
TEST_PRICE_SELLER = "TEST PRICE — not real"


def test_prices_allowed() -> bool:
    """Synthetic test prices are only ever shown in dev/test; staging and prod hide them even if present."""
    from ..config import get_settings

    return get_settings().env in ("dev", "test")


def latest_prices(conn: Connection, product_ids: list) -> dict:
    if not product_ids:
        return {}
    out = {}
    for r in db.rows(conn, """SELECT DISTINCT ON (product_id) product_id, amount, currency, seller, source, available,
                                observed_at FROM price_observations WHERE product_id = ANY(:ids)
                                AND (:allow_test OR source <> :test_src)
                              ORDER BY product_id, observed_at DESC""", ids=list(product_ids),
                     allow_test=test_prices_allowed(), test_src=TEST_PRICE_SOURCE):
        out[str(r["product_id"])] = r
    return out


def search(conn: Connection, q: str | None, brand: str | None, category: str | None, ingredient: str | None,
           limit: int, offset: int, include_demo: bool) -> tuple[list[dict], int]:
    where, params, order = ["(:demo OR NOT p.is_demo)"], {"demo": include_demo}, "p.name"
    if brand:
        where.append("b.slug = :brand")
        params["brand"] = brand
    if category:
        where.append("p.category = :cat")
        params["cat"] = category
    if ingredient:
        where.append("""EXISTS (SELECT 1 FROM product_versions pv JOIN product_ingredients pi
                          ON pi.product_version_id = pv.id WHERE pv.product_id = p.id AND pv.is_current
                          AND pi.ingredient_id = :ing)""")
        params["ing"] = ingredient
    if q:
        params["q"] = q.strip()[:120].lower()
        where.append("""(f_unaccent(lower(p.name)) % f_unaccent(:q)
                         OR f_unaccent(lower(p.name)) LIKE '%' || f_unaccent(:q) || '%'
                         OR lower(b.name) LIKE '%' || :q || '%'
                         OR f_unaccent(lower(coalesce(b.name,'') || ' ' || p.name)) % f_unaccent(:q))""")
        # exact > brand+name > text similarity, then data completeness (SkinIQ §24)
        order = """(lower(p.name) = :q) DESC,
                   (lower(coalesce(b.name,'') || ' ' || p.name) = :q) DESC,
                   greatest(similarity(f_unaccent(lower(p.name)), f_unaccent(:q)),
                            similarity(f_unaccent(lower(coalesce(b.name,'') || ' ' || p.name)), f_unaccent(:q))) DESC,
                   coalesce(pv.completeness, 0) DESC, p.name"""
    sql_where = " AND ".join(where)
    total = db.scalar(conn, f"""SELECT count(*) FROM products p LEFT JOIN brands b ON b.id = p.brand_id
                                WHERE {sql_where}""", **params)
    items = db.rows(conn, f"""SELECT {PRODUCT_COLS}, pv.id AS version_id, pv.completeness, pv.version_label,
                                pv.raw_ingredients IS NOT NULL AS has_ingredients
                              FROM products p LEFT JOIN brands b ON b.id = p.brand_id
                              LEFT JOIN product_versions pv ON pv.product_id = p.id AND pv.is_current
                              WHERE {sql_where} ORDER BY {order} LIMIT :lim OFFSET :off""",
                    **params, lim=limit, off=offset)
    return items, total


def import_ingredient_file(conn: Connection, path) -> dict:
    """Load knowledge/ingredients.yaml. Names and aliases (nomenclature) are always loaded so labels are
    recognised; function classes are applied only for entries marked `review_status: reviewed`."""
    import yaml

    from ..domain.ingredients import IngredientRecord

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if data.get("fixture"):
        raise AppError(422, "KNOWLEDGE_INVALID", "fixture ingredient files cannot be imported as real data")
    counts = {"loaded": 0, "classes_applied": 0, "classes_pending_review": 0}
    for e in data.get("ingredients") or []:
        status = e.get("review_status", "draft")
        rec = IngredientRecord(id=e["id"], inci_name=e["inci_name"], aliases=tuple(e.get("aliases") or ()),
                               function_classes=tuple(e.get("function_classes") or ()), source="team-file")
        reviewed = status == "reviewed"
        upsert_ingredient(conn, rec.id, rec.inci_name, "team-file" if reviewed else "team-file-draft",
                          list(rec.aliases), list(rec.function_classes) if reviewed else [], reviewed=reviewed)
        counts["loaded"] += 1
        counts["classes_applied" if reviewed else "classes_pending_review"] += 1 if rec.function_classes else 0
    invalidate_master()
    return counts
