# Data dictionary

All tables live in PostgreSQL (`apps/api/migrations/`). Personal data is marked **P**; sensitive personal
data **S**. Every table with a `user_id` cascades on account deletion.

| Table | Purpose | Notable columns | Personal |
|---|---|---|---|
| users | Accounts | email (unique, case-insensitive), password_hash (Argon2id), role, email_verified_at, age_confirmed_18 | P |
| profiles | Preferences | skin_type, preferences (budget, brands, avoided ingredients, fragrance-free) | P |
| consents | Consent history | purpose (terms, skin_image_processing, analytics), policy_version, granted, recorded_at | P |
| refresh_tokens | Rotating sessions | family_id, token_hash (SHA-256 only), used_at, revoked_at | P |
| auth_tokens | Email verify / reset | token_hash, purpose, expires_at, used_at (single use) | P |
| import_runs | Import provenance | source, licence, counts | |
| brands | Brand names | name, slug | |
| products | Catalogue | slug, name, category, market, image_url (remote), is_demo, source, source_ref, retrieved_at | |
| product_identifiers | Barcodes | kind, value | |
| product_versions | Formulations | raw_ingredients (as received, NULL = no list), ingredients_hash, observed_at, completeness, verification, is_current | |
| ingredients | Ingredient master | id, inci_name, function_classes (empty = unknown), reviewed_at, is_demo, source | |
| ingredient_aliases | Name lookup | alias_key (normalised), alias | |
| product_ingredients | Normalised entries | position, raw_name, ingredient_id (NULL = unresolved), method, confidence, review_status, stated_role, concentration_pct, is_key_active | |
| price_observations | Observed prices | amount, currency, seller, source, available, observed_at | |
| knowledge_versions | Knowledge lifecycle | status (draft, in_review, published, retired), is_demo, published_at/by | |
| evidence_records | Evidence | claim, source_type, citation, strength (high…unknown), reviewer | |
| interaction_rules | Rules | interaction_type, severity, side_a/side_b (terms), mechanism, guidance, explanation_template | |
| rule_evidence | Rule ↔ evidence | (version, rule, evidence) | |
| concern_mappings | Observation → ingredient classes | observation, concern_category, ingredient_classes, evidence_ids | |
| comparisons | Comparison results | product_version_a/b, knowledge_version, engine_version, status, confidence, evidence_strength, completeness, result (canonical JSON), saved | P if user_id |
| comparison_findings | Findings | type, severity, rule_code, confidence, evidence_strength, explanation | |
| uploads | Private files | object_key (random), sha256, encrypted (required for skin), delete_after | S |
| skin_analyses | Skin results | skin_type, status, model_version, is_demo_model, result, keep_image, guest_token_hash | S |
| skin_observations | Observations | characteristic, confidence, severity | S |
| recommendations | Suggested products | observation, concern_category, product_id, observation_confidence, evidence_strength | S |
| alternative_searches | Alternatives results | reference product/version, mode, constraints, result, saved | P if user_id |
| product_alternatives | Ranked rows | rank, product_id, score, dimensions | |
| shelf_items | My Shelf | status (owned/wishlist), note | P |
| routines, routine_items | Routines | time_of_day, step_order, step_kind, frequency, note | P |
| ocr_results | Label scans | raw_text, corrected_text, mean_confidence, engine, status, guest_token_hash | P |
| jobs | Background jobs | type, status (queued…cancelled), idempotency_key, retry_count, error_code, progress | |
| shares | Share links | token_hash (SHA-256), target_type (never skin_analysis), revoked_at | P |
| data_quality_flags | Review queue | target_type, target_ref, reason, source, details, status | |
| audit_log | Append-only audit | actor_id (kept after deletion, no email), action, target, old/new, reason, request_id | |
| analytics_events | Funnel events | name (allow-listed), random session_id, route, small metadata; no PII | |

## Controlled vocabularies

* **Compatibility status:** no_notable_interaction, caution, strong_caution, insufficient_evidence, data_incomplete
* **Evidence strength:** high, moderate, limited, insufficient, unknown
* **Confidence level:** high (≥ 0.85), moderate (≥ 0.6), low
* **Normalisation method:** exact, alias_component, fuzzy (not used to resolve), unresolved, manual
* **Skin observations:** visible_shine, visible_pores, fine_lines_appearance, uneven_tone_appearance,
  dark_spots_appearance, visible_redness, under_eye_darkness, visible_blemishes, visible_texture, visible_dryness
