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
    + [IngredientRecord(id=n.lower().replace(" ", "-"), inci_name=n, source="t")
       for n in ("AQUA", "GLYCERIN", "NIACINAMIDE", "SODIUM HYALURONATE", "FERULIC ACID", "PANTHENOL", "CERAMIDE NP")])


def form(text, name):
    return FormulationInput(product_id=name, product_version_id=name, product_name=name, version_label="v1",
                            ingredients=tuple(normalize_list(text, MASTER)))


def rules_fired(a, b):
    return sorted(f.rule_code for f in evaluate(form(a, "A"), form(b, "B"), KV).findings if f.type == FindingType.RULE)


def test_draft_rules_load_with_evidence_and_are_all_draft():
    assert len(KV.rules) == 7 and len(KV.evidence) == 10 and not KV.is_demo
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


# ---- rules added from the team CSV (2026-11-24)
def test_r0005_retinoids_with_aha():
    for ret in ("Retinol", "Retinal", "Retinaldehyde", "Tretinoin", "Adapalene", "Tazarotene"):
        assert "R-0005" in rules_fired(f"Aqua, {ret}", "Aqua, Glycolic Acid"), ret
    assert "R-0005" in rules_fired("Aqua, Mandelic Acid", "Aqua, Retinol")  # symmetric
    r = evaluate(form("Aqua, Retinol", "A"), form("Aqua, Lactic Acid", "B"), KV)
    assert r.status == CompatibilityStatus.CAUTION


def test_r0005_ignores_low_level_lactic_acid():
    late = "Aqua, " + ", ".join(f"Filler{i}" for i in range(12)) + ", Lactic Acid"
    assert "R-0005" not in rules_fired("Aqua, Retinol", late)


def test_r0006_other_retinoids_with_salicylic_acid_without_duplicating_r0002_r0003():
    assert rules_fired("Aqua, Retinol", "Aqua, Salicylic Acid") == ["R-0006"]
    assert "R-0006" not in rules_fired("Aqua, Tretinoin", "Aqua, Salicylic Acid")  # R-0003 covers it
    assert "R-0006" not in rules_fired("Aqua, Adapalene", "Aqua, Salicylic Acid")  # R-0002 covers it


def test_r0007_dapsone_with_benzoyl_peroxide_is_info_only():
    r = evaluate(form("Aqua, Dapsone", "A"), form("Aqua, Benzoyl Peroxide", "B"), KV)
    assert [f.rule_code for f in r.findings if f.type == FindingType.RULE] == ["R-0007"]
    assert r.status == CompatibilityStatus.NO_NOTABLE_INTERACTION  # info does not change the headline


def test_csv_compatible_pairs_raise_no_rule():
    """Pairs the CSV marks COMPATIBLE must not be flagged by any rule."""
    for a, b in [("Niacinamide", "Ascorbic Acid"), ("Niacinamide", "Retinol"), ("Sodium Hyaluronate", "Retinol"),
                 ("Ascorbic Acid", "Ferulic Acid"), ("Azelaic Acid", "Niacinamide"), ("Panthenol", "Retinol"),
                 ("Ceramide NP", "Glycolic Acid")]:
        fa, fb = form(f"Aqua, {a}", "A"), form(f"Aqua, {b}", "B")
        assert all(i.resolved for i in (*fa.ingredients, *fb.ingredients)), (a, b)  # the test is meaningful
        assert rules_fired(f"Aqua, {a}", f"Aqua, {b}") == [], (a, b)


def test_qualifying_evidence_is_recorded_but_not_cited_as_support():
    assert "EV-0008" in KV.evidence and not any("EV-0008" in r.evidence_ids for r in KV.rules)


# ---- pending CSV rows written in the rule format (knowledge/review/pending-rules.yaml, not loaded by the app)
def test_pending_rules_file_is_valid_rule_format_and_unpublishable():
    from skinsync.domain.knowledge import build_knowledge_version

    doc = yaml.safe_load((KNOWLEDGE / "review" / "pending-rules.yaml").read_text())
    kv = build_knowledge_version("pending-check", doc["rules"], doc["evidence"])  # same validation as rules.yaml
    assert len(kv.rules) == 24
    assert {r.review_status for r in kv.rules} == {"draft"}
    assert {e.strength.value for e in kv.evidence.values()} == {"insufficient"}  # publish_blockers refuses these
    assert not {r.code for r in kv.rules} & {r.code for r in KV.rules}  # P- codes never clash with R- codes
    # once promoted, a pending rule matches real labels (vitamin C + kojic acid, CSV row 66)
    fired = [f.rule_code for f in evaluate(form("Aqua, L-Ascorbic Acid", "A"), form("Aqua, Kojic Acid", "B"), kv).findings
             if f.type == FindingType.RULE]
    assert len(fired) == 1 and fired[0].startswith("P-")


def test_app_loads_only_rules_yaml_not_pending():
    assert not any(r.code.startswith("P-") for r in KV.rules)
