"""Comparison workflow (UC02): resolve -> normalise -> evaluate -> persist -> explain.

Cache key = (version A, version B, knowledge version, engine version). Every input that
can change a result is in the key, so invalidation is correct by construction: a new
formulation or knowledge version produces a new key, and old entries simply age out.
"""

from __future__ import annotations

import json
import logging
import time

from sqlalchemy.engine import Connection

from .. import db
from ..domain.compatibility import ComparisonResult, FormulationInput, evaluate
from ..domain.enums import ENGINE_VERSION
from ..errors import AppError, forbidden, not_found
from ..observability import CACHE
from ..security import get_redis, sign, unsign
from . import catalog, knowledge

log = logging.getLogger("skinsync.comparisons")
CACHE_TTL_S = 7 * 86400
CLAIM_TTL_S = 7 * 86400  # a guest has a week to sign up and keep the result


def resolve(conn: Connection, spec: dict) -> tuple[FormulationInput, dict | None]:
    """spec: {product_id | product_version_id | manual_ingredients, label?}."""
    if spec.get("product_version_id"):
        f = catalog.formulation_for_version(conn, spec["product_version_id"])
        return f, catalog.find_product(conn, f.product_id)
    if spec.get("product_id"):
        p = catalog.find_product(conn, spec["product_id"])
        v = catalog.current_version(conn, p["id"])
        if v is None:
            raise AppError(422, "NO_FORMULATION", f"{p['name']} has no formulation on record.")
        return catalog.formulation_for_version(conn, v["id"]), p
    if spec.get("manual_ingredients"):
        return catalog.manual_formulation(conn, spec["manual_ingredients"], spec.get("label") or "Manual entry"), None
    raise AppError(422, "PRODUCT_REQUIRED", "Choose a product or enter an ingredient list.")


def knowledge_for(conn: Connection, products: list[dict | None]) -> str:
    demo = [bool(p and p["is_demo"]) for p in products]
    if any(demo) and not all(d for d, p in zip(demo, products, strict=True) if p is not None):
        raise AppError(422, "DEMO_MIX", "Demo products can only be compared with other demo products.")
    want_demo = any(demo)
    kv_id = knowledge.active_version_id(conn, want_demo)
    if kv_id is None:
        if want_demo:
            raise AppError(503, "DEMO_UNAVAILABLE", "Demo knowledge is not loaded.")
        knowledge.ensure_bootstrap(conn)
        kv_id = knowledge.active_version_id(conn, False)
    return kv_id


def _cache_key(a: FormulationInput, b: FormulationInput, kv_id: str) -> str:
    return f"cmp:{a.product_version_id}:{b.product_version_id}:{kv_id}:{ENGINE_VERSION}"


def run(conn: Connection, spec_a: dict, spec_b: dict, user_id: str | None) -> dict:
    a, pa = resolve(conn, spec_a)
    b, pb = resolve(conn, spec_b)
    kv_id = knowledge_for(conn, [pa, pb])
    manual = a.product_version_id.startswith("manual:") or b.product_version_id.startswith("manual:")
    key = _cache_key(a, b, kv_id)
    result: ComparisonResult | None = None
    if not manual:
        try:
            raw = get_redis().get(key)
            if raw:
                result = ComparisonResult.model_validate_json(raw)
                CACHE.labels("comparison", "hit").inc()
        except Exception:
            CACHE.labels("comparison", "error").inc()
    if result is None:
        kv, _ = knowledge.load(conn, kv_id)
        result = evaluate(a, b, kv)
        if not manual:
            CACHE.labels("comparison", "miss").inc()
            try:
                get_redis().setex(key, CACHE_TTL_S, result.canonical_json())
            except Exception:
                pass
    payload = result.model_dump(mode="json")
    comparison_id = None
    if not manual:
        comparison_id = str(db.scalar(conn, """INSERT INTO comparisons (user_id, product_version_a, product_version_b,
                                  knowledge_version, engine_version, status, confidence, evidence_strength, completeness,
                                  result)
                                VALUES (:u, :a, :b, :kv, :e, CAST(:s AS compat_status), :c,
                                        CAST(:es AS evidence_strength), :cp, CAST(:r AS jsonb)) RETURNING id""",
                                     u=user_id, a=a.product_version_id, b=b.product_version_id, kv=kv_id,
                                     e=ENGINE_VERSION, s=result.status.value, c=result.confidence,
                                     es=result.evidence_strength.value, cp=result.completeness,
                                     r=json.dumps(payload)))
        for i, f in enumerate(result.findings):
            db.execute(conn, """INSERT INTO comparison_findings (comparison_id, ordinal, type, severity, rule_code,
                                  confidence, evidence_strength, explanation)
                                VALUES (:c, :o, :t, CAST(:s AS rule_severity), :r, :cf,
                                        CAST(:es AS evidence_strength), :ex)""",
                       c=comparison_id, o=i, t=f.type.value, s=f.severity.value, r=f.rule_code, cf=f.confidence,
                       es=f.evidence_strength.value, ex=f.explanation)
    claim = None
    if comparison_id and user_id is None:
        claim = sign({"t": "comparison", "id": comparison_id, "exp": int(time.time()) + CLAIM_TTL_S}, "claim")
    return present(comparison_id, payload, a, b, pa, pb, saved=False, claim_token=claim)


def present(comparison_id, payload, a, b, pa, pb, *, saved, outdated=None, claim_token=None) -> dict:
    out = {
        "id": comparison_id,
        "result": payload,
        "product_a": _product_view(pa, a),
        "product_b": _product_view(pb, b),
        "saved": saved,
        "outdated": outdated or [],
        "saveable": comparison_id is not None,
        "claim_token": claim_token,
    }
    return out


def _product_view(p: dict | None, f: FormulationInput) -> dict:
    return {
        "product_id": str(p["id"]) if p else None,
        "slug": p["slug"] if p else None,
        "name": f.product_name,
        "brand": p["brand"] if p else None,
        "is_demo": bool(p and p["is_demo"]),
        "version_id": f.product_version_id,
        "version_label": f.version_label,
        "ingredients": [i.model_dump(mode="json") for i in f.ingredients],
    }


def outdated_reasons(conn: Connection, rec: dict) -> list[str]:
    reasons = []
    for side in ("product_version_a", "product_version_b"):
        if not db.scalar(conn, "SELECT is_current FROM product_versions WHERE id = :v", v=rec[side]):
            reasons.append(f"A newer formulation exists for product {'A' if side.endswith('a') else 'B'}.")
    kv_demo = db.scalar(conn, "SELECT is_demo FROM knowledge_versions WHERE id = :k", k=rec["knowledge_version"])
    if knowledge.active_version_id(conn, bool(kv_demo)) != rec["knowledge_version"]:
        reasons.append("The knowledge base has been updated since this result.")
    if rec["engine_version"] != ENGINE_VERSION:
        reasons.append("The comparison engine has been updated.")
    return reasons


def get(conn: Connection, comparison_id: str, user_id: str | None, *, via_share: bool = False) -> dict:
    rec = db.row(conn, "SELECT * FROM comparisons WHERE id = :i", i=comparison_id)
    if not rec:
        raise not_found("Comparison")
    if rec["user_id"] is not None and str(rec["user_id"]) != user_id and not via_share:
        raise not_found("Comparison")  # 404, not 403: do not reveal that it exists
    a = catalog.formulation_for_version(conn, rec["product_version_a"])
    b = catalog.formulation_for_version(conn, rec["product_version_b"])
    pa, pb = catalog.find_product(conn, a.product_id), catalog.find_product(conn, b.product_id)
    return present(str(rec["id"]), rec["result"], a, b, pa, pb, saved=rec["saved"],
                   outdated=outdated_reasons(conn, rec))


def save(conn: Connection, comparison_id: str, user_id: str) -> None:
    rec = db.row(conn, "SELECT user_id FROM comparisons WHERE id = :i FOR UPDATE", i=comparison_id)
    if not rec:
        raise not_found("Comparison")
    if rec["user_id"] is not None and str(rec["user_id"]) != user_id:
        raise not_found("Comparison")
    db.execute(conn, "UPDATE comparisons SET user_id = :u, saved = true WHERE id = :i", u=user_id, i=comparison_id)


def claim(conn: Connection, token: str, user_id: str) -> bool:
    data = unsign(token, "claim")
    if not data or data.get("t") != "comparison":
        return False
    n = db.execute(conn, "UPDATE comparisons SET user_id = :u, saved = true WHERE id = :i AND user_id IS NULL",
                   u=user_id, i=data["id"])
    return n == 1


def forbid_if_not_owner(rec_user, user_id):
    if rec_user is None or str(rec_user) != user_id:
        raise forbidden()
