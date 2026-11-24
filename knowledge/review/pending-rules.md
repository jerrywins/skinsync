# Pending rules: flagged by a dataset, no verified source yet

These pairs are **not** in `rules.yaml`. 24 of them are already written in the rule format in
`pending-rules.yaml` (codes P-0001 to P-0024; row 41, "peptides" in general, has no single ingredient to match).
That file is not loaded by the app, and each rule there cites only its CSV row, graded `insufficient`. The team CSV and/or the Skinzy app flag them, but no source that
supports the claim was found or checked. To promote one: find a source (label, guideline, or
peer-reviewed study that tests the pair or clearly covers it), add it to `evidence.yaml`, copy the P- rule into
`rules.yaml` with a new R- code citing that evidence, keep `review_status: draft`, and update `OUTCOMES` in
`scripts/crosswalk_datasets.py`.

Until then, the engine says nothing about these pairs. A comparison of two such products shows "no notable
interaction identified in the current knowledge base", which only means "not in our knowledge base".

Row numbers refer to `knowledge/sources/skincare_ingredient_compatibility_dataset.csv`
(full detail: `csv-crosswalk.csv`, `skinzy-crosscheck.csv`).

## Priority 1: both datasets flag it

| Pair | CSV label (strength) | Skinzy | Note |
|---|---|---|---|
| Retinol + benzoyl peroxide (row 46) | FORMULATION_DEPENDENT (Low) | avoid | Retinal and hydroxypinacolone retinoate + BPO: Skinzy only. EV-0001 shows *tretinoin* degrades; it did not test retinol |
| Retinyl palmitate + benzoyl peroxide (row 50) | FORMULATION_DEPENDENT (Low) | – | as above |
| Benzoyl peroxide + glycolic / lactic acid (rows 51, 52) | CAUTION_IRRITATION (Moderate) | avoid (also mandelic) | CSV cites the AAD guideline page generally; not pair-specific |
| Vitamin C (L-ascorbic acid) + glycolic acid (row 20) | CAUTION_IRRITATION (Low) | avoid (also lactic, mandelic) | |
| Vitamin C + retinol (row 19) | COMPATIBLE_WITH_CAUTION | use in separate routines | |
| Vitamin C + kojic acid (row 66) | COMPATIBLE_WITH_CAUTION (Low) | **avoid** | the datasets disagree |

## Priority 2: the CSV flags it, Skinzy does not cover it

| Pair (CSV row) | CSV label (strength) |
|---|---|
| Vitamin C + benzoyl peroxide (17) | FORMULATION_DEPENDENT (Low) |
| Vitamin C + salicylic acid (21) | CAUTION_IRRITATION (Low) |
| Azelaic acid + benzoyl peroxide (31), adapalene (32), tretinoin (33), salicylic acid (53), glycolic acid (55) | COMPATIBLE_WITH_CAUTION / CAUTION_IRRITATION (Moderate) |
| Hydroquinone + tretinoin (36) | COMPATIBLE_WITH_CAUTION (High). Cites a prescribing label by a directory URL, not a document |
| Hydroquinone + glycolic acid (37), benzoyl peroxide (72), vitamin C (73) | Low |
| Kojic acid + glycolic acid (38) | Low |
| Urea + retinol (63), glycolic acid (64) | Low |
| PHA (gluconolactone) + glycolic acid (16) | Low |
| Peptides / copper peptides + vitamin C (41, 71), glycolic acid (70) | FORMULATION_DEPENDENT (Low) |

## Priority 3: Skinzy only

| Pair | Skinzy |
|---|---|
| Bakuchiol + glycolic / lactic / mandelic / salicylic acid | caution |
| Two retinoids together (retinol, retinal, hydroxypinacolone retinoate, adapalene, tretinoin) | same_class (a class label, not a verdict). Candidate for a "duplicate retinoid" rule if a source supports it |
