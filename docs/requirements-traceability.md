# Requirements traceability

Status key: **Done** (implemented and verified by the named tests), **Dev adapter** (works with a labelled
development adapter), **Awaiting review** (machinery done; needs human-reviewed scientific content),
**Partial**, **Not done**. Verified 2026-11-05: 119 backend tests, 14 E2E tests.

Paths are relative to `apps/api/skinsync/` (api) or `apps/web/src/` (web). Tests: `tests/…` (pytest) and `e2e/…` (Playwright).

## Functional requirements

| ID | Requirement | Pri | Implementation | Tests | Status |
|---|---|---|---|---|---|
| FR-01 | Product search | Med | `services/catalog.search` (trigram, accents, brand, category, ingredient); web `/products`, `ProductPicker` | `test_fr01_search_typo_tolerant_and_filters`; SQL T12; E2E product search | Done |
| FR-02 | Compare two products | High | `domain/compatibility.evaluate`, `services/comparisons`, `POST /comparisons`; web `/compare` | C01–C07, `test_sc01_…`; E2E SC-01 | Done |
| FR-03 | Ingredient normalisation | High | `domain/ingredients`; fuzzy = suggestion only (ADR 0006) | `test_normalization.py` (14) | Done |
| FR-04 | Findings from structured rules | High | `compatibility._evaluate_rule`, `services/knowledge` | C02, strong caution, symmetry, max_position | Done (engine); **Awaiting review** (no real rules) |
| FR-05 | Explain findings, evidence, confidence | High | `Finding.why`, evidence refs; web `CompareResult`, `ExplainPanel` | `test_confidence_and_evidence_strength_are_separate_fields`; E2E "Why was this flagged?" | Done |
| FR-06 | Skin image upload | High | `POST /skin-analyses`, encrypted storage; web `/analyze`, `PhotoInput` | `test_sc02_guest_skin_analysis_…`; E2E SC-02 | Done |
| FR-07 | Image validation | High | `domain/images.validate_and_sanitize` | image tests; `test_fr07_invalid_skin_images_rejected_with_guidance`; E2E invalid upload | Done (face check not performed) |
| FR-08 | Skin observations | High | `SkinModelAdapter`, `MockSkinModelAdapter`, `HeuristicSkinAdapter` | `test_mock_adapter_is_deterministic_labelled_and_cosmetic_only`, `tests/test_skin_heuristics.py`, `test_heuristic_adapter_end_to_end_is_labelled_and_uses_real_knowledge` | **Experimental, not validated** |
| FR-09 | Observation confidence | High | `ObservationView`, `ConfidenceBadge` | concern-map tests, E2E SC-02 | Done |
| FR-10 | Concern mapping | High | `build_concern_map`, `map_concerns` | `test_fr10_concern_mapping_…` | Done (engine); **Awaiting review** |
| FR-11 | Product recommendations | High | `services/recommend.products_for` (classes → products → preferences → routine check) | `test_sc02_…` (demo) | Done with demo data; real mappings **awaiting review** |
| FR-12 | Product image input | Med | `POST /scan/label`, Tesseract adapter; web `/scan` | `test_ocr_label_scan_confirm_and_candidates`, OCR unit tests | Done |
| FR-13 | Identify from search/barcode/OCR | Med | barcode lookup, OCR candidates; web barcode scanner (BarcodeDetector + ZXing) | `test_barcode_lookup`, OCR test | Done (camera untested on a real device) |
| FR-14 | Alternative search | High | `domain/alternatives.rank_alternatives`, `POST /alternatives/search`; web `/alternatives` | `test_alternatives.py`, `test_fr15_…`; E2E SC-03 | Done |
| FR-15 | Cheaper / similar / premium | High | `Mode` | `test_fr15_cheaper_…`, `test_fr15_premium_and_similar` | Done (real products have no prices) |
| FR-16 | Routine-compatible alternatives | Med | routine conflicts via engine | `test_fr16_routine_compatible_drops_conflicts`, sign-in requirement | Done |
| FR-17 | Save products | Med | `/shelf`; web `/shelf` | `test_fr17_shelf_…`; E2E SC-04 | Done |
| FR-18 | Create routines | High | `/routines`, `/routines/{id}/analyze`; web builder with keyboard reordering | `test_fr18_sc04_…`; E2E SC-04 | Done |
| FR-19 | Share; skin private | Low | `/shares`, `/public/shares`, DB trigger | `test_fr19_share_revoke_and_skin_refusal`; SQL T6; E2E share/revoke | Done |
| FR-20 | Account deletion | High | `DELETE /me` + cascades + image deletion | `test_fr20_account_deletion_removes_everything`; SQL T13 | Done |

## Non-functional requirements

| ID | Status | Evidence |
|---|---|---|
| NFR-01 Performance | Done | `PERFORMANCE.md`: search p95 774 ms, cached compare 151 ms, alternatives 978 ms |
| NFR-02 Security | Done (with gaps listed) | `security.md`; auth, CSRF, IDOR, rate-limit, upload tests; Bandit/Ruff/pip-audit/npm audit clean |
| NFR-03 Availability | Done | `test_nfr03_redis_outage_…`, `test_nfr03_queue_outage_…`; readiness `degraded` |
| NFR-04 Maintainability | Done | framework-free domain, typed contracts, generated TS types, ADRs |
| NFR-05 Scalability | Partial | stateless API, worker, indexes, cache; no horizontal-scale test |
| NFR-06 Usability | Done | every flow has loading/empty/partial/error states; recovery actions |
| NFR-07 Accessibility | Done (automated) | axe WCAG 2.1 AA on 15 pages, no serious/critical issues; contrast fixed; keyboard routine reordering. No manual screen-reader audit |
| NFR-08 Privacy | Done | `privacy.md`; encryption, deletion, retention job, consent records |
| NFR-09 Data integrity | Done | provenance columns, versioned formulations, DB constraints (SQL tests) |
| NFR-10 Explainability | Done | `ExplainPanel` on every result; versions stamped; confidence ≠ evidence |

## Story cards and acceptance

| Card | Status |
|---|---|
| SC-01 Compare | Done (API + E2E) |
| SC-02 Analyze skin | Done with the labelled mock model |
| SC-03 Alternatives | Done (API + E2E) |
| SC-04 Routine | Done (API + E2E) |
| SC-05 Review data | Done (API + E2E) |

## Engineering acceptance (spec §19)

| Item | Status |
|---|---|
| Unit / integration / E2E tests | Done (119 + 14) |
| Security check | Done locally (Bandit, Ruff S-rules, pip-audit, npm audit); gitleaks/Trivy in CI, not run here |
| Accessibility check | Automated axe: done |
| CI/CD | Workflow written; **not executed** (no GitHub run from here) |
| Error monitoring | Prometheus metrics + Grafana dashboard provisioned; Sentry not integrated |
