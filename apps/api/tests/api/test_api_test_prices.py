"""Synthetic TEST prices (dev/test only): labelled, deterministic, removable, hidden outside dev/test."""

import pytest

from skinsync import cli, db
from skinsync.config import get_settings
from skinsync.services import catalog
from tests.api.conftest import demo_id

V = "/api/v1"


def _ref(client, name):
    r = client.get(f"{V}/products", params={"q": name})
    return next(i for i in r.json()["items"] if i["name"] == name)


def test_seed_label_remove_and_hide_in_prod(client, monkeypatch):
    try:
        n = cli.seed_test_prices()
        assert n >= 4  # the non-demo test products have no prices
        assert cli.seed_test_prices() == 0  # idempotent: only unpriced products
        item = _ref(client, "Test Plain Lotion")
        p = item["price"]
        assert p["is_test"] is True and p["source"] == "synthetic-test" and p["currency"] == "INR"
        assert "TEST PRICE" in p["label"] and "not real" in p["label"]
        assert 149 <= p["amount"] <= 1949
        detail = client.get(f"{V}/products/{item['slug']}").json()
        assert detail["prices"][0]["is_test"] is True and detail["prices"][0]["seller"] == catalog.TEST_PRICE_SELLER
        # demo products keep their own (fictional, demo-labelled) prices; no test price is added to them
        with db.transaction() as conn:
            assert db.scalar(conn, """SELECT count(*) FROM price_observations po JOIN products p ON p.id = po.product_id
                                      WHERE p.is_demo AND po.source = 'synthetic-test'""") == 0
        assert demo_id(client, "DEMO Hydra Gel Cream")
        # staging/prod: test prices are never shown even if present in the database
        monkeypatch.setattr(get_settings(), "env", "staging")
        assert _ref(client, "Test Plain Lotion")["price"]["state"] == "unavailable"
        assert client.get(f"{V}/products/{item['slug']}").json()["prices"][0]["state"] == "unavailable"
        with pytest.raises(SystemExit):
            cli.seed_test_prices()
        monkeypatch.setattr(get_settings(), "env", "test")
    finally:
        removed = cli.remove_test_prices()
    assert removed >= 4
    assert _ref(client, "Test Plain Lotion")["price"]["state"] == "unavailable"
