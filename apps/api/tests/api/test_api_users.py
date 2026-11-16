"""Integration: auth, CSRF, rate limits, shelf, routines, history, shares, IDOR, deletion (FR-17..20, NFR-02/08)."""

import uuid

from tests.api.conftest import Client, demo_id, face_like_jpeg, make_user

V = "/api/v1"


def test_signup_does_not_reveal_existing_accounts(client):
    email = f"dup-{uuid.uuid4().hex[:6]}@example.com"
    body = {"email": email, "password": "Correct-Horse-Battery-9", "age_confirmed_18": True, "accept_terms": True}
    r1, r2 = client.post(f"{V}/auth/signup", json=body), client.post(f"{V}/auth/signup", json=body)
    assert r1.status_code == r2.status_code == 202 and r1.json() == r2.json()


def test_signup_requires_age_and_strong_password(client):
    base = {"email": "x@example.com", "accept_terms": True}
    assert client.post(f"{V}/auth/signup", json={**base, "password": "Correct-Horse-9", "age_confirmed_18": False}
                       ).json()["code"] == "AGE_REQUIRED"
    assert client.post(f"{V}/auth/signup", json={**base, "password": "password123", "age_confirmed_18": True}
                       ).json()["code"] == "WEAK_PASSWORD"


def test_login_requires_verified_email_and_hides_which_part_failed(client):
    email = f"unv-{uuid.uuid4().hex[:6]}@example.com"
    client.post(f"{V}/auth/signup", json={"email": email, "password": "Correct-Horse-Battery-9",
                                         "age_confirmed_18": True, "accept_terms": True})
    assert client.post(f"{V}/auth/login", json={"email": email, "password": "Correct-Horse-Battery-9"}
                       ).json()["code"] == "EMAIL_NOT_VERIFIED"
    wrong_pw = client.post(f"{V}/auth/login", json={"email": email, "password": "nope-nope-nope"}).json()
    no_user = client.post(f"{V}/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"}).json()
    assert wrong_pw["code"] == no_user["code"] == "INVALID_CREDENTIALS" and wrong_pw["message"] == no_user["message"]


def test_session_cookies_are_httponly(user):
    jar = {c.name: c for c in user.c.cookies.jar}
    assert "ss_access" in jar and "ss_refresh" in jar
    assert jar["ss_access"].has_nonstandard_attr("HttpOnly") or "httponly" in str(jar["ss_access"]._rest).lower()


def test_csrf_required_on_state_changing_requests(user):
    r = user.c.post(f"{V}/shelf", json={"product_id": "x"})  # raw client: no X-CSRF-Token header
    assert r.status_code == 403 and r.json()["code"] == "CSRF_FAILED"


def test_refresh_rotation_and_reuse_detection(user):
    old = user.c.cookies.get("ss_refresh", path="/api/v1/auth")
    assert user.post(f"{V}/auth/refresh").status_code == 200
    thief = Client()
    thief.c.cookies.set("ss_refresh", old, path="/api/v1/auth")
    assert thief.post(f"{V}/auth/refresh").status_code == 401  # reused token
    assert user.post(f"{V}/auth/refresh").status_code == 401  # whole family revoked


def test_login_rate_limited(client):
    codes = [client.post(f"{V}/auth/login", json={"email": "rl@example.com", "password": "wrong-password"}).status_code
             for _ in range(12)]
    assert 429 in codes  # per-account lock after repeated failures


def test_password_reset_single_use(client):
    from skinsync import mailer

    email = f"reset-{uuid.uuid4().hex[:6]}@example.com"
    make_user(email)
    mailer.OUTBOX.clear()
    client.post(f"{V}/auth/request-password-reset", json={"email": email})
    tok = mailer.OUTBOX[-1].get_content().split("token=")[1].split()[0]
    assert client.post(f"{V}/auth/reset-password", json={"token": tok, "password": "New-Strong-Passphrase-7"}
                       ).status_code == 200
    assert client.post(f"{V}/auth/reset-password", json={"token": tok, "password": "Another-Strong-Pass-8"}
                       ).status_code == 400
    assert client.post(f"{V}/auth/login", json={"email": email, "password": "New-Strong-Passphrase-7"}).status_code == 200


def test_fr17_shelf_add_duplicate_remove(user):
    pid = demo_id(user, "DEMO Calm Cica Cream")
    assert user.post(f"{V}/shelf", json={"product_id": pid}).status_code == 201
    dup = user.post(f"{V}/shelf", json={"product_id": pid})
    assert dup.status_code == 409 and dup.json()["code"] == "ALREADY_ON_SHELF"
    assert [i["name"] for i in user.get(f"{V}/shelf").json()["items"]] == ["DEMO Calm Cica Cream"]
    assert user.delete(f"{V}/shelf/{pid}").status_code == 200


def test_guest_cannot_use_personal_features(client):
    assert client.get(f"{V}/shelf").status_code == 401
    assert client.get(f"{V}/routines").status_code == 401


def test_fr18_sc04_routine_build_and_analyze(user):
    ids = [demo_id(user, n) for n in ("DEMO Renewal Night Serum", "DEMO Smooth Acid Toner", "DEMO Double Acid Peel",
                                      "DEMO Mystery Botanical Oil")]
    r = user.post(f"{V}/routines", json={"name": "PM", "time_of_day": "evening",
                                         "steps": [{"product_id": i} for i in ids + [ids[0]]]})
    assert r.status_code == 201 and r.json()["warnings"]  # duplicate step flagged
    rid = r.json()["id"]
    res = user.post(f"{V}/routines/{rid}/analyze").json()
    assert res["status"] == "caution" and res["knowledge_is_demo"]
    assert any(p["result"]["status"] == "caution" for p in res["pairs"])
    assert res["missing_data"]  # mystery oil has an unknown ingredient
    assert res["shared_ingredients"]
    # reorder via PUT
    r2 = user.put(f"{V}/routines/{rid}", json={"name": "PM", "time_of_day": "evening",
                                               "steps": [{"product_id": i} for i in reversed(ids)]})
    assert [s["product"]["id"] for s in r2.json()["steps"]] == list(reversed(ids))


def test_save_comparison_claim_and_history(client):
    a, b = demo_id(client, "DEMO Renewal Night Serum"), demo_id(client, "DEMO Smooth Acid Toner")
    guest = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()
    email = f"claim-{uuid.uuid4().hex[:6]}@example.com"
    u = make_user(email)
    assert u.post(f"{V}/me/claim", json={"claim_tokens": [guest["claim_token"]]}).json()["claimed"] == 1
    hist = u.get(f"{V}/history").json()["items"]
    assert any(h["id"] == guest["id"] and h["type"] == "comparison" for h in hist)
    # once claimed, a guest can no longer read it
    assert client.get(f"{V}/comparisons/{guest['id']}").status_code == 404


def test_idor_other_users_data_is_invisible(user):
    other = make_user(f"other-{uuid.uuid4().hex[:6]}@example.com")
    pid = demo_id(user, "DEMO Hydra Gel Cream")
    rid = user.post(f"{V}/routines", json={"name": "AM", "time_of_day": "morning",
                                           "steps": [{"product_id": pid}]}).json()["id"]
    a, b = demo_id(user, "DEMO Bright C Serum"), pid
    cid = user.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()["id"]
    assert user.post(f"{V}/comparisons/{cid}/save").status_code == 200
    for method, url in [("get", f"{V}/routines/{rid}"), ("post", f"{V}/routines/{rid}/analyze"),
                        ("delete", f"{V}/routines/{rid}"), ("get", f"{V}/comparisons/{cid}"),
                        ("post", f"{V}/comparisons/{cid}/save"), ("delete", f"{V}/history/comparison/{cid}")]:
        r = getattr(other, method)(url)
        assert r.status_code == 404, (method, url, r.status_code)
    s = other.post(f"{V}/shares", json={"target_type": "routine", "target_id": rid})
    assert s.status_code == 404


def test_fr19_share_revoke_and_skin_refusal(user):
    a, b = demo_id(user, "DEMO Renewal Night Serum"), demo_id(user, "DEMO Smooth Acid Toner")
    cid = user.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()["id"]
    user.post(f"{V}/comparisons/{cid}/save")
    s = user.post(f"{V}/shares", json={"target_type": "comparison", "target_id": cid}).json()
    viewer = Client()
    pub = viewer.get(f"{V}/public/shares/{s['token']}").json()
    assert pub["read_only"] and pub["data"]["result"]["status"] == "caution" and "claim_token" not in pub["data"]
    share_id = user.get(f"{V}/shares").json()["items"][0]["share_id"]
    assert user.delete(f"{V}/shares/{share_id}").status_code == 200
    assert viewer.get(f"{V}/public/shares/{s['token']}").json()["code"] == "SHARE_UNAVAILABLE"
    r = user.post(f"{V}/shares", json={"target_type": "skin_analysis", "target_id": str(uuid.uuid4())})
    assert r.status_code == 403 and r.json()["code"] == "SHARE_REFUSED"


def test_sc02_guest_skin_analysis_full_pipeline_and_privacy(client):
    import os

    from tests.api.conftest import STORE

    r = client.post(f"{V}/skin-analyses", files={"image": ("face.jpg", face_like_jpeg(), "image/jpeg")},
                    data={"skin_type": "combination", "consent": "true"})
    assert r.status_code == 202, r.text
    aid, poll = r.json()["id"], r.json()["poll_token"]
    assert client.get(f"{V}/skin-analyses/{aid}").status_code == 404  # no poll token -> invisible
    res = client.get(f"{V}/skin-analyses/{aid}", headers={"X-Poll-Token": poll}).json()
    assert res["status"] == "completed" and res["is_demo_model"]
    assert res["demo_label"] == "Demo model — not a real analysis" and "not a medical diagnosis" in res["medical_boundary"]
    assert res["shareable"] is False and res["image_stored"] is False  # deleted right after analysis
    obs = res["result"]["observations"]
    assert obs and all("confidence" in o and "severity" in o for o in obs)
    assert all(p["evidence_strength"] and "observation_confidence" in p for p in res["result"]["products"])
    files = [f for _, _, fs in os.walk(STORE) for f in fs if not f.endswith(".tmp")]
    assert all("skin" not in f for f in files)
    assert client.delete(f"{V}/skin-analyses/{aid}", headers={"X-Poll-Token": poll}).status_code == 200
    assert client.get(f"{V}/skin-analyses/{aid}", headers={"X-Poll-Token": poll}).status_code == 404


def test_fr07_invalid_skin_images_rejected_with_guidance(client):
    r = client.post(f"{V}/skin-analyses", files={"image": ("x.gif", b"GIF89a" + b"\0" * 64, "image/gif")},
                    data={"consent": "true"})
    assert r.status_code == 422 and r.json()["code"] == "UNSUPPORTED_TYPE" and r.json()["details"]["guidance"]
    r = client.post(f"{V}/skin-analyses", files={"image": ("f.jpg", face_like_jpeg(), "image/jpeg")},
                    data={"consent": "false"})
    assert r.json()["code"] == "CONSENT_REQUIRED"


def test_registered_user_keeps_image_then_deletes_it(user):
    import os

    from tests.api.conftest import STORE

    r = user.post(f"{V}/skin-analyses", files={"image": ("f.jpg", face_like_jpeg(9), "image/jpeg")},
                  data={"consent": "true", "keep_image": "true"}).json()
    res = user.get(f"{V}/skin-analyses/{r['id']}").json()
    assert res["image_stored"] is True
    stored = [os.path.join(d, f) for d, _, fs in os.walk(STORE) for f in fs if "skin" in d]
    assert stored and all(b"\xff\xd8\xff" not in open(p, "rb").read()[:16] for p in stored)  # encrypted at rest
    assert user.delete(f"{V}/skin-analyses/{r['id']}/image").status_code == 200
    assert user.get(f"{V}/skin-analyses/{r['id']}").json()["image_stored"] is False


def test_ocr_label_scan_confirm_and_candidates(client):
    import io

    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("L", (1600, 260), 255)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 44)
    except OSError:
        font = ImageFont.load_default(size=44)
    ImageDraw.Draw(img).text((30, 90), "DEMO BASE AQUA, DEMO AMIDE-N, DEMO GLYCEROL-G", fill=0, font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    r = client.post(f"{V}/scan/label", files={"image": ("label.png", buf.getvalue(), "image/png")})
    assert r.status_code == 202, r.text
    sid, poll = r.json()["id"], r.json()["poll_token"]
    scan = client.get(f"{V}/scan/label/{sid}", headers={"X-Poll-Token": poll}).json()
    assert scan["status"] in ("auto_extracted", "pending_review") and "AMIDE" in scan["raw_text"].upper()
    conf = client.post(f"{V}/scan/label/{sid}/confirm", json={"text": "DEMO BASE AQUA, DEMO AMIDE-N, DEMO GLYCEROL-G"},
                       headers={"X-Poll-Token": poll}).json()
    assert conf["resolved"] == 3 and conf["product_candidates"][0]["name"] == "DEMO Budget Balance Serum"


def test_admin_routes_require_admin(user, client):
    assert client.get(f"{V}/admin/flags").status_code == 401
    assert user.get(f"{V}/admin/flags").status_code == 403


def test_sc05_knowledge_import_review_publish_and_audit(admin):
    vid = f"kv-test-{uuid.uuid4().hex[:6]}"
    r = admin.post(f"{V}/admin/knowledge-versions", json={"version_id": vid})
    assert r.status_code == 201 and r.json()["rules"] == 4  # shipped draft rules, all review_status draft
    bad = admin.post(f"{V}/admin/knowledge-versions/{vid}/transition", json={"to": "published", "reason": "skip review"})
    assert bad.status_code == 409 and bad.json()["code"] == "INVALID_TRANSITION"
    assert admin.post(f"{V}/admin/knowledge-versions/{vid}/transition",
                      json={"to": "in_review", "reason": "ready"}).status_code == 200
    blocked = admin.post(f"{V}/admin/knowledge-versions/{vid}/transition", json={"to": "published", "reason": "try"})
    assert blocked.status_code == 409 and blocked.json()["code"] == "PUBLISH_BLOCKED"
    assert any("not marked reviewed" in r for r in blocked.json()["details"]["reasons"])
    log = admin.get(f"{V}/admin/audit").json()["items"]
    assert any(e["action"] == "knowledge.in_review" and e["target"] == f"knowledge:{vid}" for e in log)
    dq = admin.get(f"{V}/admin/data-quality").json()
    assert dq["published_knowledge"] == "kv-0-empty"


def test_admin_corrects_mapping_creates_new_version_and_outdates_results(admin, client):
    a, b = demo_id(client, "DEMO Mystery Botanical Oil"), demo_id(client, "DEMO Hydra Gel Cream")
    cmp = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()
    assert cmp["result"]["status"] == "data_incomplete"
    old_vid = cmp["product_a"]["version_id"]
    r = admin.post(f"{V}/admin/ingredient-mappings", json={"product_version_id": old_vid, "position": 2,
                                                           "ingredient_id": "demo-oat-o", "reason": "verified label"})
    assert r.status_code == 200, r.text
    later = client.get(f"{V}/comparisons/{cmp['id']}").json()
    assert later["outdated"] and later["result"]["status"] == "data_incomplete"  # old result stays reproducible
    fresh = client.post(f"{V}/comparisons", json={"a": {"product_id": a}, "b": {"product_id": b}}).json()
    assert fresh["product_a"]["version_id"] == r.json()["new_version_id"]
    assert fresh["result"]["ingredients"]["unresolved_a"] == []


def test_fr20_account_deletion_removes_everything(user):
    import os

    from skinsync import db
    from tests.api.conftest import STORE

    pid = demo_id(user, "DEMO Oat Barrier Cream")
    user.post(f"{V}/shelf", json={"product_id": pid})
    user.post(f"{V}/routines", json={"name": "AM", "time_of_day": "morning", "steps": [{"product_id": pid}]})
    an = user.post(f"{V}/skin-analyses", files={"image": ("f.jpg", face_like_jpeg(5), "image/jpeg")},
                   data={"consent": "true", "keep_image": "true"}).json()
    me = user.get(f"{V}/me").json()
    before = sum(len(fs) for d, _, fs in os.walk(STORE) if "skin" in d)
    assert user.delete(f"{V}/me", json={"password": "wrong", "confirm": "DELETE"}).status_code == 401
    r = user.delete(f"{V}/me", json={"password": "Correct-Horse-Battery-9", "confirm": "DELETE"})
    assert r.status_code == 200 and r.json()["images_deleted"] >= 1
    after = sum(len(fs) for d, _, fs in os.walk(STORE) if "skin" in d)
    assert after == before - r.json()["images_deleted"]
    with db.transaction() as conn:
        for table in ("users", "profiles", "consents", "shelf_items", "routines", "skin_analyses", "uploads",
                      "refresh_tokens", "comparisons", "alternative_searches", "shares", "ocr_results"):
            col = "id" if table == "users" else "user_id"
            assert db.scalar(conn, f"SELECT count(*) FROM {table} WHERE {col} = :u", u=me["id"]) == 0, table
        assert db.scalar(conn, "SELECT count(*) FROM skin_analyses WHERE id = :i", i=an["id"]) == 0
    assert user.get(f"{V}/me").status_code == 401
