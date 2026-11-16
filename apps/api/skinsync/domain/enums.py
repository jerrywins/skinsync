"""Controlled vocabularies shared by every pipeline.

These values are part of the API contract (spec SkinSync §22, SkinIQ §34, §41).
Changing one is a breaking change: bump ENGINE_VERSION and the API version.
"""

from enum import Enum

ENGINE_VERSION = "compat-engine-1.0.0"


class EvidenceStrength(str, Enum):
    """Strength of the scientific support for a claim. NOT model confidence."""

    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """How certain the system is about an identification or result.

    Distinct from EvidenceStrength (spec principle 1.2.3).
    """

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class Severity(str, Enum):
    INFO = "info"
    CAUTION = "caution"
    STRONG_CAUTION = "strong_caution"


class InteractionType(str, Enum):
    REDUNDANCY = "redundancy"
    IRRITATION_CONCERN = "irritation_concern"
    FORMULATION_CONFLICT = "formulation_conflict"
    PH_SENSITIVE = "ph_sensitive_concern"
    DUPLICATE_ACTIVE_LOAD = "duplicate_active_load"
    EVIDENCE_LIMITED = "evidence_limited_interaction"


class FindingType(str, Enum):
    RULE = "rule"                      # a reviewed knowledge rule fired
    SHARED_KEY_ACTIVE = "shared_key_active"  # factual: both contain the same flagged active
    UNRESOLVED = "unresolved_ingredients"
    INCOMPLETE = "incomplete_formulation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class CompatibilityStatus(str, Enum):
    """The five controlled result categories (SkinIQ spec §34)."""

    NO_NOTABLE_INTERACTION = "no_notable_interaction"
    CAUTION = "caution"
    STRONG_CAUTION = "strong_caution"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_INCOMPLETE = "data_incomplete"


STATUS_LABELS = {
    CompatibilityStatus.NO_NOTABLE_INTERACTION: (
        "No notable interaction identified in the current knowledge base "
        "for the formulations supplied."
    ),
    CompatibilityStatus.CAUTION: "Potential interaction: caution",
    CompatibilityStatus.STRONG_CAUTION: "Strong caution",
    CompatibilityStatus.INSUFFICIENT_EVIDENCE: "Insufficient evidence for a conclusion",
    CompatibilityStatus.DATA_INCOMPLETE: "Data incomplete: one or both formulations are not fully known",
}


class NormalizationMethod(str, Enum):
    EXACT = "exact"
    ALIAS_COMPONENT = "alias_component"
    FUZZY = "fuzzy"
    UNRESOLVED = "unresolved"


class ReviewStatus(str, Enum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    RETIRED = "retired"


class SourceType(str, Enum):
    REGULATORY = "regulatory"
    PEER_REVIEWED = "peer_reviewed"
    PROFESSIONAL_GUIDANCE = "professional_guidance"
    MANUFACTURER = "manufacturer"
    EXPERT_CURATED = "expert_curated"
    FIXTURE = "fixture"  # tests and the labelled demo only; rejected by the real loader


def confidence_level(score: float) -> ConfidenceLevel:
    """Map a 0..1 score to a label. Thresholds are design parameters (ASSUMPTIONS.md)."""
    if score >= 0.85:
        return ConfidenceLevel.HIGH
    if score >= 0.6:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW
