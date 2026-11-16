"""Integration: health, catalogue, comparison, alternatives (FR-01..05, FR-13..16, NFR-03, NFR-10)."""

from tests.api.conftest import demo_id

V = "/api/v1"


def test_health_ready_and_request_ids(client):
    r = client.get(f"{V}/health")
    assert r.status_code == 200 and r.headers["X-Request-ID"]
    ready = client.get(f"{V}/ready").json()
    assert ready["checks"]["database"] == "ok" and ready["checks"]["redis"] == "ok"
    assert ready["status"] in ("ok", "degraded")  # no worker process in tests -> degraded, never down
    assert client.get(f"{V}/metrics").status_code == 200


def test_error_envelope_and_unknown_route(client):
    r = client.get(f"{V}/products/does-not-exist")
    body = r.json()
    assert r.status_code == 404 and set(body) == {"code", "message", "details", "request_id"}
    assert body["code"] == "NOT_FOUND"


def test_fr01_search_typo_tolerant_and_filters(client):
    r = client.get(f"{V}/products", params={"q": "DEMO Renewl Nigt Serum"})
    assert r.status_code == 200 and r.json()["items"][0]["name"] == "DEMO Renewal Night Serum"
    r = client.get(f"{V}/products", params={"category": "moisturizer", "limit": 50})
    assert all(i["category"] == "moisturizer" for i in r.json()["items"])
    r = client.get(f"{V}/products", params={"ingredient": "demo-retinal-x"})
    assert [i["name"] for i in r.json()["items"]] == ["DEMO Renewal Night Serum"]
    assert client.get(f"{V}/products", params={"q": "zzzzqqq-nothing"}).json()["total"] == 0


def test_validation_rejects_unknown_fields(client):
    r = client.post(f"{V}/comparisons", json={"a": {"product_id": "x"}, "b": {"product_id": "y"}, "evil": 1})
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"


def test_product_detail_has_provenance_versions_and_unresolved(client):
    pid = demo_id(client, "DEMO Mystery Botanical Oil")
    d = client.get(f"{V}/products/{pid}").json()
    assert d["is_demo"] and d["provenance"]["source"] == "demo"
    assert d["unresolved_count"] == 1 and d["current_version"]["completeness"] == 0.5
    assert d["prices"][0]["state"] == "unavailable" and d["prices"][0]["label"] == "Price unavailable"
    assert d["indexable"] is False  # demo pages are never indexed


def test_barcode_lookup(client):
    assert client.get(f"{V}/products/barcode/4000000000001").json()["status"] == "found"
    assert client.get(f"{V}/products/barcode/9999999999999").json()["status"] == "not_found"
    assert client.get(f"{V}/products/barcode/abc").status_code == 422


def test_ingredient_detail_and_normalize(client):
    d = client.get(f"{V}/ingredients/demo-retinal-x").json()
    assert d["product_count"] >= 1 and d["evidence"]  # cited by demo rules
    n = client.post(f"{V}/ingredients/normalize", json={"text": "DEMO RETINAL-X, Unknown Thing"}).json()
    assert n["resolved"] == 1 and n["total"] == 2


def test_sc01_demo_comparison_caution_with_evidence_and_why(client):
    a, b = demo_id(client, "DEMO Renewal Night Serum"), demo_id(client, "DEMO Smooth Acid Toner")
    r = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}})
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    assert res["status"] == "caution" and res["knowledge_is_demo"] and res["knowledge_version"] == "demo-kv-1"
    rule = [f for f in res["findings"] if f["type"] == "rule"][0]
    assert rule["rule_code"] == "DEMO-R1" and rule["evidence"] and len(rule["why"]) == 5
    assert "confidence" in rule and "evidence_strength" in rule
    assert r.json()["claim_token"]  # guest can keep it by signing up


def test_strong_caution_and_reproducible_by_id(client):
    a, b = demo_id(client, "DEMO Clear Spot Gel"), demo_id(client, "DEMO Renewal Night Serum")
    r = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()
    assert r["result"]["status"] == "strong_caution"
    again = client.get(f"{V}/comparisons/{r['id']}").json()
    assert again["result"] == r["result"] and again["outdated"] == []


def test_determinism_and_cache_hit(client):
    from skinsync.observability import CACHE

    a, b = demo_id(client, "DEMO Bright C Serum"), demo_id(client, "DEMO Hydra Gel Cream")
    body = {"a": {"product_id": a}, "b": {"product_id": b}}
    r1 = client.post(f"{V}/comparisons", json=body).json()["result"]
    hits = CACHE.labels("comparison", "hit")._value.get()
    r2 = client.post(f"{V}/comparisons", json=body).json()["result"]
    assert r1 == r2 and CACHE.labels("comparison", "hit")._value.get() == hits + 1


def test_real_products_with_no_reviewed_rules_return_insufficient_evidence(client):
    a, b = demo_id(client, "Test Plain Lotion"), demo_id(client, "Test Plain Cream")
    res = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()["result"]
    assert res["status"] == "insufficient_evidence" and res["knowledge_version"] == "kv-0-empty"
    assert not res["knowledge_is_demo"]


def test_c04_c05_unknown_or_missing_ingredients_never_clear(client):
    a, b, c = (demo_id(client, n) for n in ("Test Unknown Mix", "Test Plain Cream", "Test No List"))
    r1 = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()["result"]
    assert r1["status"] == "data_incomplete" and r1["ingredients"]["unresolved_a"] == ["Totally Unknown Extract"]
    r2 = client.post(f"{V}/comparisons", json={"a": {"product_id": c}, "b": {"product_id": b}}).json()["result"]
    assert r2["status"] == "data_incomplete" and r2["completeness"] == 0.0


def test_demo_and_real_products_cannot_be_mixed(client):
    a, b = demo_id(client, "DEMO Bright C Serum"), demo_id(client, "Test Plain Cream")
    r = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}})
    assert r.status_code == 422 and r.json()["code"] == "DEMO_MIX"


def test_manual_ingredient_entry_is_compared_but_not_persisted(client):
    b = demo_id(client, "Test Plain Cream")
    r = client.post(f"{V}/comparisons", json={"a": {"manual_ingredients": "DEMO BASE AQUA, DEMO GLYCEROL-G"},
                                              "b": {"product_id": b}}).json()
    assert r["id"] is None and r["saveable"] is False
    assert r["result"]["status"] == "insufficient_evidence"


def test_nfr03_redis_outage_does_not_break_search_or_compare(client, monkeypatch):
    from skinsync import security

    class Down:
        def __getattr__(self, _):
            raise ConnectionError("redis down")

    monkeypatch.setattr(security, "_redis", Down())
    assert client.get(f"{V}/products", params={"q": "DEMO"}).status_code == 200
    a, b = demo_id(client, "DEMO Bright C Serum"), demo_id(client, "DEMO Hydra Gel Cream")
    assert client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).status_code == 200


def test_nfr03_queue_outage_only_affects_async_features(client, monkeypatch):
    from skinsync import jobs
    from tests.api.conftest import face_like_jpeg

    monkeypatch.delenv("SKINSYNC_QUEUE_SYNC")
    monkeypatch.setattr("rq.Queue.enqueue", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("down")))
    r = client.post(f"{V}/skin-analyses", files={"image": ("f.jpg", face_like_jpeg(), "image/jpeg")},
                    data={"skin_type": "oily", "consent": "true"})
    assert r.status_code == 503 and r.json()["code"] == "ANALYSIS_UNAVAILABLE"
    a, b = demo_id(client, "DEMO Bright C Serum"), demo_id(client, "DEMO Hydra Gel Cream")
    assert client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).status_code == 200
    assert jobs  # imported for monkeypatch target resolution


def test_fr15_cheaper_alternatives_with_prices_and_reasons(client):
    ref = demo_id(client, "DEMO Balance Niacin Serum")
    r = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "cheaper"})
    assert r.status_code == 200, r.text
    res = r.json()
    names = [x["name"] for x in res["results"]]
    assert "DEMO Budget Balance Serum" in names and "DEMO Luxe Balance Elixir" not in names
    top = res["results"][0]
    assert top["price_delta_pct"] < 0 and top["price"]["seller"].startswith("DEMO")
    assert top["reasons"] and top["dimensions"] and res["excluded"]


def test_fr15_premium_and_similar(client):
    ref = demo_id(client, "DEMO Balance Niacin Serum")
    prem = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "premium"}).json()
    assert [x["name"] for x in prem["results"]][0] == "DEMO Luxe Balance Elixir"
    sim = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "similar"}).json()
    assert sim["results"] and all(x["product_id"] != ref for x in sim["results"])
    again = client.get(f"{V}/alternatives/{sim['id']}").json()
    assert again["results"] == sim["results"]


def test_unavailable_price_never_invented(client):
    ref = demo_id(client, "DEMO Renewal Night Serum")
    res = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "similar"}).json()
    myst = [x for x in res["results"] if x["name"] == "DEMO Mystery Botanical Oil"]
    assert myst and myst[0]["price"] is None and myst[0]["price_state"] == "unavailable"


def test_alternatives_reference_without_ingredients_is_explained(client):
    ref = demo_id(client, "Test No List")
    r = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "similar"})
    assert r.status_code == 422 and r.json()["code"] == "REFERENCE_INCOMPLETE"


def test_routine_compatible_requires_sign_in(client):
    ref = demo_id(client, "DEMO Balance Niacin Serum")
    r = client.post(f"{V}/alternatives/search", json={"product_id": ref, "mode": "routine_compatible"})
    assert r.status_code == 401


def test_user_report_creates_flag(client, admin):
    pid = demo_id(client, "DEMO Hydra Gel Cream")
    r = client.post(f"{V}/reports", json={"target_type": "product", "target_ref": pid, "message": "Wrong ingredient list"})
    assert r.status_code == 201
    flags = admin.get(f"{V}/admin/flags", params={"reason": "user_report"}).json()["items"]
    assert any(f["target_ref"] == pid for f in flags)


def test_events_accept_only_allowlisted_names_without_pii(client):
    ok = client.post(f"{V}/events", json={"name": "comparison_started", "consent": True, "session_id": "abcd1234"})
    assert ok.status_code == 202
    bad = client.post(f"{V}/events", json={"name": "email_captured", "consent": True, "session_id": "abcd1234"})
    assert bad.status_code == 422
    no_consent = client.post(f"{V}/events", json={"name": "landing_view", "consent": False, "session_id": "abcd1234"})
    assert no_consent.status_code == 422


def test_heuristic_adapter_end_to_end_is_labelled_and_uses_real_knowledge(client, monkeypatch):
    """Experimental adapter: result is labelled 'not validated', is not demo, uses the real knowledge version."""
    from skinsync.config import get_settings
    from tests.api.conftest import face_like_jpeg

    monkeypatch.setattr(get_settings(), "skin_model_adapter", "heuristic")
    r = client.post(f"{V}/skin-analyses", files={"image": ("f.jpg", face_like_jpeg(), "image/jpeg")},
                    data={"skin_type": "oily", "consent": "true"})
    assert r.status_code == 202, r.text
    assert r.json()["quality"]["face_check"] in ("not_detected", "not_performed")  # advisory, not rejected
    a = client.get(f"{V}/skin-analyses/{r.json()['id']}", headers={"X-Poll-Token": r.json()["poll_token"]}).json()
    assert a["status"] == "completed", a
    assert a["model_version"] == "heuristic-0.1" and a["is_demo_model"] is False
    assert a["demo_label"] == "Experimental image measurements — not validated"
    assert a["result"]["knowledge_is_demo"] is False
    assert not any(p.get("is_demo") for p in a["result"]["products"])
