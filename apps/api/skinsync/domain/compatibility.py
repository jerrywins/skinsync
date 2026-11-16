"""Deterministic two-formulation compatibility engine (SkinSync §12.2, FR-02/04/05, SC-01).

`evaluate(a, b, knowledge)` is a pure function: no I/O, no clock, no randomness, no ML.
The same (formulations, knowledge version) always yields byte-identical JSON.

Status precedence (most conservative first):
  1. DATA_INCOMPLETE     - a formulation has no ingredient list, or unresolved ingredients
                           mean a rule could be missed. (Rule findings are still reported.)
  2. STRONG_CAUTION      - a reviewed rule with severity strong_caution fired.
  3. CAUTION             - a reviewed rule with severity caution fired.
  4. INSUFFICIENT_EVIDENCE - the knowledge version has no rules at all, so silence means nothing.
  5. NO_NOTABLE_INTERACTION - everything resolved, rules evaluated, none fired.

A fired rule outranks DATA_INCOMPLETE for the headline: if we *know* about a caution we
say so, and still list the missing data. With no fired rule, missing data wins over
"no notable interaction" - unknown never becomes safe (principle 1.2.2).
"""

from __future__ import annotations

import json
from itertools import product as cartesian

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    ENGINE_VERSION,
    STATUS_LABELS,
    CompatibilityStatus,
    ConfidenceLevel,
    EvidenceStrength,
    FindingType,
    Severity,
    confidence_level,
)
from .ingredients import NormalizedIngredient
from .knowledge import InteractionRule, KnowledgeVersion, Term

_SEVERITY_RANK = {Severity.STRONG_CAUTION: 3, Severity.CAUTION: 2, Severity.INFO: 1}
_STRENGTH_RANK = {
    EvidenceStrength.HIGH: 5,
    EvidenceStrength.MODERATE: 4,
    EvidenceStrength.LIMITED: 3,
    EvidenceStrength.INSUFFICIENT: 2,
    EvidenceStrength.UNKNOWN: 1,
}


class FormulationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str
    product_version_id: str
    product_name: str
    version_label: str
    ingredients: tuple[NormalizedIngredient, ...] = ()
    has_ingredient_list: bool = True


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    claim: str
    citation: str
    source_type: str
    strength: EvidenceStrength


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: FindingType
    severity: Severity
    title: str
    explanation: str
    why: tuple[str, ...]  # numbered "Why was this flagged?" steps
    practical_guidance: str | None = None
    rule_code: str | None = None
    interaction_type: str | None = None
    a_ingredients: tuple[str, ...] = ()
    b_ingredients: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    confidence_level: ConfidenceLevel
    evidence_strength: EvidenceStrength
    evidence: tuple[EvidenceRef, ...] = ()

    @property
    def is_conclusive(self) -> bool:
        return self.type == FindingType.RULE and self.evidence_strength in (
            EvidenceStrength.HIGH,
            EvidenceStrength.MODERATE,
        )


class IngredientDiff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    shared: tuple[str, ...]
    a_only: tuple[str, ...]
    b_only: tuple[str, ...]
    unresolved_a: tuple[str, ...]
    unresolved_b: tuple[str, ...]


class ComparisonResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: CompatibilityStatus
    status_label: str
    confidence: float
    confidence_level: ConfidenceLevel
    evidence_strength: EvidenceStrength  # strongest evidence behind a fired rule, else UNKNOWN
    completeness: float
    findings: tuple[Finding, ...]
    ingredients: IngredientDiff
    product_version_a: str
    product_version_b: str
    knowledge_version: str
    knowledge_is_demo: bool
    engine_version: str = ENGINE_VERSION

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def _term_matches(term: Term, ing: NormalizedIngredient) -> bool:
    if not ing.resolved:
        return False
    if term.max_position is not None and ing.position > term.max_position:
        return False
    if term.ingredient is not None:
        return ing.canonical_id == term.ingredient
    return term.function_class in ing.function_classes


def _side_hits(terms: tuple[Term, ...], ings: tuple[NormalizedIngredient, ...]) -> list[NormalizedIngredient]:
    return [i for i in ings if any(_term_matches(t, i) for t in terms)]


def _completeness(f: FormulationInput) -> float:
    if not f.has_ingredient_list or not f.ingredients:
        return 0.0
    resolved = sum(1 for i in f.ingredients if i.resolved)
    return resolved / len(f.ingredients)


def _names(ings: list[NormalizedIngredient]) -> tuple[str, ...]:
    return tuple(sorted({i.inci_name or i.raw for i in ings}))


def _evaluate_rule(
    rule: InteractionRule, a: FormulationInput, b: FormulationInput, kv: KnowledgeVersion
) -> Finding | None:
    # Rules are symmetric: try (A as side_a, B as side_b) and the reverse.
    for left, right, swapped in ((a, b, False), (b, a, True)):
        hits_l = _side_hits(rule.side_a, left.ingredients)
        hits_r = _side_hits(rule.side_b, right.ingredients)
        if hits_l and hits_r:
            a_hits, b_hits = (hits_r, hits_l) if swapped else (hits_l, hits_r)
            break
    else:
        return None

    ev = sorted(kv.evidence_for(rule), key=lambda e: (-_STRENGTH_RANK[e.strength], e.id))
    strongest = ev[0].strength
    conf = min(i.confidence for i in (*a_hits, *b_hits))
    a_names, b_names = _names(a_hits), _names(b_hits)
    explanation = rule.explanation_template.format(
        a_ingredients=", ".join(a_names),
        b_ingredients=", ".join(b_names),
        product_a=a.product_name,
        product_b=b.product_name,
    )
    why = (
        f"{', '.join(a_names)} was identified in {a.product_name} ({a.version_label}).",
        f"{', '.join(b_names)} was identified in {b.product_name} ({b.version_label}).",
        f"Knowledge rule {rule.code} links this combination to: {rule.interaction_type.value.replace('_', ' ')}.",
        f"Strongest supporting evidence: {strongest.value}.",
        f"Knowledge version used: {kv.version_id}.",
    )
    return Finding(
        type=FindingType.RULE,
        severity=rule.severity,
        title=rule.mechanism_summary,
        explanation=explanation,
        why=why,
        practical_guidance=rule.practical_guidance,
        rule_code=rule.code,
        interaction_type=rule.interaction_type.value,
        a_ingredients=a_names,
        b_ingredients=b_names,
        confidence=round(conf, 4),
        confidence_level=confidence_level(conf),
        evidence_strength=strongest,
        evidence=tuple(
            EvidenceRef(id=e.id, claim=e.claim, citation=e.citation, source_type=e.source_type.value, strength=e.strength)
            for e in ev
        ),
    )


def evaluate(a: FormulationInput, b: FormulationInput, kv: KnowledgeVersion) -> ComparisonResult:
    findings: list[Finding] = []

    # --- data completeness -------------------------------------------------
    missing = [f for f in (a, b) if not f.has_ingredient_list or not f.ingredients]
    for f in missing:
        findings.append(
            Finding(
                type=FindingType.INCOMPLETE,
                severity=Severity.INFO,
                title=f"No ingredient list for {f.product_name}",
                explanation=(
                    f"{f.product_name} ({f.version_label}) has no ingredient list in our data, "
                    "so it could not be checked."
                ),
                why=("Compatibility is evaluated from ingredient lists; none is available for this formulation.",),
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                evidence_strength=EvidenceStrength.UNKNOWN,
            )
        )

    unresolved_a = tuple(sorted({i.raw for i in a.ingredients if not i.resolved}))
    unresolved_b = tuple(sorted({i.raw for i in b.ingredients if not i.resolved}))
    for f, unresolved in ((a, unresolved_a), (b, unresolved_b)):
        if unresolved:
            findings.append(
                Finding(
                    type=FindingType.UNRESOLVED,
                    severity=Severity.INFO,
                    title=f"{len(unresolved)} unrecognised ingredient(s) in {f.product_name}",
                    explanation=(
                        "These ingredients could not be matched to a known ingredient. They were not "
                        "treated as harmless; an interaction involving them could be missed."
                    ),
                    why=tuple(f"Not recognised: {u}" for u in unresolved),
                    a_ingredients=unresolved if f is a else (),
                    b_ingredients=unresolved if f is b else (),
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.LOW,
                    evidence_strength=EvidenceStrength.UNKNOWN,
                )
            )

    # --- factual: shared key actives (no scientific claim attached) --------
    a_keys = {i.canonical_id: i for i in a.ingredients if i.resolved and i.is_key_active}
    b_keys = {i.canonical_id: i for i in b.ingredients if i.resolved and i.is_key_active}
    for cid in sorted(set(a_keys) & set(b_keys)):
        name = a_keys[cid].inci_name or cid
        findings.append(
            Finding(
                type=FindingType.SHARED_KEY_ACTIVE,
                severity=Severity.INFO,
                title=f"Both products contain {name}",
                explanation=(
                    f"{name} is listed as a key active in both products. Using both means applying it twice."
                ),
                why=(f"{name} appears as a key active in {a.product_name} and in {b.product_name}.",),
                a_ingredients=(name,),
                b_ingredients=(name,),
                confidence=round(min(a_keys[cid].confidence, b_keys[cid].confidence), 4),
                confidence_level=confidence_level(min(a_keys[cid].confidence, b_keys[cid].confidence)),
                evidence_strength=EvidenceStrength.UNKNOWN,
            )
        )

    # --- reviewed rules ----------------------------------------------------
    rule_findings = [f for r in kv.rules if (f := _evaluate_rule(r, a, b, kv))]
    findings.extend(rule_findings)

    if not kv.rules:
        findings.append(
            Finding(
                type=FindingType.INSUFFICIENT_EVIDENCE,
                severity=Severity.INFO,
                title="No reviewed interaction knowledge available",
                explanation=(
                    f"Knowledge version {kv.version_id} contains no reviewed interaction rules, "
                    "so the absence of findings tells you nothing."
                ),
                why=("No reviewed interaction rules are published yet.",),
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                evidence_strength=EvidenceStrength.INSUFFICIENT,
            )
        )

    # --- headline status ---------------------------------------------------
    worst = max((_SEVERITY_RANK[f.severity] for f in rule_findings), default=0)
    if worst == 3:
        status = CompatibilityStatus.STRONG_CAUTION
    elif worst == 2:
        status = CompatibilityStatus.CAUTION
    elif missing or unresolved_a or unresolved_b:
        status = CompatibilityStatus.DATA_INCOMPLETE
    elif not kv.rules:
        status = CompatibilityStatus.INSUFFICIENT_EVIDENCE
    else:
        status = CompatibilityStatus.NO_NOTABLE_INTERACTION

    # --- result confidence: weakest link, not an average (SkinIQ §173) ---
    completeness = round(min(_completeness(a), _completeness(b)), 4)
    norm_conf = min((i.confidence for f in (a, b) for i in f.ingredients if i.resolved), default=0.0)
    factors = [completeness, norm_conf]
    if rule_findings:
        factors.append(min(f.confidence for f in rule_findings))
    if not kv.rules:
        factors.append(0.0)  # rule applicability unknown
    confidence = round(min(factors), 4)

    evidence_strength = max(
        (f.evidence_strength for f in rule_findings), key=lambda s: _STRENGTH_RANK[s], default=EvidenceStrength.UNKNOWN
    )

    def _resolved_names(f: FormulationInput) -> set[str]:
        return {i.inci_name for i in f.ingredients if i.resolved and i.inci_name}

    ra, rb = _resolved_names(a), _resolved_names(b)
    order = {FindingType.RULE: 0, FindingType.SHARED_KEY_ACTIVE: 1, FindingType.INCOMPLETE: 2,
             FindingType.UNRESOLVED: 3, FindingType.INSUFFICIENT_EVIDENCE: 4}
    findings.sort(key=lambda f: (order[f.type], -_SEVERITY_RANK[f.severity], f.rule_code or "", f.title))

    return ComparisonResult(
        status=status,
        status_label=STATUS_LABELS[status],
        confidence=confidence,
        confidence_level=confidence_level(confidence),
        evidence_strength=evidence_strength,
        completeness=completeness,
        findings=tuple(findings),
        ingredients=IngredientDiff(
            shared=tuple(sorted(ra & rb)),
            a_only=tuple(sorted(ra - rb)),
            b_only=tuple(sorted(rb - ra)),
            unresolved_a=unresolved_a,
            unresolved_b=unresolved_b,
        ),
        product_version_a=a.product_version_id,
        product_version_b=b.product_version_id,
        knowledge_version=kv.version_id,
        knowledge_is_demo=kv.is_demo,
    )


def evaluate_routine(
    items: list[FormulationInput], kv: KnowledgeVersion
) -> list[tuple[int, int, ComparisonResult]]:
    """Pairwise compatibility across a routine (SC-04). Index pairs are stable."""
    return [(i, j, evaluate(items[i], items[j], kv)) for i, j in cartesian(range(len(items)), repeat=2) if i < j]
