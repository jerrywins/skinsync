"""FR-02/04/05, SC-01: deterministic compatibility engine. Test IDs C01-C07 from SkinIQ spec §107."""

import random

import pytest
from pydantic import ValidationError

from skinsync.domain.compatibility import FormulationInput, evaluate, evaluate_routine
from skinsync.domain.enums import CompatibilityStatus, EvidenceStrength, FindingType, Severity
from skinsync.domain.knowledge import KnowledgeLoadError, KnowledgeVersion, build_knowledge_version, load_knowledge_dir

EMPTY_KV = KnowledgeVersion(version_id="kv-empty")


def test_c01_identical_product_reports_shared_key_active(make_formulation, fixture_kv):
    a = make_formulation("TEST_BASE_WATER, TEST_ACTIVE_A", "A", keys={"test-active-a"})
    b = make_formulation("TEST_BASE_WATER, TEST_ACTIVE_A", "B", keys={"test-active-a"})
    r = evaluate(a, b, fixture_kv)
    shared = [f for f in r.findings if f.type == FindingType.SHARED_KEY_ACTIVE]
    assert len(shared) == 1 and shared[0].evidence_strength == EvidenceStrength.UNKNOWN
    assert r.ingredients.shared == ("TEST_ACTIVE_A", "TEST_BASE_WATER")


def test_c02_known_interaction_gives_caution_with_evidence(make_formulation, fixture_kv):
    a = make_formulation("TEST_BASE_WATER, TEST_ACTIVE_A", "A")
    b = make_formulation("TEST_BASE_WATER, TEST_EXFOLIANT_B", "B")
    r = evaluate(a, b, fixture_kv)
    assert r.status == CompatibilityStatus.CAUTION
    (f,) = [f for f in r.findings if f.type == FindingType.RULE]
    assert f.rule_code == "FIX-R1" and f.evidence and f.evidence_strength == EvidenceStrength.MODERATE
    assert len(f.why) == 5 and "fixture-kv-1" in f.why[-1]
    assert r.evidence_strength == EvidenceStrength.MODERATE


def test_rules_are_symmetric(make_formulation, fixture_kv):
    a = make_formulation("TEST_EXFOLIANT_B", "A")
    b = make_formulation("TEST_ACTIVE_A", "B")
    r = evaluate(a, b, fixture_kv)
    (f,) = [f for f in r.findings if f.type == FindingType.RULE]
    assert f.a_ingredients == ("TEST_EXFOLIANT_B",) and f.b_ingredients == ("TEST_ACTIVE_A",)


def test_strong_caution_by_function_class(make_formulation, fixture_kv):
    r = evaluate(make_formulation("TEST_STRONG_C", "A"), make_formulation("TEST_STRONG_D", "B"), fixture_kv)
    assert r.status == CompatibilityStatus.STRONG_CAUTION


def test_c03_no_relevant_rule_gives_no_notable_interaction_with_exact_wording(make_formulation, fixture_kv):
    r = evaluate(make_formulation("TEST_BASE_WATER", "A"), make_formulation("TEST_HUMECTANT_E", "B"), fixture_kv)
    assert r.status == CompatibilityStatus.NO_NOTABLE_INTERACTION
    assert r.status_label == (
        "No notable interaction identified in the current knowledge base for the formulations supplied."
    )
    assert "safe" not in r.status_label.lower()


def test_c04_missing_ingredient_list_is_data_incomplete(make_formulation, fixture_kv):
    a = make_formulation("", "A", has_list=False)
    b = make_formulation("TEST_BASE_WATER", "B")
    r = evaluate(a, b, fixture_kv)
    assert r.status == CompatibilityStatus.DATA_INCOMPLETE and r.completeness == 0.0
    assert any(f.type == FindingType.INCOMPLETE for f in r.findings)


def test_c05_unknown_ingredient_is_unresolved_and_never_clear(make_formulation, fixture_kv):
    r = evaluate(make_formulation("TEST_BASE_WATER, Mystery Root", "A"), make_formulation("TEST_HUMECTANT_E", "B"), fixture_kv)
    assert r.status == CompatibilityStatus.DATA_INCOMPLETE
    assert r.ingredients.unresolved_a == ("Mystery Root",)
    assert r.completeness == 0.5


def test_fired_rule_outranks_incomplete_data_but_still_lists_it(make_formulation, fixture_kv):
    a = make_formulation("TEST_ACTIVE_A, Mystery Root", "A")
    b = make_formulation("TEST_EXFOLIANT_B", "B")
    r = evaluate(a, b, fixture_kv)
    assert r.status == CompatibilityStatus.CAUTION
    assert any(f.type == FindingType.UNRESOLVED for f in r.findings)


def test_c06_result_is_bound_to_formulation_versions(make_formulation, fixture_kv):
    old = make_formulation("TEST_ACTIVE_A", "A", vid="pv-A-2024")
    new = make_formulation("TEST_HUMECTANT_E", "A", vid="pv-A-2026")
    b = make_formulation("TEST_EXFOLIANT_B", "B")
    r_old, r_new = evaluate(old, b, fixture_kv), evaluate(new, b, fixture_kv)
    assert r_old.product_version_a == "pv-A-2024" and r_old.status == CompatibilityStatus.CAUTION
    assert r_new.product_version_a == "pv-A-2026" and r_new.status == CompatibilityStatus.NO_NOTABLE_INTERACTION


def test_c07_malformed_product_is_a_validation_error():
    with pytest.raises(ValidationError):
        FormulationInput(product_id="x", product_name="x")  # missing required fields


def test_empty_knowledge_returns_insufficient_evidence_not_a_verdict(make_formulation):
    r = evaluate(make_formulation("TEST_BASE_WATER", "A"), make_formulation("TEST_HUMECTANT_E", "B"), EMPTY_KV)
    assert r.status == CompatibilityStatus.INSUFFICIENT_EVIDENCE
    assert r.confidence == 0.0


def test_confidence_and_evidence_strength_are_separate_fields(make_formulation, fixture_kv):
    a = make_formulation("TEST_ACTIVE_A / TEST_HUMECTANT_E", "A")  # slash name -> confidence 0.8
    r = evaluate(a, make_formulation("TEST_EXFOLIANT_B", "B"), fixture_kv)
    (f,) = [f for f in r.findings if f.type == FindingType.RULE]
    assert f.confidence < 1.0 and f.evidence_strength == EvidenceStrength.MODERATE


def test_determinism_same_inputs_byte_identical(make_formulation, fixture_kv):
    a = make_formulation("TEST_ACTIVE_A, Mystery Root, TEST_STRONG_C", "A", keys={"test-active-a"})
    b = make_formulation("TEST_EXFOLIANT_B, TEST_STRONG_D, TEST_ACTIVE_A", "B", keys={"test-active-a"})
    outs = {evaluate(a, b, fixture_kv).canonical_json() for _ in range(20)}
    assert len(outs) == 1


def test_property_status_never_clear_when_anything_unresolved(make_formulation, fixture_kv):
    """Property test (seeded): random formulations with any unknown ingredient are never 'no notable interaction'."""
    pool = ["TEST_BASE_WATER", "TEST_ACTIVE_A", "TEST_EXFOLIANT_B", "TEST_STRONG_C", "TEST_HUMECTANT_E", "Mystery Root", "Odd Extract"]
    rng = random.Random(20261103)
    for _ in range(300):
        ta = ", ".join(rng.sample(pool, rng.randint(1, 4)))
        tb = ", ".join(rng.sample(pool, rng.randint(1, 4)))
        r = evaluate(make_formulation(ta, "A"), make_formulation(tb, "B"), fixture_kv)
        if r.ingredients.unresolved_a or r.ingredients.unresolved_b:
            assert r.status != CompatibilityStatus.NO_NOTABLE_INTERACTION
        assert 0.0 <= r.confidence <= 1.0
        assert evaluate(make_formulation(tb, "B"), make_formulation(ta, "A"), fixture_kv).status == r.status


def test_routine_pairwise(make_formulation, fixture_kv):
    items = [make_formulation(t, n) for t, n in [("TEST_ACTIVE_A", "A"), ("TEST_EXFOLIANT_B", "B"), ("TEST_BASE_WATER", "C")]]
    pairs = evaluate_routine(items, fixture_kv)
    assert [(i, j) for i, j, _ in pairs] == [(0, 1), (0, 2), (1, 2)]
    assert pairs[0][2].status == CompatibilityStatus.CAUTION


def test_fixture_knowledge_refused_by_real_loader(tmp_path):
    from tests.conftest import FIXTURES

    with pytest.raises(KnowledgeLoadError, match="fixture"):
        load_knowledge_dir(FIXTURES / "knowledge", "kv")


def test_fixture_source_type_refused_even_without_header():
    with pytest.raises(KnowledgeLoadError):
        build_knowledge_version(
            "kv", [], [{"id": "E1", "claim": "x", "source_type": "fixture", "citation": "abc", "strength": "high"}]
        )


def test_rule_without_existing_evidence_is_rejected():
    rule = {
        "code": "R1", "interaction_type": "redundancy", "severity": "caution",
        "side_a": [{"ingredient": "x"}], "side_b": [{"ingredient": "y"}],
        "mechanism_summary": "m", "practical_guidance": "g", "explanation_template": "t",
        "evidence_ids": ["MISSING"],
    }
    with pytest.raises(KnowledgeLoadError, match="missing evidence"):
        build_knowledge_version("kv", [rule], [])


def test_rule_with_no_evidence_list_is_rejected():
    rule = {
        "code": "R1", "interaction_type": "redundancy", "severity": "caution",
        "side_a": [{"ingredient": "x"}], "side_b": [{"ingredient": "y"}],
        "mechanism_summary": "m", "practical_guidance": "g", "explanation_template": "t", "evidence_ids": [],
    }
    with pytest.raises(KnowledgeLoadError):
        build_knowledge_version("kv", [rule], [])


def test_explanation_template_rejects_unknown_placeholders():
    rule = {
        "code": "R1", "interaction_type": "redundancy", "severity": "caution",
        "side_a": [{"ingredient": "x"}], "side_b": [{"ingredient": "y"}],
        "mechanism_summary": "m", "practical_guidance": "g", "explanation_template": "{__class__}",
        "evidence_ids": ["E1"],
    }
    ev = [{"id": "E1", "claim": "c", "source_type": "peer_reviewed", "citation": "Real citation", "strength": "high"}]
    with pytest.raises(KnowledgeLoadError):
        build_knowledge_version("kv", [rule], ev)


def test_shipped_real_knowledge_loads_and_every_rule_is_still_draft():
    from pathlib import Path

    kv = load_knowledge_dir(Path(__file__).parents[3] / "knowledge", "kv-1")
    assert not kv.is_demo and all(r.review_status == "draft" for r in kv.rules)


def test_max_position_condition(master, fixture_kv):
    from skinsync.domain.ingredients import normalize_list
    from skinsync.domain.knowledge import Term

    ings = normalize_list("TEST_BASE_WATER, TEST_HUMECTANT_E, TEST_ACTIVE_A", master)
    from skinsync.domain.compatibility import _side_hits

    assert _side_hits((Term(ingredient="test-active-a", max_position=2),), tuple(ings)) == []
    assert len(_side_hits((Term(ingredient="test-active-a", max_position=3),), tuple(ings))) == 1
    assert Severity.CAUTION  # keep import used


def test_is_conclusive_only_for_rules_with_high_or_moderate_evidence(make_formulation, fixture_kv):
    a = make_formulation("TEST_ACTIVE_A, Mystery Root", "A")
    b = make_formulation("TEST_EXFOLIANT_B", "B")
    r = evaluate(a, b, fixture_kv)
    by_type = {f.type: f for f in r.findings}
    assert by_type[FindingType.RULE].is_conclusive  # moderate evidence
    assert not by_type[FindingType.UNRESOLVED].is_conclusive
    strong = evaluate(make_formulation("TEST_STRONG_C", "A"), make_formulation("TEST_STRONG_D", "B"), fixture_kv)
    assert not next(f for f in strong.findings if f.type == FindingType.RULE).is_conclusive  # limited evidence
