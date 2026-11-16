# Entity-relationship model

Source of truth: `apps/api/migrations/*.sql` (37 tables). This diagram shows the core entities; audit,
analytics, auth-token and job tables are listed in `data-dictionary.md`.

```mermaid
erDiagram
  USERS ||--o| PROFILES : has
  USERS ||--o{ CONSENTS : records
  USERS ||--o{ SHELF_ITEMS : owns
  USERS ||--o{ ROUTINES : owns
  ROUTINES ||--o{ ROUTINE_ITEMS : "ordered steps"
  USERS ||--o{ COMPARISONS : saves
  USERS ||--o{ SKIN_ANALYSES : owns
  USERS ||--o{ ALTERNATIVE_SEARCHES : saves
  USERS ||--o{ SHARES : creates

  BRANDS ||--o{ PRODUCTS : makes
  PRODUCTS ||--o{ PRODUCT_VERSIONS : "formulations over time"
  PRODUCTS ||--o{ PRODUCT_IDENTIFIERS : barcodes
  PRODUCTS ||--o{ PRICE_OBSERVATIONS : "observed prices"
  PRODUCT_VERSIONS ||--o{ PRODUCT_INGREDIENTS : "ordered, normalised"
  INGREDIENTS ||--o{ PRODUCT_INGREDIENTS : "NULL = unresolved"
  INGREDIENTS ||--o{ INGREDIENT_ALIASES : "names"

  KNOWLEDGE_VERSIONS ||--o{ INTERACTION_RULES : contains
  KNOWLEDGE_VERSIONS ||--o{ EVIDENCE_RECORDS : contains
  KNOWLEDGE_VERSIONS ||--o{ CONCERN_MAPPINGS : contains
  INTERACTION_RULES ||--|{ RULE_EVIDENCE : "cites >= 1"
  EVIDENCE_RECORDS ||--o{ RULE_EVIDENCE : supports

  COMPARISONS }o--|| PRODUCT_VERSIONS : "version A"
  COMPARISONS }o--|| PRODUCT_VERSIONS : "version B"
  COMPARISONS }o--|| KNOWLEDGE_VERSIONS : "evaluated with"
  COMPARISONS ||--o{ COMPARISON_FINDINGS : has

  SKIN_ANALYSES ||--o{ SKIN_OBSERVATIONS : has
  SKIN_ANALYSES ||--o{ RECOMMENDATIONS : has
  SKIN_ANALYSES }o--o| UPLOADS : "image (deleted after analysis)"
  ALTERNATIVE_SEARCHES ||--o{ PRODUCT_ALTERNATIVES : ranks
```

## Rules the schema enforces

| Rule | Mechanism |
|---|---|
| An unresolved ingredient has no canonical id and confidence 0 | CHECK on `product_ingredients` |
| One current formulation per product | partial unique index `product_versions_one_current` |
| A rule cannot be published without evidence | trigger `knowledge_publish_guard` |
| Fixture evidence cannot be published as real knowledge | same trigger |
| Published or retired knowledge cannot change | trigger `knowledge_immutable_guard` on rules, evidence, links, mappings |
| Only one published real knowledge version | partial unique index |
| Skin analyses cannot be shared | trigger `shares_no_skin` |
| Skin images must be encrypted | CHECK on `uploads` |
| Guest results cannot be marked saved | CHECK on `comparisons`, `alternative_searches` |
| Deleting a user deletes all personal rows | `ON DELETE CASCADE` on every user FK |
| Audit log is append-only | trigger `audit_append_only` |
| Accounts require 18+ confirmation; emails unique case-insensitively | CHECK + unique index on `lower(email)` |
