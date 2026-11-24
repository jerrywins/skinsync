# Data governance, licensing and formats

## Sources

| Source | What | Licence / terms | Status |
|---|---|---|---|
| Open Beauty Facts CSV export (`static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv.gz`) | Products, brands, categories, ingredient text, barcodes, image URLs | Database: ODbL 1.0. Contents: Database Contents License 1.0. Images: CC BY-SA. | **Imported**: 2,557 skincare products (export of 2026-11-04; 64,237 rows, 17,626 with ingredients overall) |
| Ingredient names observed in OBF data | Canonical names seeded from strings seen in ≥ 5 products and ≥ 2 brands | Derived from ODbL data | **Imported, unreviewed**: 700 names, no function classes |
| `knowledge/ingredients.yaml` | Ingredient master entries | Team-owned | **20 AI-drafted entries** (acne actives, AHAs/BHA, retinoids incl. retinol/retinal/tazarotene, dapsone, azelaic, kojic, hydroquinone, bakuchiol, ascorbic acid); names/aliases load, function classes **only after review** |
| `knowledge/rules.yaml`, `evidence.yaml` | Interaction rules and evidence | Team-owned, citations required | **7 AI-drafted rules, 10 evidence records with real citations** (PubMed 9990414/26557215/26516077, AAD 2024 guideline + AAFP 2025 summary, 21 CFR 333.350, FDA/DailyMed labels; R-0005..R-0007 from the team CSV, `knowledge/review/INTEGRATION_REPORT.md`); all `draft`, loaded into version `kv-…-draft` which **cannot be published** until a human marks them reviewed (`knowledge/RESEARCH_NOTES.md`) |
| `knowledge/concern_map.yaml` | Observation → ingredient classes | Team-owned, citations required | Empty, **awaiting human scientific review** |
| Team compatibility CSV (`knowledge/sources/skincare_ingredient_compatibility_dataset.csv`) | 73 ingredient pairs with labels and citations | Team-supplied | **Integrated** 2026-11-24: 13 rows → new draft rules, 10 covered by existing rules, 25 compatible/no interaction, 25 pending a verified source. Every row's outcome: `knowledge/review/csv-crosswalk.csv` |
| Skinzy app dataset (300 pairs, not stored) | Third-party app's pair statuses | Third-party content; explanations not copied | **Cross-check only** (`knowledge/review/skinzy-crosscheck.csv`): names, status, public URL |
| Price observations | Seller prices | CSV import only | **No real source connected**. For testing only, `seed-test-prices` adds one **random** INR price per unpriced real product (source `synthetic-test`, seller "TEST PRICE — not real", badge in UI). Refused outside dev/test, hidden by the API in staging/prod, removed with `remove-test-prices`. |
| `knowledge/demo/` | Fictional demo products, rules, prices | Project-owned, fictional | Loaded only when `SKINSYNC_DEMO_MODE=true`; labelled DEMO everywhere |

### ODbL obligations for anyone redistributing this database

* **Attribute** Open Beauty Facts (done: footer, `/data-sources`, product pages link to the source record).
* **Share-alike**: a public database derived from OBF must be offered under ODbL.
* **Keep open**: no technical restrictions on the derived database.
* Product photos are referenced by URL, not re-hosted.

## Record classes

| Class | How it is marked | Shown to users as |
|---|---|---|
| Verified | `product_versions.verification = 'verified'`; `ingredients.reviewed_at` set | normal |
| Imported | `verification = 'imported'`, `source = 'openbeautyfacts'` | source + retrieved date; "unreviewed" ingredient names |
| Unverified | `verification = 'unverified'` | flagged |
| Demonstration | `is_demo = true` | DEMO badge; separate knowledge version; cannot mix with real products |
| Synthetic test price | `price_observations.source = 'synthetic-test'` | "TEST PRICE — not real" badge; never shown in staging/prod |

## Review workflow

1. The importer raises flags: missing ingredient list, unrecognised ingredients, fuzzy suggestions.
2. Users can report incorrect data (`/reports`).
3. Admins resolve flags, add or correct ingredients (`POST /admin/ingredients`) and fix individual matches
   (`POST /admin/ingredient-mappings`). A correction creates a new formulation version, so earlier results
   stay reproducible and are marked out of date.
4. Rules and evidence are edited in `knowledge/*.yaml` under review (pull request), imported as a draft
   version, moved to review, and published. The database refuses unsafe publishes. See `ADMIN_GUIDE.md`.

## File formats

### `knowledge/evidence.yaml`
```yaml
evidence:
  - id: EV-0001                       # unique
    claim: "One-sentence claim the citation supports."
    source_type: peer_reviewed        # regulatory | peer_reviewed | professional_guidance | manufacturer | expert_curated
    citation: "Author, Title, Journal, Year, DOI"
    strength: moderate                # high | moderate | limited | insufficient | unknown
    publication_date: 2024-05-01      # optional
    retrieved_at: 2026-11-01          # optional
    reviewer: "Name"                  # optional
```

### `knowledge/rules.yaml`
```yaml
rules:
  - code: R-0001
    interaction_type: irritation_concern  # redundancy | irritation_concern | formulation_conflict | ph_sensitive_concern | duplicate_active_load | evidence_limited_interaction
    severity: caution                     # info | caution | strong_caution
    side_a: [{ingredient: some-canonical-id}]            # or {function_class: name}; optional max_position
    side_b: [{function_class: some-class, max_position: 5}]
    mechanism_summary: "Short, neutral description"
    practical_guidance: "What a user can do"
    explanation_template: "{a_ingredients} in {product_a} and {b_ingredients} in {product_b} ..."
    evidence_ids: [EV-0001]               # at least one; must exist
    review_status: reviewed
    last_reviewed: 2026-11-01
```
Rules are symmetric. Placeholders other than the four shown are rejected.

### `knowledge/concern_map.yaml`
```yaml
mappings:
  - observation: visible_shine          # one of the cosmetic observation vocabulary
    concern_category: "Oil balance"     # no condition or diagnosis words (validated)
    ingredient_classes: [some-function-class]
    intended_role: "Cosmetic role in plain words"
    evidence_ids: [EV-0002]
```

### Team product CSV (`python -m skinsync.cli import-csv FILE`)
`source_ref,brand,name,category,category_parent,barcode,market,observed_at,ingredients,key_actives,source_name`
(`observed_at` = YYYY-MM-DD; `key_actives` = `;`-separated canonical ids; `category` from `ingest/obf_categories.yaml`).

### Price CSV (`python -m skinsync.cli import-prices FILE`)
`product_ref,amount,currency,seller,country,source,observed_at,available` — `product_ref` is a slug, id or barcode;
`observed_at` ISO 8601 with time zone. Prices older than 30 days show as "older observation", older than 120 days as unavailable.
