"""API integration test harness: real PostgreSQL + real Redis, jobs run inline."""

import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

API = Path(__file__).resolve().parents[2]
ROOT = API.parents[1]
DB = "skinsync_apitest"
STORE = tempfile.mkdtemp(prefix="skinsync-store-")

os.environ.update({
    "SKINSYNC_ENV": "test",
    "SKINSYNC_DATABASE_URL": f"postgresql+psycopg://postgres@localhost:5432/{DB}",
    "SKINSYNC_REDIS_URL": "redis://localhost:6379/15",
    "SKINSYNC_QUEUE_SYNC": "1",
    "SKINSYNC_DEMO_MODE": "true",
    "SKINSYNC_STORAGE_DIR": STORE,
    "SKINSYNC_KNOWLEDGE_DIR": str(ROOT / "knowledge"),
    "SKINSYNC_ADMIN_PASSWORD": "Adm1n-strong-passphrase",
    "SKINSYNC_SKIN_MODEL_ADAPTER": "mock",
})
os.environ.pop("SKINSYNC_SMTP_HOST", None)


def _psql(*args):
    return subprocess.run(["psql", "-h", "localhost", "-U", "postgres", "-X", "-q", *args], capture_output=True, text=True)


@pytest.fixture(scope="session", autouse=True)
def database():
    if shutil.which("psql") is None or _psql("-c", "select 1").returncode != 0:
        pytest.skip("PostgreSQL not reachable")
    _psql("-c", f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
    assert _psql("-c", f"CREATE DATABASE {DB}").returncode == 0
    r = subprocess.run([str(Path(os.sys.executable).parent / "alembic"), "upgrade", "head"], cwd=API,
                       capture_output=True, text=True, env=os.environ.copy())
    assert r.returncode == 0, r.stderr
    from skinsync import cli, db
    from skinsync.services import catalog

    cli.bootstrap()
    cli.seed_demo()
    cli.create_admin("admin@example.com")
    # a few NON-demo test products for the real-knowledge path (fictional names, source "test")
    with db.transaction() as conn:
        master = catalog.load_master(conn, max_age_s=0)
        from datetime import date

        for ref, name, ing in [("t1", "Test Plain Lotion", "DEMO BASE AQUA, DEMO GLYCEROL-G"),
                               ("t2", "Test Plain Cream", "DEMO BASE AQUA, DEMO EMOLLIENT-E"),
                               ("t3", "Test Unknown Mix", "DEMO BASE AQUA, Totally Unknown Extract"),
                               ("t4", "Test No List", "")]:
            catalog.upsert_product(conn, catalog.ProductRecord(
                source="test", source_ref=ref, name=name, brand="Test Brand", category="moisturizer",
                category_parent="face", raw_ingredients=ing or None, observed_at=date(2026, 1, 1),
                barcode=f"400000000000{ref[-1]}"), master, None)
    yield
    from skinsync import db as _db

    _db.reset_engine()
    _psql("-c", f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
    shutil.rmtree(STORE, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_redis():
    from skinsync.security import get_redis

    get_redis().flushdb()
    yield


class Client:
    """TestClient wrapper that performs the CSRF double-submit like the real frontend."""

    def __init__(self):
        from fastapi.testclient import TestClient

        from skinsync.main import app

        self.c = TestClient(app)
        self.csrf = self.c.get("/api/v1/auth/csrf").json()["csrf_token"]

    def _h(self, extra=None):
        return {"X-CSRF-Token": self.csrf, **(extra or {})}

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def post(self, url, json=None, headers=None, **kw):
        return self.c.post(url, json=json, headers=self._h(headers), **kw)

    def put(self, url, json=None, **kw):
        return self.c.put(url, json=json, headers=self._h(), **kw)

    def patch(self, url, json=None, **kw):
        return self.c.patch(url, json=json, headers=self._h(), **kw)

    def delete(self, url, json=None, headers=None, **kw):
        return self.c.request("DELETE", url, json=json, headers=self._h(headers), **kw)


@pytest.fixture
def client():
    return Client()


def make_user(email: str, password: str = "Correct-Horse-Battery-9") -> Client:
    from skinsync import mailer

    c = Client()
    mailer.OUTBOX.clear()
    r = c.post("/api/v1/auth/signup", json={"email": email, "password": password, "age_confirmed_18": True,
                                            "accept_terms": True})
    assert r.status_code == 202, r.text
    body = mailer.OUTBOX[-1].get_content()
    token = body.split("token=")[1].split()[0]
    assert c.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
    r = c.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def user():
    import uuid

    return make_user(f"user-{uuid.uuid4().hex[:8]}@example.com")


@pytest.fixture
def admin():
    c = Client()
    assert c.post("/api/v1/auth/login", json={"email": "admin@example.com",
                                              "password": "Adm1n-strong-passphrase"}).status_code == 200
    return c


def face_like_jpeg(seed: int = 3) -> bytes:
    rng = np.random.default_rng(seed)
    arr = np.clip(rng.normal(130, 40, (800, 800, 3)), 0, 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return buf.getvalue()


def demo_id(client, name: str) -> str:
    r = client.get("/api/v1/products", params={"q": name})
    items = [i for i in r.json()["items"] if i["name"] == name]
    assert items, f"{name} not found"
    return items[0]["id"]
