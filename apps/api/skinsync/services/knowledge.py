"""Knowledge versions in the database: import from reviewed YAML as a draft, review,
publish (DB triggers block unsafe publishes), retire, and load the active version.

Demo knowledge (fictional fixture rules, is_demo=true) is only used for demo products,
so fictional rules never touch real products and real rules never touch demo products.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError

from .. import db
from ..domain.enums import KnowledgeStatus
from ..domain.knowledge import (
    EvidenceRecord,
    InteractionRule,
    KnowledgeLoadError,
    KnowledgeVersion,
    build_knowledge_version,
)
from ..domain.skin import ConcernMapping, build_concern_map
from ..errors import AppError, not_found

EMPTY_VERSION_ID = "kv-0-empty"
_cache: dict[str, tuple[KnowledgeVersion, tuple[ConcernMapping, ...]]] = {}


def ensure_bootstrap(conn: Connection) -> None:
    """A published, empty real version so results always bind to a real version id.
    Honest by construction: it has no rules, so comparisons say 'insufficient evidence'."""
    if db.scalar(conn, "SELECT 1 FROM knowledge_versions WHERE status = 'published' AND NOT is_demo"):
        return
    if not db.scalar(conn, "SELECT 1 FROM knowledge_versions WHERE id = :i", i=EMPTY_VERSION_ID):
        db.execute(conn, """INSERT INTO knowledge_versions (id, notes) VALUES (:i, 'Bootstrap: no reviewed knowledge yet')""",
                   i=EMPTY_VERSION_ID)
    db.execute(conn, "UPDATE knowledge_versions SET status='published', published_at=now() WHERE id=:i",
               i=EMPTY_VERSION_ID)


def import_directory(conn: Connection, directory: Path, version_id: str, *, actor: str | None,
                     allow_fixture: bool = False) -> dict:
    if db.scalar(conn, "SELECT 1 FROM knowledge_versions WHERE id = :i", i=version_id):
        raise AppError(409, "VERSION_EXISTS", f"Knowledge version {version_id} already exists.")
    kv = _load_dir(directory, version_id, allow_fixture)
    concern_doc = yaml.safe_load((directory / "concern_map.yaml").read_text()) if (directory / "concern_map.yaml").exists() else {}
    try:
        cmap = build_concern_map((concern_doc or {}).get("mappings") or [], kv.evidence)
    except KnowledgeLoadError as e:
        raise AppError(422, "KNOWLEDGE_INVALID", str(e)) from e
    db.execute(conn, "INSERT INTO knowledge_versions (id, is_demo, created_by, notes) VALUES (:i, :d, :u, :n)",
               i=version_id, d=kv.is_demo, u=actor, n=f"Imported from {directory.name}")
    for e in kv.evidence.values():
        db.execute(conn, """INSERT INTO evidence_records (id, knowledge_version, claim, source_type, citation, strength,
                              publication_date, retrieved_at, reviewer, notes)
                            VALUES (:id, :kv, :c, :st, :ci, :s, :pd, :rd, :rv, :n)""",
                   id=e.id, kv=version_id, c=e.claim, st=e.source_type.value, ci=e.citation, s=e.strength.value,
                   pd=e.publication_date, rd=e.retrieved_at, rv=e.reviewer, n=e.notes)
    for r in kv.rules:
        db.execute(conn, """INSERT INTO interaction_rules (code, knowledge_version, interaction_type, severity, side_a,
                              side_b, mechanism_summary, practical_guidance, explanation_template, review_status,
                              last_reviewed)
                            VALUES (:c, :kv, :t, :s, CAST(:a AS jsonb), CAST(:b AS jsonb), :m, :g, :e, :rs, :lr)""",
                   c=r.code, kv=version_id, t=r.interaction_type.value, s=r.severity.value,
                   a=json.dumps([t.model_dump(exclude_none=True) for t in r.side_a]),
                   b=json.dumps([t.model_dump(exclude_none=True) for t in r.side_b]),
                   m=r.mechanism_summary, g=r.practical_guidance, e=r.explanation_template, rs=r.review_status,
                   lr=r.last_reviewed)
        for ev in r.evidence_ids:
            db.execute(conn, "INSERT INTO rule_evidence VALUES (:kv, :c, :e)", kv=version_id, c=r.code, e=ev)
    for m in cmap:
        db.execute(conn, """INSERT INTO concern_mappings (knowledge_version, observation, concern_category,
                              ingredient_classes, intended_role, evidence_ids) VALUES (:kv, :o, :c, :ic, :r, :e)""",
                   kv=version_id, o=m.observation, c=m.concern_category, ic=list(m.ingredient_classes),
                   r=m.intended_role, e=list(m.evidence_ids))
    return {"version_id": version_id, "is_demo": kv.is_demo, "rules": len(kv.rules), "evidence": len(kv.evidence),
            "concern_mappings": len(cmap)}


def _load_dir(directory: Path, version_id: str, allow_fixture: bool) -> KnowledgeVersion:
    from ..domain.knowledge import load_knowledge_dir

    try:
        return load_knowledge_dir(directory, version_id, allow_fixture=allow_fixture)
    except KnowledgeLoadError as e:
        raise AppError(422, "KNOWLEDGE_INVALID", str(e)) from e


def set_status(conn: Connection, version_id: str, target: str, actor: str | None) -> dict:
    kv = db.row(conn, "SELECT * FROM knowledge_versions WHERE id = :i FOR UPDATE", i=version_id)
    if not kv:
        raise not_found("Knowledge version")
    allowed = {"draft": {"in_review"}, "in_review": {"draft", "published"}, "published": {"retired"},
               "retired": {"published"}}  # re-publishing a retired version = rollback
    if target not in allowed.get(kv["status"], set()):
        raise AppError(409, "INVALID_TRANSITION", f"Cannot move a {kv['status']} version to {target}.")
    if target == "published":
        problems = publish_blockers(conn, version_id)
        if problems:
            raise AppError(409, "PUBLISH_BLOCKED", "This version cannot be published yet.", {"reasons": problems})
        # retire the currently published version of the same kind (real vs demo)
        db.execute(conn, """UPDATE knowledge_versions SET status='retired', retired_at=now()
                            WHERE status='published' AND is_demo = :d AND id <> :i""", d=kv["is_demo"], i=version_id)
    try:
        db.execute(conn, """UPDATE knowledge_versions SET status = CAST(:s AS knowledge_status),
                              published_at = CASE WHEN :s = 'published' THEN now() ELSE published_at END,
                              published_by = CASE WHEN :s = 'published' THEN CAST(:u AS uuid) ELSE published_by END,
                              retired_at = CASE WHEN :s = 'retired' THEN now() ELSE retired_at END
                            WHERE id = :i""", s=target, u=actor, i=version_id)
    except DBAPIError as e:
        raise AppError(409, "PUBLISH_BLOCKED", str(e.orig).split("\n")[0]) from e
    _cache.pop(version_id, None)
    return {"version_id": version_id, "from": kv["status"], "to": target}


def publish_blockers(conn: Connection, version_id: str) -> list[str]:
    out = []
    for r in db.rows(conn, """SELECT code FROM interaction_rules r WHERE knowledge_version = :i AND NOT EXISTS
                                (SELECT 1 FROM rule_evidence e WHERE e.knowledge_version = r.knowledge_version
                                 AND e.rule_code = r.code)""", i=version_id):
        out.append(f"Rule {r['code']} has no evidence.")
    for r in db.rows(conn, "SELECT code FROM interaction_rules WHERE knowledge_version = :i AND review_status <> 'reviewed'",
                     i=version_id):
        out.append(f"Rule {r['code']} is not marked reviewed.")
    for r in db.rows(conn, """SELECT id FROM evidence_records WHERE knowledge_version = :i
                              AND strength IN ('insufficient','unknown')""", i=version_id):
        out.append(f"Evidence {r['id']} is graded insufficient/unknown and cannot support a published rule.")
    kv = db.row(conn, "SELECT is_demo FROM knowledge_versions WHERE id = :i", i=version_id)
    if kv and not kv["is_demo"] and db.scalar(conn, """SELECT 1 FROM evidence_records WHERE knowledge_version = :i
                                                       AND source_type = 'fixture'""", i=version_id):
        out.append("Fixture evidence cannot be published as real knowledge.")
    for r in db.rows(conn, """SELECT open.target_ref FROM data_quality_flags open WHERE open.status = 'open'
                              AND open.reason = 'conflicting_evidence' AND open.target_ref LIKE :p""",
                     p=f"{version_id}:%"):
        out.append(f"Unresolved conflicting-evidence flag on {r['target_ref']}.")
    return out


def active_version_id(conn: Connection, demo: bool) -> str | None:
    return db.scalar(conn, "SELECT id FROM knowledge_versions WHERE status = 'published' AND is_demo = :d", d=demo)


def load(conn: Connection, version_id: str) -> tuple[KnowledgeVersion, tuple[ConcernMapping, ...]]:
    if version_id in _cache:
        return _cache[version_id]
    meta = db.row(conn, "SELECT * FROM knowledge_versions WHERE id = :i", i=version_id)
    if not meta:
        raise not_found("Knowledge version")
    ev = {e["id"]: EvidenceRecord(id=e["id"], claim=e["claim"], source_type=e["source_type"], citation=e["citation"],
                                   strength=e["strength"], publication_date=e["publication_date"],
                                   retrieved_at=e["retrieved_at"], reviewer=e["reviewer"], notes=e["notes"])
          for e in db.rows(conn, "SELECT * FROM evidence_records WHERE knowledge_version = :i", i=version_id)}
    links: dict[str, list[str]] = {}
    for link in db.rows(conn, "SELECT rule_code, evidence_id FROM rule_evidence WHERE knowledge_version = :i ORDER BY 2",
                        i=version_id):
        links.setdefault(link["rule_code"], []).append(link["evidence_id"])
    rules = []
    for r in db.rows(conn, "SELECT * FROM interaction_rules WHERE knowledge_version = :i ORDER BY code", i=version_id):
        if not links.get(r["code"]):
            continue  # cannot happen for a published version (trigger); defensive for drafts
        rules.append(InteractionRule(code=r["code"], interaction_type=r["interaction_type"], severity=r["severity"],
                                     side_a=r["side_a"], side_b=r["side_b"], mechanism_summary=r["mechanism_summary"],
                                     practical_guidance=r["practical_guidance"],
                                     explanation_template=r["explanation_template"],
                                     evidence_ids=tuple(links[r["code"]]), review_status=r["review_status"],
                                     last_reviewed=r["last_reviewed"]))
    kv = KnowledgeVersion(version_id=version_id, status=KnowledgeStatus(meta["status"]), is_demo=meta["is_demo"],
                          rules=tuple(rules), evidence=ev)
    cmap = tuple(ConcernMapping(observation=m["observation"], concern_category=m["concern_category"],
                                ingredient_classes=tuple(m["ingredient_classes"]), intended_role=m["intended_role"],
                                evidence_ids=tuple(m["evidence_ids"]))
                 for m in db.rows(conn, "SELECT * FROM concern_mappings WHERE knowledge_version = :i ORDER BY 2, 3",
                                  i=version_id))
    if meta["status"] in ("published", "retired"):
        _cache[version_id] = (kv, cmap)  # immutable once published
    return kv, cmap


def build_from_db_check(kv: KnowledgeVersion) -> None:
    """Re-validate a version through the domain loader (used by tests and the publish preview)."""
    build_knowledge_version(kv.version_id, [r.model_dump(mode="json") for r in kv.rules],
                            [e.model_dump(mode="json") for e in kv.evidence.values()], allow_fixture=kv.is_demo,
                            is_demo=kv.is_demo)
