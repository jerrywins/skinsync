"""FR-14/15/16, SC-03: alternatives ranking. Prices are never invented."""

from datetime import date, timedelta

from skinsync.domain.alternatives import (
    Mode,
    Preferences,
    PriceObservation,
    PriceState,
    ProductFeatures,
    rank_alternatives,
    weighted_overlap,
)

TODAY = date(2026, 11, 3)


def price(amount, days_ago=1, currency="INR"):
    return PriceObservation(amount=amount, currency=currency, seller="Seller X", source="fixture",
                            observed_at=TODAY - timedelta(days=days_ago))


def feat(pid, ids, cat="serum", brand="Brand", p=None, keys=(), fcs=(), barcode=None, completeness=1.0):
    return ProductFeatures(product_id=pid, name=pid.upper(), brand=brand, category=cat, barcode=barcode,
                           ingredient_ids=tuple(ids), key_actives=tuple(keys), function_classes=tuple(fcs),
                           completeness=completeness, price=p)


REF = feat("ref", ["w", "a", "b", "c"], p=price(1000), keys=("a",), fcs=("x", "y"), barcode="111")


def test_fr14_similar_ranks_closest_formula_first():
    close = feat("close", ["w", "a", "b"], fcs=("x", "y"))
    far = feat("far", ["w", "z"], fcs=("q",))
    r = rank_alternatives(REF, [far, close], Mode.SIMILAR, today=TODAY)
    assert [x.product_id for x in r.results] == ["close", "far"]
    assert r.results[0].rank == 1 and r.results[0].reasons


def test_reference_and_duplicates_are_removed():
    dup_barcode = feat("other-id", ["w", "a"], barcode="111")
    r = rank_alternatives(REF, [REF, dup_barcode, feat("ok", ["w"])], Mode.SIMILAR, today=TODAY)
    assert [x.product_id for x in r.results] == ["ok"]
    assert r.excluded["duplicate_or_reference"] == 2


def test_fr15_cheaper_requires_fresh_comparable_price_and_lower_amount():
    cheaper = feat("cheap", ["w", "a", "b"], p=price(600))
    pricier = feat("dear", ["w", "a", "b"], p=price(1500))
    no_price = feat("noprice", ["w", "a", "b"])
    stale = feat("stale", ["w", "a", "b"], p=price(500, days_ago=60))
    r = rank_alternatives(REF, [cheaper, pricier, no_price, stale], Mode.CHEAPER, today=TODAY)
    assert [x.product_id for x in r.results] == ["cheap"]
    assert r.results[0].price_delta_pct == -40.0
    assert "40.0% lower observed price" in r.results[0].reasons
    assert r.excluded == {"not_cheaper": 1, "price_not_comparable": 2}


def test_no_cheaper_alternatives_returns_empty_with_reasons():
    r = rank_alternatives(REF, [feat("dear", ["w", "a"], p=price(2000))], Mode.CHEAPER, today=TODAY)
    assert r.results == () and r.excluded == {"not_cheaper": 1}


def test_fr15_premium_mode():
    r = rank_alternatives(REF, [feat("dear", ["w", "a"], p=price(2000))], Mode.PREMIUM, today=TODAY)
    assert r.results[0].price_delta_pct == 100.0


def test_missing_price_is_shown_unavailable_never_invented():
    r = rank_alternatives(REF, [feat("noprice", ["w", "a"])], Mode.SIMILAR, today=TODAY)
    (alt,) = r.results
    assert alt.price is None and alt.price_state == PriceState.UNAVAILABLE and alt.price_delta_pct is None
    assert "current price" in alt.missing_data


def test_stale_price_is_flagged():
    r = rank_alternatives(REF, [feat("s", ["w", "a"], p=price(900, days_ago=60))], Mode.SIMILAR, today=TODAY)
    assert r.results[0].price_state == PriceState.STALE and r.results[0].price_delta_pct is None


def test_currency_mismatch_is_not_compared():
    r = rank_alternatives(REF, [feat("usd", ["w", "a"], p=price(5, currency="USD"))], Mode.CHEAPER, today=TODAY)
    assert r.results == () and r.excluded == {"price_not_comparable": 1}


def test_hard_filters_category_avoid_ingredient_missing_data():
    prefs = Preferences(avoid_ingredients=frozenset({"z"}), avoid_brands=frozenset({"BadBrand"}))
    cands = [feat("cat", ["w"], cat="cleanser"), feat("avoid", ["w", "z"]), feat("empty", []),
             feat("brand", ["w"], brand="badbrand")]
    r = rank_alternatives(REF, cands, Mode.SIMILAR, today=TODAY, prefs=prefs)
    assert r.results == ()
    assert r.excluded == {"avoided_brand": 1, "contains_avoided_ingredient": 1,
                          "different_category": 1, "missing_ingredient_data": 1}


def test_fr16_routine_compatible_drops_conflicts():
    r = rank_alternatives(REF, [feat("c1", ["w"]), feat("c2", ["w"])], Mode.ROUTINE_COMPATIBLE,
                          today=TODAY, routine_conflicts=frozenset({"c1"}))
    assert [x.product_id for x in r.results] == ["c2"] and r.excluded == {"conflicts_with_routine": 1}


def test_ingredient_focused_requires_target():
    prefs = Preferences(target_ingredients=frozenset({"a"}))
    r = rank_alternatives(REF, [feat("has", ["a"]), feat("lacks", ["w"])], Mode.INGREDIENT_FOCUSED,
                          today=TODAY, prefs=prefs)
    assert [x.product_id for x in r.results] == ["has"]


def test_unavailable_dimensions_are_excluded_not_scored_as_zero():
    ref = feat("r", ["w", "a"])  # no key actives, no function classes
    r = rank_alternatives(ref, [feat("c", ["w", "a"])], Mode.SIMILAR, today=TODAY)
    alt = r.results[0]
    assert alt.score == 1.0  # ingredient 1.0 and category 1.0; the rest excluded and renormalised
    assert {d.name for d in alt.dimensions if d.score is None} == {"target_match", "preference_match",
                                                                   "formulation_similarity"}


def test_ranking_is_stable_and_deterministic():
    cands = [feat(f"c{i}", ["w", "a"]) for i in range(10)]
    r1 = rank_alternatives(REF, cands, Mode.SIMILAR, today=TODAY)
    r2 = rank_alternatives(REF, list(reversed(cands)), Mode.SIMILAR, today=TODAY)
    assert r1 == r2


def test_low_identification_confidence_is_flagged():
    ref = REF.model_copy(update={"identification_confidence": 0.5})
    assert rank_alternatives(ref, [], Mode.SIMILAR, today=TODAY).low_identification_confidence


def test_weighted_overlap_bounds():
    assert weighted_overlap(("a",), ("a",)) == 1.0
    assert weighted_overlap(("a",), ("b",)) == 0.0
    assert weighted_overlap((), ()) == 0.0
    assert weighted_overlap(("a", "b"), ("b", "a")) < 1.0  # order matters by design


def test_personalization_never_changes_compatibility(make_formulation, fixture_kv):
    """Spec §12.5: preferences re-rank alternatives; the compatibility engine has no preference input."""
    import inspect

    from skinsync.domain.compatibility import evaluate

    assert list(inspect.signature(evaluate).parameters) == ["a", "b", "kv"]
