"""The shipped DRAFT rules (knowledge/*.yaml): they load, fire on the right pairs, respect position limits,
and stay unpublishable while marked draft. These test behaviour, not the science (that needs review)."""

from pathlib import Path

import yaml

from skinsync.domain.compatibility import FormulationInput, evaluate
from skinsync.domain.enums import CompatibilityStatus, FindingType
from skinsync.domain.ingredients import IngredientMaster, IngredientRecord, normalize_list
from skinsync.domain.knowledge import load_knowledge_dir

KNOWLEDGE = Path(__file__).parents[3] / "knowledge"
KV = load_knowledge_dir(KNOWLEDGE, "kv-draft-test")
MASTER = IngredientMaster.from_records(
    [IngredientRecord(id=e["id"], inci_name=e["inci_name"], aliases=tuple(e.get("aliases") or ()), source="t")
     for e in yaml.safe_load((KNOWLEDGE / "ingredients.yaml").read_text())["ingredients"]]
    + [IngredientRecord(id="aqua", inci_name="AQUA", source="t"), IngredientRecord(id="glycerin", inci_name="GLYCERIN", source="t")])


def form(text, name):
    return FormulationInput(product_id=name, product_version_id=name, product_name=name, version_label="v1",
                            ingredients=tuple(normalize_list(text, MASTER)))


def rules_fired(a, b):
    return sorted(f.rule_code for f in evaluate(form(a, "A"), form(b, "B"), KV).findings if f.type == FindingType.RULE)


def test_draft_rules_load_with_evidence_and_are_all_draft():
    assert len(KV.rules) == 4 and len(KV.evidence) == 5 and not KV.is_demo
    assert {r.review_status for r in KV.rules} == {"draft"}
    for r in KV.rules:
        assert all(KV.evidence[e].citation for e in r.evidence_ids)


def test_r0001_tretinoin_with_benzoyl_peroxide():
    assert rules_fired("Aqua, Tretinoin", "Aqua, Benzoyl Peroxide") == ["R-0001"]
    r = evaluate(form("Aqua, Retinoic Acid", "A"), form("Benzoyl Peroxide", "B"), KV)
    assert r.status == CompatibilityStatus.CAUTION  # alias resolves


def test_r0001_does_not_fire_for_adapalene():
    assert "R-0001" not in rules_fired("Aqua, Adapalene", "Aqua, Benzoyl Peroxide")


def test_r0002_two_acne_actives():
    assert rules_fired("Aqua, Adapalene", "Aqua, Benzoyl Peroxide") == ["R-0002"]


def test_r0002_ignores_low_level_salicylic_acid():
    late = "Aqua, " + ", ".join(["Glycerin"] * 0) + ", ".join(f"Filler{i}" for i in range(12)) + ", Salicylic Acid"
    assert "R-0002" not in rules_fired(late, "Aqua, Benzoyl Peroxide")


def test_r0003_tretinoin_with_salicylic_acid_or_sulfur():
    assert "R-0003" in rules_fired("Aqua, Tretinoin", "Aqua, Salicylic Acid")
    assert "R-0003" in rules_fired("Aqua, Tretinoin", "Aqua, Sulphur")


def test_r0004_is_an_info_note_that_does_not_change_the_headline():
    r = evaluate(form("Aqua, Glycolic Acid", "A"), form("Aqua, Lactic Acid", "B"), KV)
    assert [f.rule_code for f in r.findings if f.type == FindingType.RULE] == ["R-0004"]
    assert r.status == CompatibilityStatus.NO_NOTABLE_INTERACTION


def test_r0004_ignores_acids_far_down_the_list():
    late = "Aqua, Glycerin, " + ", ".join(f"Filler{i}" for i in range(6)) + ", Lactic Acid"
    assert "R-0004" not in rules_fired(late, "Aqua, Glycolic Acid")


def test_unrelated_products_have_no_rule_findings():
    assert rules_fired("Aqua, Glycerin", "Aqua, Glycerin") == []
