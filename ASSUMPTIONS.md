# Assumptions and design parameters

Each entry: decision, reason, how to change it.

| # | Decision | Reason | Change it in |
|---|---|---|---|
| A1 | Product name is SkinSync | SPEC.md supersedes "SkinIQ" (ADR 0001) | `APP_NAME` config (to be added with the API) |
| A2 | Fuzzy similarity ≥ 0.85 (rapidfuzz ratio) only *suggests* a match; never resolves one; no suggestion when numbers differ (ADR 0006) | Near-identical names are often different chemicals | `domain/ingredients.py` |
| A3 | Confidence labels: high ≥ 0.85, moderate ≥ 0.6, else low | Design parameter (ADR 0005) | `domain/enums.py::confidence_level` |
| A4 | Alternatives weights 0.35/0.20/0.15/0.15/0.15 from SkinIQ §46; unavailable dimensions excluded and renormalised | Missing signal must not count as a match | `domain/alternatives.py::DEFAULT_WEIGHTS` |
| A5 | Ingredient overlap weighted by label position, w = 1/(1+pos/5) | Earlier ingredients roughly indicate larger amounts; design parameter, not science | `alternatives._position_weights` |
| A6 | Price fresh ≤ 30 days, stale ≤ 120 days, else unavailable; only fresh same-currency prices are compared | Never present an old price as current | `alternatives.FRESH_DAYS`, `STALE_DAYS` |
| A7 | "Cheaper" requires ingredient similarity ≥ 0.3 | Spec: cheaper "while maintaining meaningful similarity" | `MIN_SIMILARITY_FOR_CHEAPER` |
| A8 | Image limits: 8 MB, ≥ 480 px shortest side, ≤ 40 MP; blur variance ≥ 60; mean luminance 50–215 | Practical defaults, to be tuned on real photos | `domain/images.py` |
| A9 | Observations below 0.5 confidence are shown but not mapped to recommendations | Spec §12.3: low-confidence shown as low or suppressed | `domain/skin.py::LOW_CONFIDENCE` |
| A10 | OCR below mean word confidence 80 → `pending_review`; the user confirms the text in every case | OCR is never ground truth | `domain/ocr.py::REVIEW_THRESHOLD` |
| A11 | Face-presence check reports `not_performed` when no detector model is installed | No model available here; must not silently pass | `SKINSYNC_FACE_CASCADE` env var |
| A12 | Shared key actives are a factual INFO finding with evidence `unknown`; they do not raise the status | Raising it would be an unreviewed scientific claim (ADR 0002) | `domain/compatibility.py` |
| A13 | Observed OBF ingredient strings become unreviewed ingredient records when seen in ≥ 5 products from ≥ 2 brands | Gives real data a usable vocabulary without inventing functions | `ingest/obf.py --min-products/--min-brands` |
| A14 | "INCI / common name" labels resolve to the first-written name at confidence 0.8, flagged for review | Standard label convention | `domain/ingredients.py` |
| A15 | Evidence graded insufficient/unknown cannot support a published rule | "Unsupported claims stay unpublished" | `services/knowledge.publish_blockers` |
| A16 | Guest comparisons and searches deleted after 30 days unless saved/shared; guest skin analyses after 7 days | Minimal retention | `jobs.retention_cleanup` |
| A17 | Email must be verified before first sign-in | Prevents account enumeration (ADR 0008) | `api/auth.py` |
| A18 | Retail category mapping from OBF tags is a YAML list, first match wins | Editable without code | `ingest/obf_categories.yaml` |
| A19 | Default skin adapter is `heuristic-0.1`: uncalibrated colour/texture statistics, labelled "not validated", confidence ≤ 0.6; face detection is advisory | Owner chose "simple image heuristics" with no model or dataset available | `domain/skin_heuristics.py`, `docs/model-evaluation.md` |
| A20 | Random INR test prices (149–1949, deterministic per product) for products with no price, dev/test only and badged | Owner asked for random values for testing | `cli.seed_test_prices`, `services/catalog.TEST_PRICE_SOURCE` |
| A21 | AI-drafted rules and evidence stay `draft` and block publishing until a human reviewer marks them reviewed | Owner asked for drafts for review; no invented science goes live | `knowledge/rules.yaml`, `services/knowledge.publish_blockers` |
| A22 | A "compatible" pair needs no rule; the engine reports concerns only, and absence of a rule reads "no notable interaction identified in the current knowledge base" | Engine design; avoids asserting safety | `domain/compatibility.evaluate` |
| A23 | Rows from external datasets become rules only with a source we opened and checked; unsupported rows go to `knowledge/review/pending-rules.md` | Two of the CSV's PubMed citations did not test the pairs they were cited for | `scripts/crosswalk_datasets.py` |
| A24 | Third-party app content (Skinzy) is used to cross-check only; its explanatory text is not stored or shown | Copyright and provenance | `knowledge/review/skinzy-crosscheck.csv` |
