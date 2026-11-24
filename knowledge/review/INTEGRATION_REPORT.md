# Integration report: team CSV and Skinzy dataset (2026-11-24)

Prepared by Claude (AI). Nothing here is published: every rule added is `review_status: draft`, and the admin
console refuses to publish a knowledge version while any rule is draft or cites insufficient evidence.

## 1. What came in

| File | Content | Kept in repo? |
|---|---|---|
| `skincare_ingredient_compatibility_dataset.csv` | 73 ingredient pairs, each with a label, evidence strength, notes, guidance, and (for 37 rows) a source URL | Yes: `knowledge/sources/` |
| `skinzy_dataset_completed_annotated.xlsx` | 300 pairs from the Skinzy app (useskinzy.app), with a conservative annotation layer | **No.** Its explanations are Skinzy's own text. Only names, status labels and page URLs are kept, in `skinzy-crosscheck.csv` |

## 2. How each label maps to SkinSync

The engine stores **concerns only**. A pair with no rule is reported as "no notable interaction identified in
the current knowledge base", so "compatible" needs no rule.

| Label | SkinSync |
|---|---|
| CSV `COMPATIBLE`, Skinzy `verified_ok` | No rule. Tested: no rule fires for these pairs |
| CSV `CAUTION_IRRITATION`, Skinzy `avoid` / `caution` | `irritation_concern` rule, **if** a checked source supports it |
| CSV `FORMULATION_DEPENDENT` | `formulation_conflict` rule, **if** a checked source supports it |
| CSV `COMPATIBLE_WITH_CAUTION` | No rule when the caution is one ingredient's own irritation; otherwise as above |
| Skinzy `same_class` | Not a compatibility verdict; not imported |
| Skinzy `no_conflict_on_record` (238 rows) | **Ignored.** It means Skinzy has no record, not that the pair is compatible |

## 3. Result for the 73 CSV rows

| Outcome | Rows |
|---|---|
| New draft rule (R-0005 retinoid + AHA, R-0006 retinoid + salicylic acid, R-0007 dapsone + benzoyl peroxide) | 13 |
| Covered by an existing draft rule (R-0001 to R-0004) | 10 |
| No rule: compatible | 22 |
| No rule: irritation from one ingredient alone, not an interaction | 3 |
| **Pending: no verified source** (`pending-rules.md`; 24 already written as rules in `pending-rules.yaml`, not loaded) | 25 |

## 4. Citation check

Each source URL in the CSV was opened (2026-11-24) where possible.

| Source | Finding |
|---|---|
| PubMed 9990414 (stability study, 1998) | Verified. Already EV-0001 |
| AAD 2024 acne guideline, PubMed 38300170 | Verified (abstract). Added as EV-0006. General recommendations, not pair-specific |
| AAFP 2025 summary of the AAD guideline | Verified (full page). Added as EV-0007. Supports: tretinoin degrades with BPO; adapalene/tazarotene can be used with BPO; BPO with topical antibiotics; emollients reduce retinoid irritation |
| Dapsone 7.5% label (DailyMed) | Found and verified for the CSV's dapsone row (the CSV gave only a directory URL). Added as EV-0010 |
| **PubMed 26557215** (cited for 7 retinoid/AHA rows) | **Does not support those rows.** A small, uncontrolled, industry-linked study of one product regimen (retinoid-lactic acid conjugate). No retinol, tretinoin or glycolic acid; no tolerability problems reported. Added as EV-0008, marked qualifying evidence, not cited by any rule |
| **PubMed 26516077** (cited for 7 retinoid/salicylic acid rows) | **Indirect.** A pilot of a retinoid ester with 2% salicylic acid; 2 of 27 stopped for irritation. Not the retinoids in the CSV rows. Added as EV-0009 (limited) |
| PubMed 16185284 (vitamin C + ferulic acid) | Title confirmed; abstract not read (PubMed blocked automated access). Only used by compatible rows, so no rule depends on it |
| aad.org guideline page (10 rows) | Not opened: a general landing page, not pair-specific |
| `accessdata.fda.gov/drugsatfda_docs/label/` (2 rows) | Not a source: a directory, not a document |
| No URL (36 rows) | Left pending, unless a checked source already covered the pair |

## 5. Where the datasets disagree

* **Retinoids + AHAs/BHA:** Skinzy says *avoid*; the CSV says it is a cumulative-irritation *caution*, not a
  chemical incompatibility. SkinSync follows the CSV (`caution`) because the checked sources support
  irritation, not incompatibility. Reviewer decision recorded in R-0005/R-0006.
* **Adapalene + benzoyl peroxide:** Skinzy *avoid* (because of irritation, although its own text says the pair
  is chemically stable); the CSV says *compatible*; SkinSync's draft R-0002 flags irritation from the Differin
  label. Reviewer decision recorded in R-0002.
* **Vitamin C + kojic acid:** Skinzy *avoid*, CSV *compatible with caution*. Pending (no checked source).
* **AHA + BHA stacking:** CSV says *caution*; SkinSync's draft R-0004 shows it as *info*. Reviewer decision.

## 6. Other changes made

* Ingredient names added (draft): retinol, retinal (alias retinaldehyde), tazarotene, retinyl palmitate,
  hydroxypinacolone retinoate, dapsone, azelaic acid, kojic acid, hydroquinone, bakuchiol, ascorbic acid
  (alias L-ascorbic acid).
* `pending-rules.yaml`: the pending rows in the `rules.yaml` format, ready to promote once a source is checked.
  Kept out of `rules.yaml` because the publish check refuses any version containing evidence graded insufficient,
  which would also block the 7 checked rules.
* Ingredient name added for the pending rules: copper tripeptide-1 (aliases copper peptides, GHK-Cu).
* New command `reresolve`, also run by `bootstrap`: products imported earlier are re-matched against new names.
  On the development database this matched 16 more ingredients in 16 products (e.g. 4 with retinol, 2 with
  retinal); stale cached comparisons are cleared.

## 7. What a reviewer needs to do

1. Check EV-0006 to EV-0010 (claims, strength grades) and set `reviewer`.
2. Decide the REVIEWER DECISION notes in R-0001, R-0002, R-0004, R-0005, R-0006.
3. Work through `pending-rules.md`, starting with priority 1.
4. Mark reviewed rules `review_status: reviewed`, then import and publish a knowledge version in the admin console.
