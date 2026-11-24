"""Operational commands.

  python -m skinsync.cli bootstrap                     publish the empty bootstrap knowledge version
  python -m skinsync.cli create-admin EMAIL            create an admin (password from SKINSYNC_ADMIN_PASSWORD)
  python -m skinsync.cli create-user EMAIL             dev/test only: verified user (SKINSYNC_USER_PASSWORD)
  python -m skinsync.cli seed-demo                     load the FICTIONAL demo dataset (requires demo mode)
  python -m skinsync.cli import-csv FILE               import team-curated products (docs/DATA_FORMATS.md)
  python -m skinsync.cli import-prices FILE            import price observations (CSV)
  python -m skinsync.cli seed-test-prices              dev/test only: RANDOM labelled prices for unpriced products
  python -m skinsync.cli remove-test-prices            delete every synthetic test price
  python -m skinsync.cli reresolve                     re-match products' unrecognised ingredients to the master
  python -m skinsync.cli retention                     run the retention cleanup now
"""

from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

from . import db
from .config import get_settings
from .security import hash_password, validate_password
from .services import catalog, knowledge


def demo_dir() -> Path:
    """Same knowledge root as everything else (SKINSYNC_KNOWLEDGE_DIR). Never index parents of __file__: the
    package sits only two levels deep in the container (/app/skinsync), so that raised IndexError there."""
    return Path(get_settings().knowledge_dir) / "demo"
DEMO_KV = "demo-kv-1"


def bootstrap() -> None:
    with db.transaction() as conn:
        knowledge.ensure_bootstrap(conn)
        path = Path(get_settings().knowledge_dir) / "ingredients.yaml"
        if path.exists():
            print(f"ingredient file: {catalog.import_ingredient_file(conn, path)}")
            print(f"re-resolve: {catalog.reresolve_unresolved(conn)}")
    print("bootstrap knowledge version ready")


def create_admin(email: str) -> None:
    pw = os.environ.get("SKINSYNC_ADMIN_PASSWORD") or getpass.getpass("Admin password: ")
    validate_password(pw, email)
    with db.transaction() as conn:
        if db.scalar(conn, "SELECT 1 FROM users WHERE email_lower = lower(:e)", e=email):
            db.execute(conn, "UPDATE users SET role = 'admin' WHERE email_lower = lower(:e)", e=email)
            print("existing user promoted to admin")
            return
        uid = db.scalar(conn, """INSERT INTO users (email, password_hash, role, email_verified_at, age_confirmed_18)
                                 VALUES (:e, :h, 'admin', now(), true) RETURNING id""", e=email, h=hash_password(pw))
        db.execute(conn, "INSERT INTO profiles (user_id) VALUES (:u)", u=uid)
        db.execute(conn, """INSERT INTO consents (user_id, purpose, policy_version, granted)
                            VALUES (:u, 'terms', :v, true)""", u=uid, v=get_settings().policy_version)
    print(f"admin created: {email}")


def create_user(email: str) -> None:
    """Dev/test only: a verified registered user (for E2E tests). Refused outside dev/test."""
    if get_settings().env not in ("dev", "test"):
        sys.exit("refusing: create-user is for dev/test environments only")
    pw = os.environ.get("SKINSYNC_USER_PASSWORD") or getpass.getpass("Password: ")
    validate_password(pw, email)
    with db.transaction() as conn:
        if db.scalar(conn, "SELECT 1 FROM users WHERE email_lower = lower(:e)", e=email):
            print("user exists")
            return
        uid = db.scalar(conn, """INSERT INTO users (email, password_hash, email_verified_at, age_confirmed_18)
                                 VALUES (:e, :h, now(), true) RETURNING id""", e=email, h=hash_password(pw))
        db.execute(conn, "INSERT INTO profiles (user_id) VALUES (:u)", u=uid)
    print(f"user created: {email}")


def seed_demo() -> None:
    if not get_settings().demo_mode:
        sys.exit("refusing: set SKINSYNC_DEMO_MODE=true to load the fictional demo dataset")
    ddir = demo_dir()
    ing = yaml.safe_load((ddir / "ingredients.yaml").read_text())
    prods = yaml.safe_load((ddir / "products.yaml").read_text())
    if not (ing.get("fixture") and prods.get("fixture")):
        sys.exit("demo files must be marked fixture: true")
    with db.transaction() as conn:
        knowledge.ensure_bootstrap(conn)
        for i in ing["ingredients"]:
            catalog.upsert_ingredient(conn, i["id"], i["inci_name"], "demo-fictional", [], i["function_classes"],
                                      is_demo=True)
        catalog.invalidate_master()
        if not db.scalar(conn, "SELECT 1 FROM knowledge_versions WHERE id = :i", i=DEMO_KV):
            knowledge.import_directory(conn, ddir, DEMO_KV, actor=None, allow_fixture=True)
            knowledge.set_status(conn, DEMO_KV, "in_review", None)
            knowledge.set_status(conn, DEMO_KV, "published", None)
    with db.transaction() as conn:
        master = catalog.load_master(conn, max_age_s=0)
        run = db.scalar(conn, "INSERT INTO import_runs (source, licence) VALUES ('demo', 'fictional demo data') RETURNING id")
        for p in prods["products"]:
            rec = catalog.ProductRecord(source="demo", source_ref=p["ref"], name=p["name"], brand=p["brand"],
                                        category=p["category"], category_parent="face", raw_ingredients=p["ingredients"],
                                        observed_at=date.today(), market="IN", is_demo=True,
                                        key_actives=frozenset(p["key_actives"]), verification="unverified")
            catalog.upsert_product(conn, rec, master, str(run))
            pid = db.scalar(conn, "SELECT id FROM products WHERE source='demo' AND source_ref=:r", r=p["ref"])
            if p.get("price") and not db.scalar(conn, "SELECT 1 FROM price_observations WHERE product_id = :p", p=pid):
                db.execute(conn, """INSERT INTO price_observations (product_id, amount, currency, seller, country, source,
                                      observed_at) VALUES (:p, :a, 'INR', 'DEMO seller (fictional)', 'IN',
                                      'DEMO price (fictional)', now() - interval '2 days')""", p=pid, a=p["price"])
    print(f"demo dataset loaded ({len(prods['products'])} fictional products, knowledge {DEMO_KV})")


def import_csv(path: Path) -> None:
    """Team-curated products. Columns: source_ref,brand,name,category,category_parent,barcode,market,
    observed_at(YYYY-MM-DD),ingredients,key_actives(;-separated canonical ids),source_name."""
    counts: dict[str, int] = {}
    with db.transaction() as conn:
        run = db.scalar(conn, "INSERT INTO import_runs (source, licence) VALUES ('team_csv', 'team-owned') RETURNING id")
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            try:
                with db.transaction() as conn:
                    master = catalog.load_master(conn)
                    rec = catalog.ProductRecord(
                        source=f"team:{row['source_name'].strip()}", source_ref=row["source_ref"].strip(),
                        name=row["name"].strip(), brand=row["brand"].strip(), category=row["category"].strip(),
                        category_parent=row.get("category_parent") or None,
                        raw_ingredients=row.get("ingredients") or None,
                        observed_at=date.fromisoformat(row["observed_at"]), market=row.get("market") or None,
                        barcode=(row.get("barcode") or "").strip() or None,
                        key_actives=frozenset(k for k in (row.get("key_actives") or "").split(";") if k),
                        verification="verified")
                    st = catalog.upsert_product(conn, rec, master, str(run))
                counts[st] = counts.get(st, 0) + 1
            except Exception as e:  # report and continue
                counts["failed"] = counts.get("failed", 0) + 1
                print(f"row {i + 2}: {type(e).__name__}: {e}", file=sys.stderr)
    print(json.dumps(counts))


def import_prices(path: Path) -> None:
    """Columns: product_ref(slug|uuid|barcode),amount,currency,seller,country,source,observed_at(ISO),available."""
    n = 0
    with db.transaction() as conn, path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ref = row["product_ref"].strip()
            pid = db.scalar(conn, "SELECT product_id FROM product_identifiers WHERE value = :v", v=ref)
            pid = pid or catalog.find_product(conn, ref)["id"]
            db.execute(conn, """INSERT INTO price_observations (product_id, amount, currency, seller, country, source,
                                  available, observed_at) VALUES (:p, :a, :c, :s, :co, :src, :av, :o)""",
                       p=pid, a=float(row["amount"]), c=row["currency"].strip().upper(), s=row["seller"].strip(),
                       co=row.get("country") or None, src=row["source"].strip(),
                       av=(row.get("available", "true").lower() != "false"),
                       o=datetime.fromisoformat(row["observed_at"]).astimezone(UTC))
            n += 1
    print(f"{n} price observations imported")


def seed_test_prices(seed: int = 20261105) -> int:
    """Dev/test only. Gives every non-demo product with no price ONE random INR price, clearly labelled
    (source synthetic-test, seller "TEST PRICE — not real"). These are NOT real prices; they exist only so the
    cheaper/premium flows can be exercised. Deterministic per product. Refused outside dev/test."""
    import hashlib

    if get_settings().env not in ("dev", "test"):
        sys.exit("refusing: test prices are for dev/test environments only")
    n = 0
    with db.transaction() as conn:
        ids = db.rows(conn, """SELECT p.id FROM products p WHERE NOT p.is_demo
                               AND NOT EXISTS (SELECT 1 FROM price_observations po WHERE po.product_id = p.id)""")
        for r in ids:
            h = int(hashlib.sha256(f"{seed}:{r['id']}".encode()).hexdigest()[:8], 16)
            amount = 149 + (h % 37) * 50  # 149 .. 1949 INR in steps of 50
            db.execute(conn, """INSERT INTO price_observations (product_id, amount, currency, seller, country, source,
                                  available, observed_at) VALUES (:p, :a, 'INR', :s, 'IN', :src, true, now())""",
                       p=r["id"], a=amount, s=catalog.TEST_PRICE_SELLER, src=catalog.TEST_PRICE_SOURCE)
            n += 1
    print(f"{n} TEST prices added (random, not real; remove with remove-test-prices)")
    return n


def remove_test_prices() -> int:
    with db.transaction() as conn:
        n = db.scalar(conn, """WITH d AS (DELETE FROM price_observations WHERE source = :s RETURNING 1)
                               SELECT count(*) FROM d""", s=catalog.TEST_PRICE_SOURCE)
    print(f"{n} test prices removed")
    return int(n)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bootstrap")
    a = sub.add_parser("create-admin")
    a.add_argument("email")
    sub.add_parser("seed-demo")
    u = sub.add_parser("create-user")
    u.add_argument("email")
    c = sub.add_parser("import-csv")
    c.add_argument("file", type=Path)
    p = sub.add_parser("import-prices")
    p.add_argument("file", type=Path)
    sub.add_parser("retention")
    sub.add_parser("reresolve")
    sub.add_parser("seed-test-prices")
    sub.add_parser("remove-test-prices")
    args = ap.parse_args(argv)
    if args.cmd == "bootstrap":
        bootstrap()
    elif args.cmd == "create-admin":
        create_admin(args.email)
    elif args.cmd == "create-user":
        create_user(args.email)
    elif args.cmd == "seed-test-prices":
        seed_test_prices()
    elif args.cmd == "remove-test-prices":
        remove_test_prices()
    elif args.cmd == "reresolve":
        with db.transaction() as conn:
            print(f"re-resolve: {catalog.reresolve_unresolved(conn)}")
    elif args.cmd == "seed-demo":
        seed_demo()
    elif args.cmd == "import-csv":
        import_csv(args.file)
    elif args.cmd == "import-prices":
        import_prices(args.file)
    elif args.cmd == "retention":
        from .jobs import retention_cleanup

        print(f"{retention_cleanup()} expired uploads removed")


if __name__ == "__main__":
    main()
