"""Knowledge layer: evidence records, interaction rules, knowledge versions.

All scientific content comes from team-reviewed YAML files (knowledge/*.yaml),
never from code. The loader enforces:
  * every rule cites >= 1 existing evidence record;
  * evidence uses the controlled source-type and strength vocabularies;
  * fixture/demo content (source_type=fixture or a `fixture: true` file header)
    is refused unless the caller explicitly allows it (tests and the labelled demo).
"""

from __future__ import annotations

import string
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import EvidenceStrength, InteractionType, KnowledgeStatus, Severity, SourceType


class KnowledgeLoadError(ValueError):
    pass


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=80)
    claim: str = Field(min_length=1, max_length=2000)
    source_type: SourceType
    citation: str = Field(min_length=3, max_length=1000)
    strength: EvidenceStrength
    publication_date: date | None = None
    retrieved_at: date | None = None
    reviewer: str | None = None
    notes: str | None = None


class Term(BaseModel):
    """Matches an ingredient on one side of a pair, by canonical id or function class."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ingredient: str | None = None
    function_class: str | None = None
    max_position: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _exactly_one(self):
        if (self.ingredient is None) == (self.function_class is None):
            raise ValueError("a term needs exactly one of `ingredient` or `function_class`")
        return self


_ALLOWED_PLACEHOLDERS = {"a_ingredients", "b_ingredients", "product_a", "product_b"}


class InteractionRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1, max_length=80)
    interaction_type: InteractionType
    severity: Severity
    side_a: tuple[Term, ...] = Field(min_length=1)
    side_b: tuple[Term, ...] = Field(min_length=1)
    mechanism_summary: str = Field(min_length=1, max_length=2000)
    practical_guidance: str = Field(min_length=1, max_length=2000)
    explanation_template: str = Field(min_length=1, max_length=2000)
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    review_status: str = "reviewed"
    last_reviewed: date | None = None

    @field_validator("explanation_template")
    @classmethod
    def _placeholders(cls, v: str) -> str:
        names = {f for _, f, _, _ in string.Formatter().parse(v) if f}
        bad = names - _ALLOWED_PLACEHOLDERS
        if bad:
            raise ValueError(f"unknown placeholders {sorted(bad)}; allowed {sorted(_ALLOWED_PLACEHOLDERS)}")
        return v


class KnowledgeVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version_id: str = Field(min_length=1, max_length=80)
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    is_demo: bool = False
    rules: tuple[InteractionRule, ...] = ()
    evidence: dict[str, EvidenceRecord] = Field(default_factory=dict)

    def evidence_for(self, rule: InteractionRule) -> list[EvidenceRecord]:
        return [self.evidence[e] for e in rule.evidence_ids]


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise KnowledgeLoadError(f"{path}: top level must be a mapping")
    return data


def build_knowledge_version(
    version_id: str,
    rules_data: list[dict],
    evidence_data: list[dict],
    *,
    allow_fixture: bool = False,
    is_demo: bool = False,
    status: KnowledgeStatus = KnowledgeStatus.DRAFT,
) -> KnowledgeVersion:
    try:
        evidence = [EvidenceRecord(**e) for e in evidence_data]
        rules = [InteractionRule(**r) for r in rules_data]
    except Exception as exc:  # pydantic ValidationError -> uniform error
        raise KnowledgeLoadError(str(exc)) from exc

    by_id: dict[str, EvidenceRecord] = {}
    for e in evidence:
        if e.id in by_id:
            raise KnowledgeLoadError(f"duplicate evidence id {e.id}")
        if not allow_fixture and (e.source_type == SourceType.FIXTURE or "FIXTURE" in e.citation.upper()):
            raise KnowledgeLoadError(f"evidence {e.id} is fixture content and cannot be loaded as real knowledge")
        by_id[e.id] = e

    seen: set[str] = set()
    for r in rules:
        if r.code in seen:
            raise KnowledgeLoadError(f"duplicate rule code {r.code}")
        seen.add(r.code)
        missing = [e for e in r.evidence_ids if e not in by_id]
        if missing:
            raise KnowledgeLoadError(f"rule {r.code} cites missing evidence {missing}")

    if is_demo and not allow_fixture:
        raise KnowledgeLoadError("demo knowledge requires allow_fixture=True")

    return KnowledgeVersion(
        version_id=version_id,
        status=status,
        is_demo=is_demo,
        rules=tuple(sorted(rules, key=lambda r: r.code)),
        evidence=by_id,
    )


def load_knowledge_dir(directory: Path, version_id: str, *, allow_fixture: bool = False) -> KnowledgeVersion:
    """Load rules.yaml + evidence.yaml from a directory as a DRAFT version."""
    rules_doc = _read_yaml(directory / "rules.yaml")
    ev_doc = _read_yaml(directory / "evidence.yaml")
    is_fixture_file = bool(rules_doc.get("fixture") or ev_doc.get("fixture"))
    if is_fixture_file and not allow_fixture:
        raise KnowledgeLoadError(f"{directory} is marked `fixture: true`; refusing to load as real knowledge")
    return build_knowledge_version(
        version_id,
        rules_doc.get("rules") or [],
        ev_doc.get("evidence") or [],
        allow_fixture=allow_fixture,
        is_demo=is_fixture_file,
    )
