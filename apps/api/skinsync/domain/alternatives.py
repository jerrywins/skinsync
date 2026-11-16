"""Alternatives engine (SkinSync §12.4, FR-14/15/16, SC-03).

Pipeline: features -> candidates -> dedupe -> hard filters -> per-dimension scores
-> weighted rank -> visible reasons. Pure and deterministic.

Weights are product-design parameters, not science (SkinIQ §46). Dimensions that
cannot be computed (no key actives, no preferences) are reported as unavailable and
excluded, and the remaining weights are renormalised, so a missing signal never
counts as a match.

Prices: only FRESH observations in the same currency are compared. Stale or
missing prices are shown with their state, never filled in. "Cheaper"/"premium"
modes exclude candidates whose price cannot be compared, and say how many.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_WEIGHTS = {
    "ingredient_similarity": 0.35,
    "target_match": 0.20,
    "category_match": 0.15,
    "preference_match": 0.15,
    "formulation_similarity": 0.15,
}
FRESH_DAYS = 30
STALE_DAYS = 120
MIN_SIMILARITY_FOR_CHEAPER = 0.3  # "cheaper while maintaining meaningful similarity"


class Mode(str, Enum):
    SIMILAR = "similar"
    CHEAPER = "cheaper"
    PREMIUM = "premium"
    INGREDIENT_FOCUSED = "ingredient_focused"
    ROUTINE_COMPATIBLE = "routine_compatible"
    SENSITIVE_PREFERENCE = "sensitive_preference"


class PriceState(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


class PriceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    seller: str
    source: str
    observed_at: date
    available: bool = True


class ProductFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str
    name: str
    brand: str
    category: str
    category_parent: str | None = None
    barcode: str | None = None
    ingredient_ids: tuple[str, ...] = ()  # resolved canonical ids, in label order
    key_actives: tuple[str, ...] = ()
    function_classes: tuple[str, ...] = ()
    completeness: float = Field(ge=0, le=1, default=0.0)
    identification_confidence: float = Field(ge=0, le=1, default=1.0)
    price: PriceObservation | None = None


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    avoid_ingredients: frozenset[str] = frozenset()
    avoid_brands: frozenset[str] = frozenset()
    preferred_brands: frozenset[str] = frozenset()
    target_ingredients: frozenset[str] = frozenset()
    exclude_product_ids: frozenset[str] = frozenset()
    currency: str = "INR"


class Dimension(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    score: float | None  # None = not computable, excluded from the total
    detail: str


class RankedAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str
    name: str
    brand: str
    rank: int
    score: float
    dimensions: tuple[Dimension, ...]
    reasons: tuple[str, ...]
    differences: tuple[str, ...]
    price_state: PriceState
    price: PriceObservation | None
    price_delta_pct: float | None
    data_confidence: float
    missing_data: tuple[str, ...]


class AlternativesResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: str
    mode: Mode
    results: tuple[RankedAlternative, ...]
    excluded: dict[str, int]  # reason -> count, so filtering is visible
    reference_price_state: PriceState
    low_identification_confidence: bool
    weights: dict[str, float]


def price_state(p: PriceObservation | None, today: date) -> PriceState:
    if p is None or not p.available:
        return PriceState.UNAVAILABLE
    age = (today - p.observed_at).days
    if age <= FRESH_DAYS:
        return PriceState.FRESH
    if age <= STALE_DAYS:
        return PriceState.STALE
    return PriceState.UNAVAILABLE


def _position_weights(ids: tuple[str, ...]) -> dict[str, float]:
    """Earlier ingredients weigh more (label order roughly tracks amount). Design parameter."""
    out: dict[str, float] = {}
    for pos, i in enumerate(ids):
        out.setdefault(i, 1.0 / (1.0 + pos / 5.0))
    return out


def weighted_overlap(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Position-weighted Jaccard (sum of min weights / sum of max weights)."""
    wa, wb = _position_weights(a), _position_weights(b)
    keys = set(wa) | set(wb)
    if not keys:
        return 0.0
    num = sum(min(wa.get(k, 0), wb.get(k, 0)) for k in keys)
    den = sum(max(wa.get(k, 0), wb.get(k, 0)) for k in keys)
    return num / den


def _jaccard(a, b) -> float | None:
    a, b = set(a), set(b)
    if not a and not b:
        return None
    return len(a & b) / len(a | b)


def rank_alternatives(
    ref: ProductFeatures,
    candidates: list[ProductFeatures],
    mode: Mode,
    *,
    today: date,
    prefs: Preferences | None = None,
    routine_conflicts: frozenset[str] = frozenset(),  # candidate ids that conflict with the routine
    weights: dict[str, float] | None = None,
    limit: int = 20,
) -> AlternativesResult:
    weights = dict(weights or DEFAULT_WEIGHTS)
    prefs = prefs or Preferences()
    excluded: dict[str, int] = {}

    def drop(reason: str):
        excluded[reason] = excluded.get(reason, 0) + 1

    ref_state = price_state(ref.price, today)
    targets = prefs.target_ingredients or frozenset(ref.key_actives)
    seen_ids, seen_barcodes = {ref.product_id}, {ref.barcode} if ref.barcode else set()
    scored: list[tuple[float, str, RankedAlternative]] = []

    for c in sorted(candidates, key=lambda x: x.product_id):
        # ---- hard filters --------------------------------------------------
        if c.product_id in seen_ids or (c.barcode and c.barcode in seen_barcodes):
            drop("duplicate_or_reference")
            continue
        seen_ids.add(c.product_id)
        if c.barcode:
            seen_barcodes.add(c.barcode)
        if c.product_id in prefs.exclude_product_ids:
            drop("user_excluded")
            continue
        if not c.ingredient_ids:
            drop("missing_ingredient_data")
            continue
        if c.category != ref.category and not (c.category_parent and c.category_parent == ref.category_parent):
            drop("different_category")
            continue
        if c.brand.lower() in {b.lower() for b in prefs.avoid_brands}:
            drop("avoided_brand")
            continue
        hit_avoid = sorted(set(c.ingredient_ids) & prefs.avoid_ingredients)
        if hit_avoid:
            drop("contains_avoided_ingredient")
            continue
        if mode == Mode.ROUTINE_COMPATIBLE and c.product_id in routine_conflicts:
            drop("conflicts_with_routine")
            continue

        c_state = price_state(c.price, today)
        comparable = (
            ref_state == PriceState.FRESH
            and c_state == PriceState.FRESH
            and ref.price.currency == c.price.currency
        )
        delta = round((c.price.amount - ref.price.amount) / ref.price.amount * 100, 1) if comparable else None
        if mode in (Mode.CHEAPER, Mode.PREMIUM):
            if delta is None:
                drop("price_not_comparable")
                continue
            if mode == Mode.CHEAPER and delta >= 0:
                drop("not_cheaper")
                continue
            if mode == Mode.PREMIUM and delta <= 0:
                drop("not_premium")
                continue

        # ---- dimensions ----------------------------------------------------
        ing_sim = weighted_overlap(ref.ingredient_ids, c.ingredient_ids)
        target = None
        if targets:
            target = len(targets & set(c.ingredient_ids)) / len(targets)
        if mode == Mode.INGREDIENT_FOCUSED and not target:
            drop("missing_target_ingredients")
            continue
        cat = 1.0 if c.category == ref.category else 0.5
        form_sim = _jaccard(ref.function_classes, c.function_classes)
        pref = None
        if prefs.preferred_brands:
            pref = 1.0 if c.brand.lower() in {b.lower() for b in prefs.preferred_brands} else 0.0

        dims = (
            Dimension(name="ingredient_similarity", score=round(ing_sim, 4),
                      detail=f"{round(ing_sim * 100)}% position-weighted ingredient overlap"),
            Dimension(name="target_match", score=None if target is None else round(target, 4),
                      detail="no target ingredients known" if target is None
                      else f"{len(targets & set(c.ingredient_ids))} of {len(targets)} target ingredients"),
            Dimension(name="category_match", score=cat,
                      detail="same category" if cat == 1.0 else "related category"),
            Dimension(name="preference_match", score=pref,
                      detail="no brand preferences set" if pref is None
                      else ("preferred brand" if pref else "not a preferred brand")),
            Dimension(name="formulation_similarity", score=None if form_sim is None else round(form_sim, 4),
                      detail="function classes unknown" if form_sim is None
                      else f"{round(form_sim * 100)}% shared function classes"),
        )
        avail = [d for d in dims if d.score is not None]
        wsum = sum(weights[d.name] for d in avail)
        score = round(sum(weights[d.name] * d.score for d in avail) / wsum, 4) if wsum else 0.0
        if mode == Mode.CHEAPER and ing_sim < MIN_SIMILARITY_FOR_CHEAPER:
            drop("too_dissimilar")
            continue

        reasons = [f"{round(ing_sim * 100)}% ingredient-profile similarity"]
        if delta is not None:
            reasons.append(f"{abs(delta)}% {'lower' if delta < 0 else 'higher'} observed price")
        reasons.append("Same product category" if cat == 1.0 else "Related category")
        if target:
            reasons.append(f"Contains {len(targets & set(c.ingredient_ids))} of {len(targets)} target ingredients")
        if mode == Mode.ROUTINE_COMPATIBLE:
            reasons.append("No conflict found with your routine in the current knowledge base")

        only_ref = sorted(set(ref.ingredient_ids) - set(c.ingredient_ids))
        only_c = sorted(set(c.ingredient_ids) - set(ref.ingredient_ids))
        differences = []
        if only_ref:
            differences.append(f"Lacks {len(only_ref)} ingredient(s) in your product")
        if only_c:
            differences.append(f"Has {len(only_c)} ingredient(s) your product does not")

        missing = []
        if c_state != PriceState.FRESH:
            missing.append("current price" if c_state == PriceState.UNAVAILABLE else "fresh price (observation is stale)")
        if c.completeness < 1:
            missing.append(f"{round((1 - c.completeness) * 100)}% of ingredients unrecognised")
        for d in dims:
            if d.score is None:
                missing.append(d.detail)

        data_conf = round(min(c.completeness, ref.completeness, ref.identification_confidence), 4)
        alt = RankedAlternative(
            product_id=c.product_id, name=c.name, brand=c.brand, rank=0, score=score,
            dimensions=dims, reasons=tuple(reasons), differences=tuple(differences),
            price_state=c_state, price=c.price if c_state != PriceState.UNAVAILABLE else None,
            price_delta_pct=delta, data_confidence=data_conf, missing_data=tuple(missing),
        )
        # sort key: score desc, then for cheaper the bigger saving, then id for stability
        tiebreak = delta if (mode == Mode.CHEAPER and delta is not None) else 0.0
        scored.append((-score, f"{tiebreak:+012.3f}|{c.product_id}", alt))

    scored.sort(key=lambda t: (t[0], t[1]))
    results = tuple(
        alt.model_copy(update={"rank": i + 1}) for i, (_, _, alt) in enumerate(scored[:limit])
    )
    return AlternativesResult(
        reference_id=ref.product_id,
        mode=mode,
        results=results,
        excluded=dict(sorted(excluded.items())),
        reference_price_state=ref_state,
        low_identification_confidence=ref.identification_confidence < 0.85,
        weights=weights,
    )
