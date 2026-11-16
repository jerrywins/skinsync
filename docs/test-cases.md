# Test cases

Generated from the test suites on 2026-11-05 (`pytest --collect-only`, `playwright test --list`).
IDs in test names trace to the spec: FR-xx, SC-xx, C01–C07 (SkinIQ compatibility cases), NFR-xx.

## Backend: 119 tests (pytest, real PostgreSQL 16 + Redis)

### `api/test_api_core.py` (23)

- `test_health_ready_and_request_ids`
- `test_error_envelope_and_unknown_route`
- `test_fr01_search_typo_tolerant_and_filters`
- `test_validation_rejects_unknown_fields`
- `test_product_detail_has_provenance_versions_and_unresolved`
- `test_barcode_lookup`
- `test_ingredient_detail_and_normalize`
- `test_sc01_demo_comparison_caution_with_evidence_and_why`
- `test_strong_caution_and_reproducible_by_id`
- `test_determinism_and_cache_hit`
- `test_real_products_with_no_reviewed_rules_return_insufficient_evidence`
- `test_c04_c05_unknown_or_missing_ingredients_never_clear`
- `test_demo_and_real_products_cannot_be_mixed`
- `test_manual_ingredient_entry_is_compared_but_not_persisted`
- `test_nfr03_redis_outage_does_not_break_search_or_compare`
- `test_nfr03_queue_outage_only_affects_async_features`
- `test_fr15_cheaper_alternatives_with_prices_and_reasons`
- `test_fr15_premium_and_similar`
- `test_unavailable_price_never_invented`
- `test_alternatives_reference_without_ingredients_is_explained`
- `test_routine_compatible_requires_sign_in`
- `test_user_report_creates_flag`
- `test_events_accept_only_allowlisted_names_without_pii`

### `api/test_api_users.py` (22)

- `test_signup_does_not_reveal_existing_accounts`
- `test_signup_requires_age_and_strong_password`
- `test_login_requires_verified_email_and_hides_which_part_failed`
- `test_session_cookies_are_httponly`
- `test_csrf_required_on_state_changing_requests`
- `test_refresh_rotation_and_reuse_detection`
- `test_login_rate_limited`
- `test_password_reset_single_use`
- `test_fr17_shelf_add_duplicate_remove`
- `test_guest_cannot_use_personal_features`
- `test_fr18_sc04_routine_build_and_analyze`
- `test_save_comparison_claim_and_history`
- `test_idor_other_users_data_is_invisible`
- `test_fr19_share_revoke_and_skin_refusal`
- `test_sc02_guest_skin_analysis_full_pipeline_and_privacy`
- `test_fr07_invalid_skin_images_rejected_with_guidance`
- `test_registered_user_keeps_image_then_deletes_it`
- `test_ocr_label_scan_confirm_and_candidates`
- `test_admin_routes_require_admin`
- `test_sc05_knowledge_import_review_publish_and_audit`
- `test_admin_corrects_mapping_creates_new_version_and_outdates_results`
- `test_fr20_account_deletion_removes_everything`

### `test_alternatives.py` (16)

- `test_fr14_similar_ranks_closest_formula_first`
- `test_reference_and_duplicates_are_removed`
- `test_fr15_cheaper_requires_fresh_comparable_price_and_lower_amount`
- `test_no_cheaper_alternatives_returns_empty_with_reasons`
- `test_fr15_premium_mode`
- `test_missing_price_is_shown_unavailable_never_invented`
- `test_stale_price_is_flagged`
- `test_currency_mismatch_is_not_compared`
- `test_hard_filters_category_avoid_ingredient_missing_data`
- `test_fr16_routine_compatible_drops_conflicts`
- `test_ingredient_focused_requires_target`
- `test_unavailable_dimensions_are_excluded_not_scored_as_zero`
- `test_ranking_is_stable_and_deterministic`
- `test_low_identification_confidence_is_flagged`
- `test_weighted_overlap_bounds`
- `test_personalization_never_changes_compatibility`

### `test_compatibility.py` (23)

- `test_c01_identical_product_reports_shared_key_active`
- `test_c02_known_interaction_gives_caution_with_evidence`
- `test_rules_are_symmetric`
- `test_strong_caution_by_function_class`
- `test_c03_no_relevant_rule_gives_no_notable_interaction_with_exact_wording`
- `test_c04_missing_ingredient_list_is_data_incomplete`
- `test_c05_unknown_ingredient_is_unresolved_and_never_clear`
- `test_fired_rule_outranks_incomplete_data_but_still_lists_it`
- `test_c06_result_is_bound_to_formulation_versions`
- `test_c07_malformed_product_is_a_validation_error`
- `test_empty_knowledge_returns_insufficient_evidence_not_a_verdict`
- `test_confidence_and_evidence_strength_are_separate_fields`
- `test_determinism_same_inputs_byte_identical`
- `test_property_status_never_clear_when_anything_unresolved`
- `test_routine_pairwise`
- `test_fixture_knowledge_refused_by_real_loader`
- `test_fixture_source_type_refused_even_without_header`
- `test_rule_without_existing_evidence_is_rejected`
- `test_rule_with_no_evidence_list_is_rejected`
- `test_explanation_template_rejects_unknown_placeholders`
- `test_shipped_real_knowledge_loads_and_is_empty`
- `test_max_position_condition`
- `test_is_conclusive_only_for_rules_with_high_or_moderate_evidence`

### `test_normalization.py` (14)

- `test_fr03_parse_preserves_order_and_strips_prefix`
- `test_fr03_commas_inside_parentheses_do_not_split`
- `test_fr03_may_contain_section_is_marked`
- `test_fr03_concentration_is_captured`
- `test_fr03_exact_and_alias_match`
- `test_fr03_component_match_for_parenthetical`
- `test_fr03_fuzzy_similarity_only_suggests_never_resolves`
- `test_fr03_no_suggestion_when_numbers_differ`
- `test_parser_drops_entries_without_letters`
- `test_c05_unknown_ingredient_stays_unresolved`
- `test_fr03_slash_names_resolve_to_first_name_with_review`
- `test_fr03_ambiguous_components_without_first_match_stay_unresolved`
- `test_normalize_key_strips_accents_and_case`
- `test_empty_list_parses_to_nothing`

### `test_schema_sql.py` (1)

- `test_migration_applies_and_constraints_hold`

### `test_skin_and_images.py` (20)

- `test_fr07_good_image_is_accepted_and_reencoded`
- `test_fr07_png_and_webp_accepted`
- `test_exif_and_gps_metadata_are_stripped`
- `test_fr07_malicious_or_wrong_files_rejected[-EMPTY_FILE]`
- `test_fr07_malicious_or_wrong_files_rejected[data1-UNSUPPORTED_TYPE]`
- `test_fr07_malicious_or_wrong_files_rejected[%PDF-1.7 not an image-UNSUPPORTED_TYPE]`
- `test_fr07_malicious_or_wrong_files_rejected[data3-CORRUPT_IMAGE]`
- `test_oversized_file_rejected`
- `test_decompression_bomb_rejected`
- `test_low_resolution_rejected`
- `test_blurry_rejected`
- `test_too_dark_and_too_bright_rejected`
- `test_mock_adapter_is_deterministic_labelled_and_cosmetic_only`
- `test_observation_vocabulary_names_no_conditions`
- `test_adapter_output_is_validated`
- `test_unavailable_adapter_never_fakes_results`
- `test_fr10_concern_mapping_separates_confidence_from_evidence`
- `test_concern_mapping_requires_evidence_and_rejects_medical_terms`
- `test_ocr_extracts_label_text_and_reports_confidence`
- `test_ocr_blank_image_goes_to_review`

## End-to-end: 14 tests (Playwright + axe, production build)

- [desktop] › account.spec.ts:6:5 › SC-04 shelf, routine build and analyze
- [desktop] › account.spec.ts:24:5 › save, history, share and revoke
- [desktop] › account.spec.ts:44:5 › personal pages require sign-in
- [desktop] › account.spec.ts:51:5 › SC-05 admin sees data quality and knowledge versions; non-admin cannot
- [desktop] › guest.spec.ts:6:5 › SC-01 guest compares two products and inspects evidence @mobile
- [desktop] › guest.spec.ts:20:5 › C05 unknown ingredient is never shown as clear
- [desktop] › guest.spec.ts:29:5 › manual ingredient entry compares without saving
- [desktop] › guest.spec.ts:38:5 › SC-03 cheaper alternatives show prices, dates and reasons
- [desktop] › guest.spec.ts:56:5 › real product search, product page and provenance
- [desktop] › guest.spec.ts:66:5 › SC-02 guest skin analysis with demo model, then delete
- [desktop] › guest.spec.ts:82:5 › invalid upload is rejected with guidance
- [desktop] › guest.spec.ts:92:5 › security headers and CSP are set
- [desktop] › guest.spec.ts:103:5 › static and SEO pages are accessible
- [mobile] › guest.spec.ts:6:5 › SC-01 guest compares two products and inspects evidence @mobile
