"""Open Beauty Facts importer (ODbL 1.0). Idempotent; provenance on every row.

Source: the official CSV export documented at https://world.openbeautyfacts.org/data
  https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv.gz  (tab-separated)
Fields used (verified against the export header on 2026-11-04): code, product_name, brands,
categories_tags, countries_tags, ingredients_text, last_modified_t, image_url.

Two passes:
 1. Count how often each cleaned ingredient string appears across distinct products and
    brands. Strings seen often enough become *observed, unreviewed* ingredient records
    (source "openbeautyfacts-observed"). Function classes stay empty: OBF does not give
    reviewed functions, and we do not guess them.
 2. Upsert products and formulation versions, normalising against the master.

Usage:
  python -m skinsync.ingest.obf --file obf.csv.gz [--limit 500] [--country en:india]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import logging
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

from .. import db
from ..domain.ingredients import parse_ingredient_list
from ..services import catalog

log = logging.getLogger("skinsync.ingest.obf")
SOURCE = "openbeautyfacts"
LICENCE = "ODbL-1.0 (database), DbCL-1.0 (contents), CC-BY-SA (images)"
CATEGORY_FILE = Path(__file__).parent / "obf_categories.yaml"


def load_category_map(path: Path = CATEGORY_FILE) -> tuple[set[str], list[dict]]:
    data = yaml.safe_load(path.read_text())
    return set(data["exclude"]), data["categories"]


def classify(tags: list[str], exclude: set[str], cats: list[dict]) -> dict | None:
    tagset = set(tags)
    if tagset & exclude:
        return None
    for c in cats:
        if tagset & set(c["tags"]):
            return c
    return None


def iter_rows(path: Path):
    csv.field_size_limit(sys.maxsize)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f, delimiter="\t")


def _first_brand(brands: str) -> str:
    return (brands or "").split(",")[0].strip()[:120]


def _observed(row: dict) -> date:
    try:
        return datetime.fromtimestamp(int(row.get("last_modified_t") or 0), UTC).date()
    except (ValueError, OverflowError):
        return date.today()


def select_rows(path: Path, country: str | None, limit: int | None):
    exclude, cats = load_category_map()
    out, read, skipped = [], 0, Counter()
    for row in iter_rows(path):
        read += 1
        code = (row.get("code") or "").strip()
        name = (row.get("product_name") or "").strip()
        if not code or not name:
            skipped["missing_code_or_name"] += 1
            continue
        tags = [t for t in (row.get("categories_tags") or "").split(",") if t]
        cat = classify(tags, exclude, cats)
        if cat is None:
            skipped["not_skincare"] += 1
            continue
        if country and country not in (row.get("countries_tags") or "").split(","):
            skipped["other_country"] += 1
            continue
        out.append((row, cat))
        if limit and len(out) >= limit:
            break
    return out, read, skipped


def seed_observed_ingredients(conn, selected, min_products: int, min_brands: int) -> int:
    products, brands, forms = Counter(), defaultdict(set), defaultdict(Counter)
    for row, _ in selected:
        seen = set()
        for e in parse_ingredient_list(row.get("ingredients_text") or ""):
            if len(e.cleaned) < 2 or len(e.cleaned) > 120 or e.cleaned in seen:
                continue
            seen.add(e.cleaned)
            products[e.cleaned] += 1
            brands[e.cleaned].add(_first_brand(row.get("brands")).lower())
            forms[e.cleaned][e.raw.strip()] += 1
    added = 0
    master = catalog.load_master(conn, max_age_s=0)
    for key, n in products.items():
        if n < min_products or len(brands[key]) < min_brands or master.lookup_exact(key):
            continue
        display = forms[key].most_common(1)[0][0].upper()[:300]
        ing_id = catalog.slugify(key, 110)
        if db.scalar(conn, "SELECT 1 FROM ingredients WHERE id = :i OR inci_name = :n", i=ing_id, n=display):
            continue
        catalog.upsert_ingredient(conn, ing_id, display, "openbeautyfacts-observed", [key])
        added += 1
    catalog.invalidate_master()
    return added


def run(path: Path, *, limit: int | None = None, country: str | None = None,
        min_products: int = 5, min_brands: int = 2) -> dict:
    selected, read, skipped = select_rows(path, country, limit)
    counts = Counter(read=read, selected=len(selected), **{f"skipped_{k}": v for k, v in skipped.items()})
    with db.transaction() as conn:
        run_id = db.scalar(conn, "INSERT INTO import_runs (source, licence) VALUES (:s, :l) RETURNING id",
                           s=SOURCE, l=LICENCE)
        counts["ingredients_added"] = seed_observed_ingredients(conn, selected, min_products, min_brands)
    master = None
    for i, (row, cat) in enumerate(selected):
        try:
            with db.transaction() as conn:
                if master is None or i % 500 == 0:
                    master = catalog.load_master(conn, max_age_s=0)
                countries = (row.get("countries_tags") or "").split(",")
                rec = catalog.ProductRecord(
                    source=SOURCE, source_ref=row["code"].strip(), name=row["product_name"].strip()[:300],
                    brand=_first_brand(row.get("brands")), category=cat["id"], category_parent=cat["parent"],
                    raw_ingredients=(row.get("ingredients_text") or "").strip() or None,
                    observed_at=_observed(row), market="IN" if "en:india" in countries else None,
                    image_url=(row.get("image_url") or None), barcode=row["code"].strip() if row["code"].strip().isdigit() else None,
                )
                counts[catalog.upsert_product(conn, rec, master, str(run_id))] += 1
        except Exception as exc:  # one bad row never aborts the run
            counts["failed"] += 1
            log.warning("row failed", extra={"route": row.get("code"), "status": type(exc).__name__})
    with db.transaction() as conn:
        db.execute(conn, "UPDATE import_runs SET finished_at = now(), counts = CAST(:c AS jsonb) WHERE id = :i",
                   c=json.dumps(dict(counts)), i=run_id)
    return dict(counts)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, type=Path)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--country", help="OBF country tag, e.g. en:india")
    ap.add_argument("--min-products", type=int, default=5)
    ap.add_argument("--min-brands", type=int, default=2)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.file, limit=a.limit, country=a.country, min_products=a.min_products,
                         min_brands=a.min_brands), indent=2))


if __name__ == "__main__":
    main()
