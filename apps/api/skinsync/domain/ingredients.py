"""Ingredient-list parsing and normalization (SkinSync spec §12.1, FR-03, US-003).

Raw label text -> cleaned entries -> canonical ingredient (or UNRESOLVED).

Rules that matter:
* Unknown ingredients stay unknown. Nothing is mapped below the fuzzy threshold.
* Fuzzy matches are never auto-accepted; they are flagged NEEDS_REVIEW.
* Position and stated role ("may contain") are preserved.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, Field

from .enums import NormalizationMethod, ReviewStatus

try:  # rapidfuzz is much faster; difflib is the dependency-free fallback
    from rapidfuzz import fuzz as _rf_fuzz
    from rapidfuzz import process as _rf_process
except ImportError:  # pragma: no cover
    _rf_fuzz = _rf_process = None

SUGGEST_THRESHOLD = 0.85  # fuzzy similarity needed to *suggest* a match (never to resolve one)
COMPONENT_CONFIDENCE = 0.95
MULTI_COMPONENT_CONFIDENCE = 0.8

_PREFIX = re.compile(r"^\s*(ingredients?|inci|composition)\s*[:\-]\s*", re.I)
_MAY_CONTAIN = re.compile(r"\[?\s*(\+/-|\+/−|may contain|peut contenir)\s*[:]?\s*", re.I)
_CONCENTRATION = re.compile(r"\(?\s*(\d+(?:[.,]\d+)?)\s*%\s*\)?")
_FOOTNOTE = re.compile(r"[*†‡°]+")


class IngredientRecord(BaseModel):
    """An entry of the ingredient master (team-reviewed data, never invented)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=120)
    inci_name: str = Field(min_length=1, max_length=300)
    aliases: tuple[str, ...] = ()
    function_classes: tuple[str, ...] = ()  # empty = unknown, never guessed
    source: str = Field(min_length=1, max_length=300)


class ParsedEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    position: int
    raw: str
    cleaned: str
    stated_role: str = "listed"  # "listed" | "may_contain"
    concentration_pct: float | None = None


class NormalizedIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    position: int
    raw: str
    canonical_id: str | None
    inci_name: str | None
    function_classes: tuple[str, ...] = ()
    method: NormalizationMethod
    confidence: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus
    stated_role: str = "listed"
    concentration_pct: float | None = None
    is_key_active: bool = False
    candidate: str | None = None  # suggested match shown to a reviewer/user
    candidate_id: str | None = None
    candidate_score: float | None = None

    @property
    def resolved(self) -> bool:
        return self.canonical_id is not None and self.method != NormalizationMethod.UNRESOLVED


def normalize_key(text: str) -> str:
    """Lowercase, strip accents and punctuation noise, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9/()\-+ .]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text


def _split_top_level(text: str) -> list[str]:
    """Split on commas/semicolons that are not inside parentheses or brackets."""
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]" and depth:
            depth -= 1
        if ch in ",;" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def parse_ingredient_list(text: str) -> list[ParsedEntry]:
    """Split a raw ingredient label into ordered entries."""
    if not text or not text.strip():
        return []
    text = _PREFIX.sub("", text.strip()).rstrip(" .")
    may_contain_from: int | None = None
    entries: list[ParsedEntry] = []
    for raw in _split_top_level(text):
        role = "listed"
        m = _MAY_CONTAIN.search(raw)
        if m:
            may_contain_from = len(entries)
            raw = raw[: m.start()] + raw[m.end():]
        if may_contain_from is not None:
            role = "may_contain"
        conc = None
        cm = _CONCENTRATION.search(raw)
        if cm:
            conc = float(cm.group(1).replace(",", "."))
            raw_wo = _CONCENTRATION.sub(" ", raw)
        else:
            raw_wo = raw
        cleaned = normalize_key(_FOOTNOTE.sub("", raw_wo).strip(" []"))
        if not cleaned or not re.search(r"[a-z]", cleaned):
            continue
        entries.append(
            ParsedEntry(
                position=len(entries) + 1,
                raw=raw.strip(" []"),
                cleaned=cleaned,
                stated_role=role,
                concentration_pct=conc,
            )
        )
    return entries


@dataclass
class IngredientMaster:
    """In-memory alias index built from reviewed ingredient records."""

    records: dict[str, IngredientRecord] = field(default_factory=dict)
    _index: dict[str, str] = field(default_factory=dict)
    _sorted: list[str] | None = None

    @classmethod
    def from_records(cls, records: list[IngredientRecord]) -> IngredientMaster:
        master = cls()
        for rec in records:
            if rec.id in master.records:
                raise ValueError(f"duplicate ingredient id: {rec.id}")
            master.records[rec.id] = rec
            for name in (rec.inci_name, *rec.aliases):
                key = normalize_key(name)
                existing = master._index.get(key)
                if existing and existing != rec.id:
                    raise ValueError(f"alias {name!r} maps to both {existing} and {rec.id}")
                master._index[key] = rec.id
        return master

    def lookup_exact(self, key: str) -> IngredientRecord | None:
        rid = self._index.get(key)
        return self.records[rid] if rid else None

    def best_fuzzy(self, key: str) -> tuple[IngredientRecord | None, float, str | None]:
        if not self._index:
            return None, 0.0, None
        if self._sorted is None:
            self._sorted = sorted(self._index)  # stable order -> deterministic ties
        if _rf_process is not None:
            hit = _rf_process.extractOne(key, self._sorted, scorer=_rf_fuzz.ratio)
            if not hit:
                return None, 0.0, None
            alias, score, _ = hit
            return self.records[self._index[alias]], score / 100.0, alias
        best_alias, best = None, 0.0
        for alias in self._sorted:
            r = difflib.SequenceMatcher(None, key, alias).ratio()
            if r > best:
                best, best_alias = r, alias
        return (self.records[self._index[best_alias]] if best_alias else None), best, best_alias


def _components(cleaned: str) -> list[str]:
    """'aqua (water)' -> ['aqua', 'water']; 'parfum/fragrance' -> ['parfum', 'fragrance']."""
    out: list[str] = []
    inner = re.findall(r"\(([^)]*)\)", cleaned)
    outer = re.sub(r"\([^)]*\)", " ", cleaned)
    for chunk in [outer, *inner]:
        for piece in chunk.split("/"):
            piece = normalize_key(piece)
            if piece and piece not in out:
                out.append(piece)
    return out


def normalize_entry(
    entry: ParsedEntry, master: IngredientMaster, key_actives: frozenset[str] = frozenset()
) -> NormalizedIngredient:
    base = dict(
        position=entry.position,
        raw=entry.raw,
        stated_role=entry.stated_role,
        concentration_pct=entry.concentration_pct,
    )

    def hit(rec: IngredientRecord, method: NormalizationMethod, conf: float, status: ReviewStatus):
        return NormalizedIngredient(
            **base,
            canonical_id=rec.id,
            inci_name=rec.inci_name,
            function_classes=rec.function_classes,
            method=method,
            confidence=round(conf, 4),
            review_status=status,
            is_key_active=rec.id in key_actives,
        )

    rec = master.lookup_exact(entry.cleaned)
    if rec:
        return hit(rec, NormalizationMethod.EXACT, 1.0, ReviewStatus.AUTO_ACCEPTED)

    comps = _components(entry.cleaned)
    matched: dict[str, IngredientRecord] = {}
    for c in comps:
        r = master.lookup_exact(c)
        if r and r.id not in matched:
            matched[r.id] = r
    if len(matched) == 1:
        (rec,) = matched.values()
        return hit(rec, NormalizationMethod.ALIAS_COMPONENT, COMPONENT_CONFIDENCE, ReviewStatus.AUTO_ACCEPTED)
    if len(matched) > 1:
        # Labels conventionally write "INCI name / common name" or "INCI (common name)".
        # Resolve to the name written first, at reduced confidence, and ask for review.
        first = master.lookup_exact(comps[0])
        if first is not None:
            out = hit(first, NormalizationMethod.ALIAS_COMPONENT, MULTI_COMPONENT_CONFIDENCE, ReviewStatus.NEEDS_REVIEW)
            return out.model_copy(update={"candidate": ", ".join(sorted(matched))})
        return NormalizedIngredient(
            **base, canonical_id=None, inci_name=None, method=NormalizationMethod.UNRESOLVED,
            confidence=0.0, review_status=ReviewStatus.NEEDS_REVIEW, candidate=", ".join(sorted(matched)),
        )

    # Fuzzy similarity only ever produces a *suggestion*. Near-identical strings are often
    # different chemicals (polyglyceryl-2 vs -4 caprate), so nothing is resolved by fuzz.
    rec, ratio, alias = master.best_fuzzy(entry.cleaned)
    suggest = rec is not None and ratio >= SUGGEST_THRESHOLD and _digits(entry.cleaned) == _digits(alias or "")
    return NormalizedIngredient(
        **base,
        canonical_id=None,
        inci_name=None,
        method=NormalizationMethod.UNRESOLVED,
        confidence=0.0,
        review_status=ReviewStatus.NEEDS_REVIEW,
        candidate=rec.inci_name if suggest else None,
        candidate_id=rec.id if suggest else None,
        candidate_score=round(ratio, 4) if suggest else None,
    )


def _digits(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\d+", text))


def normalize_list(
    text: str, master: IngredientMaster, key_actives: frozenset[str] = frozenset()
) -> list[NormalizedIngredient]:
    return [normalize_entry(e, master, key_actives) for e in parse_ingredient_list(text)]
