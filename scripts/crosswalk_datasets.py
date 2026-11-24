"""Crosswalk two external compatibility datasets against SkinSync's knowledge (re-runnable).

    python3 scripts/crosswalk_datasets.py CSV [SKINZY_XLSX]

Inputs
  CSV          team-supplied skincare_ingredient_compatibility_dataset.csv (73 pairs, with citations)
  SKINZY_XLSX  skinzy_dataset_completed_annotated.xlsx (300 pairs from the Skinzy app; optional)

Outputs (knowledge/review/)
  csv-crosswalk.csv      every CSV row -> what SkinSync did with it, and what its citation check found
  skinzy-crosscheck.csv  every Skinzy row that states something (not "no_conflict_on_record") vs. the CSV
                         and SkinSync. Skinzy's explanatory text is NOT copied (third-party content); only
                         names, its status label and its public page URL are kept.

Nothing here changes rules. Outcomes are decided by people and recorded in OUTCOMES below.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "review"

# Name -> SkinSync ingredient id (both datasets use display names).
ALIASES = {
    "pha (gluconolactone)": "gluconolactone", "l-ascorbic acid": "ascorbic-acid",
    "vitamin c (l-ascorbic acid)": "ascorbic-acid", "pure vitamin c": "ascorbic-acid",
    "hyaluronic acid": "hyaluronic-acid", "ceramides": "ceramides", "ceramide 3": "ceramides",
    "topical clindamycin": "clindamycin", "tranexamic acid topical": "tranexamic-acid",
    "alpha arbutin": "alpha-arbutin", "alpha-arbutin": "alpha-arbutin", "peptides (cosmetic)": "peptides",
    "retinaldehyde": "retinal", "retinal": "retinal", "granactive retinoid": "hydroxypinacolone-retinoate",
    "vitamin e (tocopherol)": "tocopherol", "copper peptides": "copper-peptides",
}


def ing_id(name: str) -> str:
    n = name.strip().lower()
    if n in ALIASES:
        return ALIASES[n]
    n = re.sub(r"\s*\((aha|bha)\)", "", n)
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((ing_id(a), ing_id(b))))


# What SkinSync did with each CSV pair (decided 2026-11-24; rules are draft until reviewed).
RULE, EXISTING, NONE_OK, NONE_SELF, PENDING = (
    "new draft rule", "covered by existing draft rule", "no rule: compatible",
    "no rule: irritation from one ingredient on its own, not an interaction", "pending: no verified source")
OUTCOMES: dict[tuple[str, str], tuple[str, str, str]] = {}


def put(a, b, outcome, code="", note=""):
    OUTCOMES[key(a, b)] = (outcome, code, note)


put("tretinoin", "benzoyl peroxide", EXISTING, "R-0001", "strengthened with EV-0007; CSV's 'formulation dependent' noted for reviewer")
put("adapalene", "benzoyl peroxide", EXISTING, "R-0002",
    "CONFLICT: CSV says compatible; R-0002 is an irritation rule from the Differin label. Reviewer decision")
put("tazarotene", "benzoyl peroxide", NONE_OK, "", "EV-0007: tazarotene can be used concurrently with benzoyl peroxide")
for r in ("retinol", "tretinoin", "tazarotene", "retinaldehyde", "adapalene", "retinyl palmitate"):
    put(r, "glycolic acid", RULE, "R-0005")
for r in ("retinol", "tretinoin"):
    put(r, "lactic acid", RULE, "R-0005")
put("retinol", "mandelic acid", RULE, "R-0005")
for r in ("retinol", "tazarotene", "retinaldehyde"):
    put(r, "salicylic acid", RULE, "R-0006")
put("tretinoin", "salicylic acid", EXISTING, "R-0003")
put("adapalene", "salicylic acid", EXISTING, "R-0002")
put("benzoyl peroxide", "salicylic acid", EXISTING, "R-0002")
put("salicylic acid", "sulfur", EXISTING, "R-0002")
for a, b in (("glycolic acid", "lactic acid"), ("glycolic acid", "salicylic acid"), ("lactic acid", "salicylic acid"),
             ("mandelic acid", "salicylic acid")):
    put(a, b, EXISTING, "R-0004", "R-0004 is severity info; CSV says caution. Reviewer decision")
put("benzoyl peroxide", "dapsone", RULE, "R-0007", "verified on the dapsone 7.5% label (EV-0010)")
put("benzoyl peroxide", "topical clindamycin", NONE_OK, "", "EV-0007")
for a, b in (("L-ascorbic acid", "niacinamide"), ("niacinamide", "retinol"), ("niacinamide", "hyaluronic acid"),
             ("hyaluronic acid", "retinol"), ("hyaluronic acid", "glycolic acid"), ("ceramides", "retinol"),
             ("ceramides", "glycolic acid"), ("tranexamic acid topical", "niacinamide"),
             ("L-ascorbic acid", "ferulic acid"), ("L-ascorbic acid", "vitamin E (tocopherol)"),
             ("azelaic acid", "niacinamide"), ("azelaic acid", "hyaluronic acid"), ("hyaluronic acid", "salicylic acid"),
             ("hyaluronic acid", "benzoyl peroxide"), ("panthenol", "retinol"), ("panthenol", "glycolic acid"),
             ("kojic acid", "niacinamide"), ("tranexamic acid topical", "vitamin C (L-ascorbic acid)"),
             ("retinoids", "sunscreen"), ("alpha arbutin", "L-ascorbic acid")):
    put(a, b, NONE_OK)
for a, b in (("niacinamide", "salicylic acid"), ("niacinamide", "glycolic acid"), ("niacinamide", "benzoyl peroxide")):
    put(a, b, NONE_SELF)
PENDING_PAIRS = [
    ("PHA (gluconolactone)", "glycolic acid"), ("L-ascorbic acid", "benzoyl peroxide"), ("L-ascorbic acid", "retinol"),
    ("L-ascorbic acid", "glycolic acid"), ("L-ascorbic acid", "salicylic acid"), ("benzoyl peroxide", "azelaic acid"),
    ("adapalene", "azelaic acid"), ("tretinoin", "azelaic acid"), ("hydroquinone", "tretinoin"),
    ("hydroquinone", "glycolic acid"), ("kojic acid", "glycolic acid"), ("peptides (cosmetic)", "L-ascorbic acid"),
    ("retinol", "benzoyl peroxide"), ("retinyl palmitate", "benzoyl peroxide"), ("benzoyl peroxide", "glycolic acid"),
    ("benzoyl peroxide", "lactic acid"), ("salicylic acid", "azelaic acid"), ("azelaic acid", "glycolic acid"),
    ("urea", "retinol"), ("urea", "glycolic acid"), ("kojic acid", "vitamin C (L-ascorbic acid)"),
    ("copper peptides", "glycolic acid"), ("copper peptides", "L-ascorbic acid"), ("hydroquinone", "benzoyl peroxide"),
    ("hydroquinone", "vitamin C (L-ascorbic acid)"),
]
for a, b in PENDING_PAIRS:
    put(a, b, PENDING)

# What opening each cited source showed (2026-11-24).
CITATIONS = {
    "9990414": "verified: stability study (EV-0001)",
    "38300170": "verified, abstract only: AAD 2024 guideline (EV-0006); not pair-specific",
    "26557215": "MISMATCH: real study of a retinoid-lactic acid conjugate regimen; no retinol/tretinoin/glycolic (EV-0008)",
    "26516077": "MISMATCH: real pilot of a retinoid ester + 2% salicylic acid; not this retinoid (EV-0009)",
    "16185284": "title confirmed by search; abstract not read (PubMed blocked automated access)",
    "aafp.org": "verified: AAFP 2025 summary of the AAD guideline (EV-0007)",
    "aad.org": "not opened: general guideline landing page",
    "accessdata.fda.gov/drugsatfda_docs/label/": "NOT A SOURCE: a directory, not a specific label",
}


def citation_check(url: str) -> str:
    if not url.strip():
        return "no source given"
    found = [v for k, v in CITATIONS.items() if k in url]
    return " | ".join(dict.fromkeys(found)) or "not checked"


def crosswalk(csv_path: Path) -> list[dict]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out = []
    for i, r in enumerate(rows, start=2):  # spreadsheet row numbers
        if not r["ingredient_A"].strip():
            continue
        outcome, code, note = OUTCOMES.get(key(r["ingredient_A"], r["ingredient_B"]), ("UNMAPPED", "", ""))
        out.append({"csv_row": i, "ingredient_A": r["ingredient_A"], "ingredient_B": r["ingredient_B"],
                    "csv_label": r["compatibility_label"], "csv_evidence_strength": r["evidence_strength"],
                    "skinsync_outcome": outcome, "rule": code, "note": note,
                    "citation_check": citation_check(r["source_url"])})
    return out


def rule_coverage() -> dict[tuple[str, str], list[str]]:
    """Which shipped rules name both ingredients of a pair (position limits ignored)."""
    import yaml

    cov: dict[tuple[str, str], list[str]] = {}
    for r in yaml.safe_load((ROOT / "knowledge" / "rules.yaml").read_text())["rules"]:
        sa = [t["ingredient"] for t in r["side_a"] if "ingredient" in t]
        sb = [t["ingredient"] for t in r["side_b"] if "ingredient" in t]
        for x in sa:
            for y in sb:
                if x != y:
                    cov.setdefault(tuple(sorted((x, y))), []).append(r["code"])
    return cov


def skinzy(xlsx: Path, cw: list[dict]) -> list[dict]:
    import openpyxl

    by_pair = {key(c["ingredient_A"], c["ingredient_B"]): c for c in cw}
    cov = rule_coverage()
    ws = openpyxl.load_workbook(xlsx, read_only=True)["Annotated_Dataset"]
    out = []
    for a, _ia, b, _ib, status, _reason, _src, url, std, *_ in ws.iter_rows(min_row=2, values_only=True):
        if status in (None, "no_conflict_on_record"):
            continue
        c = by_pair.get(key(a, b))
        out.append({"ingredient_a": a, "ingredient_b": b, "skinzy_status": status, "skinzy_label": std,
                    "skinzy_page": url or "", "csv_label": c["csv_label"] if c else "not in CSV",
                    "skinsync_outcome": (f"{c['skinsync_outcome']} {c['rule']}".strip() if c else
                                         ("draft rule " + ", ".join(cov[key(a, b)]) if key(a, b) in cov
                                          else "no rule")),
                    "agreement": compare(status, c["csv_label"] if c else None)})
    return out


def compare(skinzy_status: str, csv_label: str | None) -> str:
    if csv_label is None:
        return "only in Skinzy"
    caution = {"CAUTION_IRRITATION", "COMPATIBLE_WITH_CAUTION", "FORMULATION_DEPENDENT"}
    if skinzy_status == "avoid":
        return "Skinzy stricter (avoid)" if csv_label in caution else "CONFLICT (Skinzy avoid, CSV compatible)"
    if skinzy_status in ("verified_ok",):
        return "agree" if csv_label.startswith("COMPATIBLE") else "CONFLICT"
    if skinzy_status in ("caution", "verified_split"):
        return "agree" if csv_label in caution else "Skinzy stricter"
    return "not a compatibility verdict"


# CSV names -> ingredient ids used in rule terms (only for pending pairs; None = no single ingredient).
TERM = {"pha (gluconolactone)": "gluconolactone", "l-ascorbic acid": "ascorbic-acid",
        "vitamin c (l-ascorbic acid)": "ascorbic-acid", "copper peptides": "copper-tripeptide-1",
        "peptides (cosmetic)": None}


def term(name: str) -> str | None:
    n = name.strip().lower()
    return TERM[n] if n in TERM else ing_id(name)


def pending_yaml(csv_path: Path) -> tuple[str, list[str]]:
    """Pending CSV rows written in the rules.yaml / evidence.yaml format (NOT loaded by the app).

    Each rule cites one evidence record that is the CSV row itself, graded `insufficient`, so even if moved into
    rules.yaml unchanged it could not be published. A reviewer replaces that record with a checked source."""
    import yaml

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    rules, evidence, skipped = [], [], []
    n = 0
    for i, r in enumerate(rows, start=2):
        if not r["ingredient_A"].strip() or OUTCOMES.get(key(r["ingredient_A"], r["ingredient_B"]), ("",))[0] != PENDING:
            continue
        a, b = term(r["ingredient_A"]), term(r["ingredient_B"])
        if a is None or b is None:
            skipped.append(f"row {i}: {r['ingredient_A']} + {r['ingredient_B']} (no single ingredient to match)")
            continue
        n += 1
        ev = f"EV-P-{n:04d}"
        evidence.append({
            "id": ev, "claim": r["scientific_note"], "source_type": "expert_curated",
            "citation": f"Team compatibility dataset, knowledge/sources/skincare_ingredient_compatibility_dataset.csv, "
                        f"row {i}. Its own reference: {r['source_reference'] or 'none'}"
                        + (f" ({r['source_url']})" if r["source_url"].strip() else ""),
            "strength": "insufficient",
            "notes": f"CSV evidence_strength {r['evidence_strength']}; basis: {r['evidence_basis']}. Not checked "
                     "against a primary source: replace with a checked record before review."})
        fd = r["compatibility_label"] == "FORMULATION_DEPENDENT"
        rules.append({
            "code": f"P-{n:04d}",
            "interaction_type": "formulation_conflict" if fd else "irritation_concern",
            "severity": "caution" if r["evidence_strength"] in ("High", "Moderate") else "info",
            "side_a": [{"ingredient": a}], "side_b": [{"ingredient": b}],
            "mechanism_summary": r["interaction_type"],
            "practical_guidance": r["usage_guidance"],
            "explanation_template": "{a_ingredients} in {product_a} and {b_ingredients} in {product_b}: "
                                    + r["scientific_note"].replace("{", "(").replace("}", ")"),
            "evidence_ids": [ev], "review_status": "draft"})
    head = ("# PENDING rules from the team CSV, in the rules.yaml format. NOT LOADED BY THE APP.\n"
            "# Generated by scripts/crosswalk_datasets.py; do not edit by hand (edit the CSV or the script).\n"
            "# Each rule cites only its CSV row, graded `insufficient`, so it cannot be published as is.\n"
            "# To promote one: add a checked source to evidence.yaml, copy the rule into rules.yaml with that\n"
            "# evidence id and a new R- code, and keep review_status draft until a reviewer approves it.\n")
    body = yaml.safe_dump({"rules": rules, "evidence": evidence}, sort_keys=False, allow_unicode=True, width=110)
    return head + body, skipped


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str]) -> None:
    cw = crosswalk(Path(argv[1]))
    unmapped = [c for c in cw if c["skinsync_outcome"] == "UNMAPPED"]
    if unmapped:
        sys.exit(f"unmapped CSV rows: {[(c['ingredient_A'], c['ingredient_B']) for c in unmapped]}")
    write(OUT / "csv-crosswalk.csv", cw)
    print(f"csv-crosswalk.csv: {len(cw)} rows")
    text, skipped = pending_yaml(Path(argv[1]))
    (OUT / "pending-rules.yaml").write_text(text, encoding="utf-8")
    print(f"pending-rules.yaml: {text.count('- code: ')} rules; skipped {skipped}")
    if len(argv) > 2:
        sz = skinzy(Path(argv[2]), cw)
        write(OUT / "skinzy-crosscheck.csv", sz)
        print(f"skinzy-crosscheck.csv: {len(sz)} rows")


if __name__ == "__main__":
    main(sys.argv)
