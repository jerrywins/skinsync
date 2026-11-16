"""Skin analysis: model adapter contract, labelled mock adapter, concern mapping.

Perception (the adapter) is separated from recommendation (the mapping table) so a
model can never invent a product (SkinIQ §18). Observation vocabulary is cosmetic
only: no condition names (acne, rosacea, melasma, eczema...) appear anywhere.
"""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import ConfidenceLevel, EvidenceStrength, confidence_level
from .knowledge import EvidenceRecord, KnowledgeLoadError

# Supported cosmetic observations. Names deliberately describe appearance, not conditions.
OBSERVATION_VOCABULARY = (
    "visible_shine",
    "visible_pores",
    "fine_lines_appearance",
    "uneven_tone_appearance",
    "dark_spots_appearance",
    "visible_redness",
    "under_eye_darkness",
    "visible_blemishes",
    "visible_texture",
    "visible_dryness",
)
FORBIDDEN_TERMS = ("acne", "rosacea", "melasma", "eczema", "dermatitis", "psoriasis", "diagnos", "disease")
LOW_CONFIDENCE = 0.5  # below this, an observation is shown as low confidence and not mapped

MEDICAL_BOUNDARY = (
    "These are estimates of visible cosmetic features based on one photo. Lighting, camera quality, "
    "makeup, filters and angle all affect them. This is not a medical diagnosis and offers no "
    "treatment. For persistent or concerning skin issues, consult a qualified professional."
)


class SkinType(str, Enum):
    DRY = "dry"
    OILY = "oily"
    COMBINATION = "combination"
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    UNSURE = "unsure"


class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    PRONOUNCED = "pronounced"


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    characteristic: str
    confidence: float = Field(ge=0, le=1)
    severity: Severity

    @field_validator("characteristic")
    @classmethod
    def _supported(cls, v: str) -> str:
        if v not in OBSERVATION_VOCABULARY:
            raise ValueError(f"unsupported observation {v!r}")
        return v


class ModelOutput(BaseModel):
    """What every adapter must return. Validated before domain logic sees it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observations: tuple[Observation, ...]
    model_version: str = Field(min_length=1, max_length=80)
    is_demo: bool
    label: str | None = Field(default=None, max_length=120)  # shown with every result, e.g. "not validated"


class SkinModelAdapter(ABC):
    @abstractmethod
    def analyze(self, jpeg_bytes: bytes) -> ModelOutput: ...


class MockSkinModelAdapter(SkinModelAdapter):
    """DEMO ONLY. Deterministic pseudo-observations seeded from the image hash.

    It does not look at skin at all. Every output is flagged is_demo=True and the UI
    labels it "Demo model - not a real analysis".
    """

    MODEL_VERSION = "mock-0.1"

    def analyze(self, jpeg_bytes: bytes) -> ModelOutput:
        seed = int(hashlib.sha256(jpeg_bytes).hexdigest()[:16], 16)
        rng = random.Random(seed)
        picks = rng.sample(OBSERVATION_VOCABULARY, rng.randint(1, 4))
        obs = tuple(
            Observation(
                characteristic=c,
                confidence=round(rng.uniform(0.3, 0.95), 2),
                severity=rng.choice(list(Severity)),
            )
            for c in sorted(picks)
        )
        return ModelOutput(observations=obs, model_version=self.MODEL_VERSION, is_demo=True,
                           label="Demo model — not a real analysis")


class UnavailableSkinModelAdapter(SkinModelAdapter):
    """Used when no model is configured: analysis is reported unavailable, never faked."""

    def analyze(self, jpeg_bytes: bytes) -> ModelOutput:
        raise RuntimeError("ANALYSIS_UNAVAILABLE")


def get_adapter(name: str) -> SkinModelAdapter:
    if name == "mock":
        return MockSkinModelAdapter()
    if name == "heuristic":
        from .skin_heuristics import HeuristicSkinAdapter

        return HeuristicSkinAdapter()
    if name in ("", "none"):
        return UnavailableSkinModelAdapter()
    raise ValueError(f"unknown skin model adapter {name!r}")


# ---- concern mapping (team-reviewed table) --------------------------------------


class ConcernMapping(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation: str
    concern_category: str = Field(min_length=1, max_length=120)
    ingredient_classes: tuple[str, ...] = Field(min_length=1)
    intended_role: str = Field(min_length=1, max_length=500)
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    notes: str | None = None

    @field_validator("observation")
    @classmethod
    def _vocab(cls, v):
        if v not in OBSERVATION_VOCABULARY:
            raise ValueError(f"mapping for unsupported observation {v!r}")
        return v

    @field_validator("concern_category", "intended_role")
    @classmethod
    def _no_medical(cls, v):
        low = v.lower()
        if any(t in low for t in FORBIDDEN_TERMS):
            raise ValueError("mapping text must not name medical conditions or diagnoses")
        return v


def build_concern_map(mappings: list[dict], evidence: dict[str, EvidenceRecord]) -> tuple[ConcernMapping, ...]:
    out = []
    for m in mappings:
        try:
            cm = ConcernMapping(**m)
        except Exception as exc:
            raise KnowledgeLoadError(str(exc)) from exc
        missing = [e for e in cm.evidence_ids if e not in evidence]
        if missing:
            raise KnowledgeLoadError(f"concern mapping for {cm.observation} cites missing evidence {missing}")
        out.append(cm)
    return tuple(sorted(out, key=lambda c: (c.observation, c.concern_category)))


class ObservationView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    characteristic: str
    label: str
    confidence: float
    confidence_level: ConfidenceLevel
    severity: Severity
    low_confidence: bool


class ConcernRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation: str
    concern_category: str
    ingredient_classes: tuple[str, ...]
    intended_role: str
    observation_confidence: float          # perception confidence
    evidence_strength: EvidenceStrength    # science behind the mapping (separate!)
    evidence_ids: tuple[str, ...]


class SkinResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    skin_type: SkinType
    observations: tuple[ObservationView, ...]
    recommendations: tuple[ConcernRecommendation, ...]
    unmapped_observations: tuple[str, ...]  # supported observation with no reviewed mapping yet
    model_version: str
    is_demo_model: bool
    medical_boundary: str = MEDICAL_BOUNDARY


_STRENGTH_ORDER = [EvidenceStrength.HIGH, EvidenceStrength.MODERATE, EvidenceStrength.LIMITED,
                   EvidenceStrength.INSUFFICIENT, EvidenceStrength.UNKNOWN]


def label_for(characteristic: str) -> str:
    return characteristic.replace("_appearance", "").replace("_", " ").capitalize()


def map_concerns(
    output: ModelOutput,
    skin_type: SkinType,
    mappings: tuple[ConcernMapping, ...],
    evidence: dict[str, EvidenceRecord],
) -> SkinResult:
    views, recs, unmapped = [], [], []
    for o in sorted(output.observations, key=lambda o: (-o.confidence, o.characteristic)):
        low = o.confidence < LOW_CONFIDENCE
        views.append(ObservationView(
            characteristic=o.characteristic, label=label_for(o.characteristic), confidence=o.confidence,
            confidence_level=confidence_level(o.confidence), severity=o.severity, low_confidence=low,
        ))
        if low:
            continue  # low-confidence observations are shown, never acted on
        ms = [m for m in mappings if m.observation == o.characteristic]
        if not ms:
            unmapped.append(o.characteristic)
        for m in ms:
            strengths = [evidence[e].strength for e in m.evidence_ids]
            best = min(strengths, key=_STRENGTH_ORDER.index)
            recs.append(ConcernRecommendation(
                observation=o.characteristic, concern_category=m.concern_category,
                ingredient_classes=m.ingredient_classes, intended_role=m.intended_role,
                observation_confidence=o.confidence, evidence_strength=best, evidence_ids=m.evidence_ids,
            ))
    return SkinResult(
        skin_type=skin_type, observations=tuple(views), recommendations=tuple(recs),
        unmapped_observations=tuple(unmapped), model_version=output.model_version, is_demo_model=output.is_demo,
    )
