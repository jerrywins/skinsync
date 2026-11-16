"""FR-03 / US-003: ingredient normalization. Unknown stays unknown."""

from skinsync.domain.enums import NormalizationMethod, ReviewStatus
from skinsync.domain.ingredients import normalize_key, normalize_list, parse_ingredient_list


def test_fr03_parse_preserves_order_and_strips_prefix():
    entries = parse_ingredient_list("Ingredients: TEST_BASE_WATER, TEST_ACTIVE_A*, TEST_HUMECTANT_E.")
    assert [e.position for e in entries] == [1, 2, 3]
    assert [e.cleaned for e in entries] == ["test_base_water".replace("_", " "), "test active a", "test humectant e"]


def test_fr03_commas_inside_parentheses_do_not_split():
    entries = parse_ingredient_list("TEST_BASE_WATER (test water, purified), TEST_ACTIVE_A")
    assert len(entries) == 2


def test_fr03_may_contain_section_is_marked():
    entries = parse_ingredient_list("TEST_BASE_WATER, TEST_ACTIVE_A, [+/- TEST_HUMECTANT_E]")
    assert entries[-1].stated_role == "may_contain"
    assert entries[0].stated_role == "listed"


def test_fr03_concentration_is_captured():
    (e,) = parse_ingredient_list("TEST_ACTIVE_A 10%")
    assert e.concentration_pct == 10.0 and e.cleaned == "test active a"


def test_fr03_exact_and_alias_match(master):
    out = normalize_list("TEST AQUA, test active alpha", master)
    assert [o.canonical_id for o in out] == ["test-base-water", "test-active-a"]
    assert all(o.method == NormalizationMethod.EXACT and o.confidence == 1.0 for o in out)


def test_fr03_component_match_for_parenthetical(master):
    (o,) = normalize_list("Unknownword (TEST_ACTIVE_A)", master)
    assert o.canonical_id == "test-active-a" and o.method == NormalizationMethod.ALIAS_COMPONENT


def test_fr03_fuzzy_similarity_only_suggests_never_resolves(master):
    (o,) = normalize_list("TEST_ACTIVE_AA", master)
    assert not o.resolved and o.method == NormalizationMethod.UNRESOLVED
    assert o.review_status == ReviewStatus.NEEDS_REVIEW
    assert o.candidate == "TEST_ACTIVE_A" and o.candidate_id == "test-active-a" and o.candidate_score >= 0.85


def test_fr03_no_suggestion_when_numbers_differ():
    from skinsync.domain.ingredients import IngredientMaster, IngredientRecord

    m = IngredientMaster.from_records([IngredientRecord(id="pg4", inci_name="POLYGLYCERYL-4 CAPRATE", source="t")])
    (o,) = normalize_list("polyglyceryl-2 caprate", m)
    assert not o.resolved and o.candidate is None  # chemically different; never suggested


def test_parser_drops_entries_without_letters():
    assert [e.cleaned for e in parse_ingredient_list("TEST_ACTIVE_A, 1, (2), TEST_BASE_WATER")] == [
        "test active a", "test base water"]


def test_c05_unknown_ingredient_stays_unresolved(master):
    (o,) = normalize_list("Completely Unknown Extract", master)
    assert o.canonical_id is None and not o.resolved
    assert o.method == NormalizationMethod.UNRESOLVED and o.confidence == 0.0


def test_fr03_slash_names_resolve_to_first_name_with_review(master):
    """Labels write 'INCI / common name'. The first-written name is used, flagged for review."""
    (o,) = normalize_list("TEST_ACTIVE_A/TEST_HUMECTANT_E", master)
    assert o.canonical_id == "test-active-a" and o.confidence == 0.8
    assert o.review_status == ReviewStatus.NEEDS_REVIEW and o.candidate == "test-active-a, test-humectant-e"


def test_fr03_ambiguous_components_without_first_match_stay_unresolved(master):
    (o,) = normalize_list("Unknown Thing / TEST_ACTIVE_A / TEST_HUMECTANT_E", master)
    assert not o.resolved


def test_normalize_key_strips_accents_and_case():
    assert normalize_key("  Crème  Ëxtract ") == "creme extract"


def test_empty_list_parses_to_nothing():
    assert parse_ingredient_list("") == [] and parse_ingredient_list("   ") == []
