"""Names added to the ingredient master later are applied to already-imported products (re-resolve)."""

from datetime import date

from skinsync import db
from skinsync.security import get_redis
from skinsync.services import catalog


def test_reresolve_matches_new_names_and_clears_comparison_cache():
    with db.transaction() as conn:
        master = catalog.load_master(conn, max_age_s=0)
        catalog.upsert_product(conn, catalog.ProductRecord(
            source="test", source_ref="rr1", name="Test Later Name Serum", brand="Test Brand", category="serum",
            category_parent="face", raw_ingredients="DEMO BASE AQUA, Zetaflora Test Extract", observed_at=date(2026, 1, 1)),
            master, None)
        vid = db.scalar(conn, """SELECT pv.id FROM product_versions pv JOIN products p ON p.id = pv.product_id
                                 WHERE p.source_ref = 'rr1' AND pv.is_current""")
        assert db.scalar(conn, "SELECT count(*) FROM product_ingredients WHERE product_version_id = :v "
                               "AND ingredient_id IS NULL", v=vid) == 1
    get_redis().set(f"cmp:{vid}:x:kv:e", "stale")
    with db.transaction() as conn:
        catalog.upsert_ingredient(conn, "zetaflora-test-extract", "ZETAFLORA TEST EXTRACT", "test", [])
        catalog.invalidate_master()
        out = catalog.reresolve_unresolved(conn)
        assert out["updated"] >= 1 and out["newly_resolved"] >= 1
        row = db.row(conn, "SELECT completeness FROM product_versions WHERE id = :v", v=vid)
        assert float(row["completeness"]) == 1.0
        assert db.scalar(conn, "SELECT ingredient_id FROM product_ingredients WHERE product_version_id = :v "
                               "AND position = 2", v=vid) == "zetaflora-test-extract"
        again = catalog.reresolve_unresolved(conn)
    assert get_redis().get(f"cmp:{vid}:x:kv:e") is None  # stale cached comparison removed
    assert again["updated"] == 0  # idempotent
