# Draft-rule research notes (in progress, 2026-11-05)

Sources verified at the source. Nothing here is a published rule; rules drafted from these must be
`review_status: draft` until a team reviewer approves them.

| # | Source | What it actually says | Use for |
|---|---|---|---|
| S1 | Martin B. et al., "Chemical stability of adapalene and tretinoin when combined with benzoyl peroxide in presence and in absence of visible light and ultraviolet radiation", Br J Dermatol 1998;139 Suppl 52:8-11, doi:10.1046/j.1365-2133.1998.1390s2008.x (PubMed 9990414) | Tretinoin 0.025% gel mixed with 10% BPO lotion under light: >50% degraded in ~2 h, ~95% in 24 h. Adapalene stable. | Rule: tretinoin + benzoyl peroxide, formulation_conflict. NOT adapalene. |
| S2 | US 21 CFR 333.350(c)(1)(ii) (OTC topical acne monograph), via law.cornell.edu | "skin irritation and dryness is more likely to occur if you use another topical acne medication at the same time. If irritation occurs, only use one topical acne medication at a time." Applies to monograph acne actives (§333.310: benzoyl peroxide, resorcinol, salicylic acid, sulfur). | Rule: two products each with an acne monograph active, irritation_concern, caution. Regulatory source. |
| S3 | Differin (adapalene 0.1%) OTC Drug Facts (otclabels.com / FDA label) | Irritation more likely "if using more than one topical acne medication at a time". | Extend S2 to adapalene. |
| S4 | Tretinoin cream prescribing label, DailyMed setid 5e3fb8ea-234c-4be2-95a7-d139e069cf98 (rev. 03/2026) | "Particular caution should be exercised in using preparations containing sulfur, resorcinol, or salicylic acid"; caution with drying cosmetics. | Rule: tretinoin + salicylic acid / sulfur / resorcinol, irritation_concern. |
| S5 | FDA, "Alpha Hydroxy Acids" (content current 11/22/2022) | AHAs increase UV sensitivity; more serious reactions with products causing most exfoliation; CIR: glycolic/lactic safe at ≤10% and pH ≥3.5. | Evidence for exfoliant load (two AHA/BHA products), limited strength; sunscreen guidance. Not a direct pairwise claim. |

## Caveats found
* Lactic and citric acid often appear at low levels as pH adjusters. Pair rules on "AHA" need a position
  limit (`max_position`) or concentration data, or they will misfire. Reviewer decision.
* In this OBF import: salicylic-acid 70 products, lactic-acid 116, glycolic-acid 7, retinyl-palmitate 27,
  niacinamide 79, ascorbic-acid 22; no benzoyl peroxide, tretinoin or adapalene.
* Vitamin C + niacinamide: commonly repeated "conflict" lacks good evidence; do NOT add a rule without a source.

## Next steps when resuming
1. Draft `knowledge/evidence.yaml` (S1-S5) and `rules.yaml` (review_status: draft) + function classes in
   `knowledge/ingredients.yaml` (retinoid, aha, bha, acne-monograph-active) and a loader for that file.
2. Experimental image-heuristics skin adapter (labelled "experimental, not validated").
3. Dev/test-only labelled TEST PRICE generator + remover.
4. Mac Docker Desktop step-by-step guide; rerun all tests; repackage.
