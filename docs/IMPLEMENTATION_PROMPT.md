# SKINIQ — MASTER ENTERPRISE IMPLEMENTATION PROMPT
## Complete Full-Stack Skincare Intelligence Platform
### Three Interconnected Intelligence Pipelines | Production-Oriented Architecture | End-to-End Implementation

---

# 0. YOUR MISSION

You are not being asked to create a website mockup.

You are being commissioned to engineer and deliver **SkinIQ**, a complete, integrated, data-driven skincare intelligence platform.

You must work as a coordinated senior engineering team comprising:

- Principal Software Architect
- Senior Frontend Engineer
- Senior Backend Engineer
- Database Architect
- AI/ML Engineer
- Computer Vision Engineer
- Data Engineer
- Information Retrieval Engineer
- Application Security Engineer
- UI/UX Designer
- QA and Automation Engineer
- DevOps Engineer

You are responsible for the complete implementation, integration, verification and documentation of the application.

Your final output must be a working software system.

Do not stop after producing:
- An architecture proposal.
- A project plan.
- A collection of code snippets.
- A homepage.
- A frontend prototype.
- A set of disconnected features.

You must actually inspect, create, modify, execute, test and integrate the project files using the tools available in your environment.

**Primary objective: Build the complete SkinIQ application described in the attached master specification.**

# 1. AUTHORITATIVE PRODUCT SPECIFICATION

The attached document:

`SkinIQ_10_10_Master_Product_Specification.md`

is the source of truth.

It contains 198 numbered sections covering the product vision, features, architecture, data model, AI/ML, workflows, engineering, testing, deployment and growth.

## Mandatory reading instructions

Before writing code:

1. Read the entire specification.
2. Understand all 198 sections.
3. Understand the three primary user questions.
4. Understand the complete end-to-end workflows.
5. Understand the shared product and ingredient knowledge infrastructure.
6. Understand the database relationships.
7. Understand the API contracts.
8. Understand the AI/ML boundaries.
9. Understand the implementation priorities.
10. Understand the final acceptance criteria.

Do not make implementation decisions based solely on this prompt when the original specification contains more detailed requirements.

The original document takes precedence over any abbreviated descriptions here.

Create a requirements traceability matrix connecting each applicable specification requirement to:
- Requirement ID.
- Description.
- Priority.
- Module.
- Implementation location.
- API/database dependency.
- Test case.
- Completion status.

Do not silently omit requirements.

If two requirements appear inconsistent, record the conflict in an Architecture Decision Record (ADR), explain the decision and preserve the original product intent.

If an external dependency is unavailable, distinguish between:
- Implemented.
- Implemented with a development adapter.
- Awaiting external credentials.
- Awaiting model weights or dataset.
- Awaiting human scientific review.
- Not implemented.

Never misrepresent the completion status.

# 2. PRODUCT DEFINITION

SkinIQ is an evidence-aware skincare intelligence platform.

Its product promise:

**Understand your skin. Understand your products. Make better skincare decisions.**

It answers three primary questions:

A. What does my skin appear to need?

B. Can I use these two skincare products together?

C. What are my alternatives to this product?

These are the three primary intelligence pipelines.

Product discovery, ingredient intelligence, product identification, OCR, evidence management and personalization are shared supporting capabilities.

Do not build three independent applications.

Build one unified platform with three interconnected intelligence systems.

# 3. CORE ARCHITECTURAL PRINCIPLE

The entire platform must follow:

USER INPUT
↓
DATA INGESTION
↓
STRUCTURED REPRESENTATION
↓
NORMALIZATION
↓
PRODUCT / INGREDIENT KNOWLEDGE
↓
EVIDENCE
↓
DETERMINISTIC DOMAIN LOGIC
↓
PERSONALIZATION
↓
TRANSPARENT EXPLANATION
↓
USER DECISION

AI may assist with:
- Perception.
- Extraction.
- Classification.
- Identification.
- Explanation.

However, high-impact skincare conclusions must be grounded in structured data, explicit rules, confidence, provenance and evidence.

The LLM must never become the source of scientific truth.

# 4. SYSTEM ARCHITECTURE

Use a modular monolith.

Do not introduce microservices without a concrete technical justification.

Recommended architecture:

BROWSER
  |
  v
NEXT.JS FRONTEND
  |
  v
FASTAPI APPLICATION API
  |
  +-------------------------------+
  |                               |
  v                               v
APPLICATION SERVICES         AUTHENTICATION
  |
  +----------+-----------+-----------+
  |          |           |           |
  v          v           v           v
PRODUCT   INGREDIENT   EVIDENCE   USER DATA
INTEL.    INTEL.       LAYER      SERVICES
  |          |           |
  +----------+-----------+
             |
      DOMAIN ENGINES
             |
     +-------+-------+
     |       |       |
     v       v       v
   SKIN   COMPAT. ALTERNATIVES
   ENGINE ENGINE   ENGINE
     |       |       |
     +-------+-------+
             |
       RECOMMENDATION
          /      \
         v        v
      ROUTINE   MY SHELF

Infrastructure:
- PostgreSQL.
- Redis.
- Private object storage.
- Background workers.
- ML inference adapters.
- OCR adapters.
- Monitoring and logging.

Recommended stack:

Frontend:
- Next.js.
- React.
- TypeScript.
- Tailwind CSS.
- Accessible component primitives.
- React Hook Form or equivalent.
- Zod.
- TanStack Query where useful.

Backend:
- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- PostgreSQL.
- Redis.
- Background worker system.
- Object storage.

Deployment options should be selected after repository and environment inspection.

Supabase is an acceptable option for managed PostgreSQL, Auth and Storage.

Vercel is an acceptable option for the Next.js frontend.

Do not introduce unnecessary infrastructure.

# 5. FIRST EXECUTION STAGE — REPOSITORY AUDIT

Before implementation, inspect the existing project.

Determine:

- Existing frontend framework.
- Existing backend.
- Existing repository structure.
- Existing pages and components.
- Existing APIs.
- Existing database.
- Existing migrations.
- Existing authentication.
- Existing model files.
- Existing datasets.
- Existing integrations.
- Existing environment variables.
- Existing tests.
- Existing deployment configuration.

Identify:
1. Working implementations.
2. Partially implemented features.
3. Broken functionality.
4. Missing functionality.
5. Duplicate code.
6. Architectural problems.
7. Dependencies that are unavailable.

Do not overwrite functional code without understanding it.

Do not assume a clean repository.

Create:

`docs/implementation-audit.md`

`docs/architecture-decisions/`

`docs/requirements-traceability.md`

`docs/implementation-roadmap.md`

After the audit, establish the implementation plan and begin actual execution.

# 6. SHARED FOUNDATION — PRODUCT AND INGREDIENT INTELLIGENCE

This is the most important dependency in the entire system.

All three pipelines must use the same canonical product and ingredient data.

## 6.1 Product intelligence

A product must contain:

- Product ID.
- Brand.
- Name.
- Category.
- Country/market.
- Identifiers and barcodes.
- Product images.
- Product versions.
- Ingredient lists.
- Product sources.
- Price observations.
- Availability.
- Creation and modification timestamps.

A product is not merely a product name.

## 6.2 Product formulation versioning

Implement:

Product
  ├── Formulation Version A
  ├── Formulation Version B
  └── Formulation Version C

Each version must preserve:
- Ingredient list.
- Market.
- Source.
- Observed date.
- Formulation notes.
- Verification status.

Do not compare two products using unverified or mismatched formulations.

## 6.3 Product provenance

Important product fields must have:

- Source.
- Source type.
- Retrieved timestamp.
- Confidence.
- Verification status.

## 6.4 Ingredient intelligence

Implement:
- Canonical INCI names.
- Common names.
- Aliases.
- Ingredient categories.
- Ingredient functions.
- Product relationships.
- Evidence relationships.

Normalization:

Raw ingredient
→ Cleaning
→ Alias lookup
→ Candidate resolution
→ Canonical ingredient
→ Confidence
→ Provenance
→ Review status

Preserve:
- Original text.
- Canonical ID.
- Ingredient position.
- Normalization method.
- Confidence.
- Source.
- Review status.

Unknown ingredients must remain unknown.

Never silently assign an unknown ingredient to an arbitrary canonical record.

## 6.5 Evidence intelligence

Implement a separate evidence layer.

Each evidence record should contain:

- ID.
- Claim.
- Source type.
- Source reference.
- Publication date.
- Retrieved date.
- Evidence strength.
- Review status.
- Reviewer.
- Notes.

Controlled evidence values:

- High.
- Moderate.
- Limited.
- Insufficient.
- Unknown.

Evidence strength must never be confused with model confidence.

## 6.6 Knowledge versioning

Implement versioned knowledge.

Every important compatibility and recommendation result must record:
- Knowledge version.
- Engine version.
- Product formulation versions.
- Relevant source records.
- Creation timestamp.

Historical results must remain reproducible.

# 7. THREE INDEPENDENT INTELLIGENCE PIPELINES

These pipelines must have independently testable domain services, APIs and result models.

They must share the same underlying product and ingredient infrastructure.

## PIPELINE A — SKIN ANALYSIS

User question:

"What does my skin appear to need?"

Complete flow:

User
↓
Select skin type
↓
Capture/upload image
↓
Secure upload
↓
File validation
↓
Image decoding
↓
Image quality assessment
↓
ML inference
↓
Structured observations
↓
Confidence
↓
Concern mapping
↓
Evidence retrieval
↓
Ingredient category recommendations
↓
Product retrieval
↓
User preference filtering
↓
Routine compatibility
↓
Recommendation ranking
↓
Explanation
↓
Results
↓
Save / Compare / Routine / Alternatives

### A.1 Skin type input

Support:

- Dry.
- Oily.
- Combination.
- Normal.
- Sensitive/easily irritated.
- Unsure.

Never force a user to select a skin type.

### A.2 Image upload

Support:
- JPEG.
- PNG.
- WebP.

Validate:
- Extension.
- MIME type.
- Actual signature.
- File size.
- Dimensions.
- Image decoding.
- Corruption.
- Unsafe files.

Apply secure filenames, upload restrictions and access control.

### A.3 Image quality

Assess:

- Poor lighting.
- Excessive brightness.
- Blur.
- Resolution.
- Face/skin visibility.
- Distance.
- Obstruction.
- Possible filters.

If the image is unsuitable, reject it with a useful explanation and retake instructions.

### A.4 Computer vision

Initial cosmetic observations:

- Fine lines/wrinkles.
- Visible pores.
- Dark circles.
- Acne/acne-like visible lesions.
- Acne marks.
- Pigmentation/dark spots.
- Uneven-looking tone.
- Redness where model performance supports it.

Implement a replaceable interface:

`SkinAnalysisModel.analyze(image) -> SkinAnalysisOutput`

Structured output:

- Concern.
- Confidence.
- Severity estimate.
- Model version.

### A.5 Model feasibility gate

Before claiming actual skin analysis:

1. Inspect available model files.
2. Inspect available datasets.
3. Identify model architecture.
4. Identify preprocessing requirements.
5. Verify input/output compatibility.
6. Test inference.
7. Evaluate per-concern performance.
8. Assess calibration.
9. Assess false positives.
10. Evaluate performance variation across skin tones, lighting, camera quality, age ranges and image angles.

Track:
- Precision.
- Recall.
- F1.
- Calibration.
- False-positive rate.

If a validated model is unavailable, implement the model adapter and a clearly labelled development-only adapter.

Never generate arbitrary fake observations and present them as real inference.

### A.6 Recommendation engine

Separate observation from recommendation.

Observation
→ Concern mapping
→ Ingredient category mapping
→ Evidence filtering
→ Product retrieval
→ User preference filtering
→ Routine compatibility
→ Ranking
→ Explanation

Store separately:

- Image observation confidence.
- Ingredient evidence strength.
- Product-data confidence.

### A.7 Results interface

Display:
- Image.
- Skin type.
- Visible observations.
- Confidence.
- Severity estimate where supported.
- Relevant ingredient categories.
- Supporting evidence.
- Product recommendations.
- Explanation.
- Data limitations.
- Cosmetic-use disclaimer.

Allow:
- Product detail.
- Alternative discovery.
- Product comparison.
- Save.
- Routine creation.
- History.

---

## PIPELINE B — PRODUCT COMPATIBILITY

User question:

"Can I use these two products together?"

This must be a deterministic, structured domain engine.

Complete flow:

Product A
→ Product resolution
→ Formulation version
→ Ingredient retrieval
→ Ingredient normalization

Product B
→ Product resolution
→ Formulation version
→ Ingredient retrieval
→ Ingredient normalization

Both
→ Pairwise rule evaluation
→ Evidence retrieval
→ Confidence calculation
→ Structured result
→ Explanation
→ Save / Share / Routine

### B.1 Product selection

Support:
- Product search.
- Brand search.
- Product category.
- Ingredient search.
- Saved products.
- Product image.
- Manual ingredient entry.
- Barcode where supported.

Ambiguous matches must require confirmation.

### B.2 Formulation resolution

Resolve the actual formulation before comparison.

Never assume all products with the same name have identical ingredient lists.

### B.3 Compatibility taxonomy

Use exactly the specification's controlled result categories:

1. No notable interaction identified.
2. Potential interaction / caution.
3. Strong caution.
4. Insufficient evidence.
5. Data incomplete.

No notable interaction does not mean universally safe.

### B.4 Interaction engine

Implement deterministic pairwise evaluation.

Interaction types:

- Redundancy.
- Irritation concern.
- Formulation conflict.
- pH-sensitive concern.
- Duplicate active load.
- Evidence-limited interaction.
- No notable concern.

Each rule must contain:

- Ingredient A.
- Ingredient B.
- Interaction type.
- Severity.
- Evidence strength.
- Mechanism summary.
- Practical guidance.
- Source IDs.
- Review status.
- Last reviewed.
- Knowledge version.

Rules must be curated, source-backed and human-reviewable.

Do not invent scientific interaction rules.

### B.5 Result confidence

Account for:

- Formulation completeness.
- Ingredient normalization.
- Evidence coverage.
- Rule applicability.

Do not use arbitrary averages.

### B.6 Comparison result interface

Display:

- Product A.
- Product B.
- Formulation versions.
- Shared ingredients.
- Product A-only ingredients.
- Product B-only ingredients.
- Unresolved ingredients.
- Compatibility status.
- Findings.
- Evidence strength.
- Confidence.
- Practical guidance.
- Knowledge version.

Each finding must have a "Why was this flagged?" explanation.

Provide access to the underlying evidence.

Never display a meaningless universal safety score.

---

## PIPELINE C — PRODUCT ALTERNATIVES

User question:

"What are my alternatives to this product?"

Complete flow:

Product name / image / barcode / URL where supported / saved product
↓
Product identification
↓
Candidate confirmation
↓
Canonical product
↓
Formulation resolution
↓
Feature extraction
↓
Candidate retrieval
↓
Duplicate removal
↓
Hard filters
↓
Similarity evaluation
↓
Target matching
↓
Price enrichment
↓
Preference matching
↓
Routine compatibility
↓
Ranking
↓
Explanation
↓
Compare / Save

### C.1 Identification

Support:
- Product name.
- Brand.
- Product image.
- Barcode.
- Ingredient image.
- Manual ingredient entry.
- Saved products.
- Product URL where supported.

Identification architecture:

Image
→ OCR
→ Visual features
→ Candidate retrieval
→ Text similarity
→ Brand/product matching
→ Candidate ranking
→ User confirmation

Never silently choose an uncertain candidate.

### C.2 Candidate retrieval

Retrieve actual products from the shared product database.

Never generate fictional alternatives.

### C.3 Alternative categories

Support:

1. Cheaper.
2. Similar.
3. Premium.
4. Ingredient-focused.
5. Routine-compatible.
6. Sensitive-preference.

### C.4 Hard filtering

Exclude:
- Incorrect categories.
- Reference product.
- Duplicate candidates.
- User-excluded products.
- Candidates lacking mandatory comparison data.

### C.5 Ranking

Expose:

- Ingredient similarity.
- Target ingredient match.
- Product category match.
- Formulation similarity.
- Price difference.
- Routine compatibility.
- Preference match.
- Data confidence.

Initial configurable conceptual formula:

Similarity =
0.35 × ingredient_similarity
+ 0.20 × target_match
+ 0.15 × category_match
+ 0.15 × preference_match
+ 0.15 × formulation_similarity

These weights are design parameters, not scientific facts.

Validate ranking through tests and document the methodology.

### C.6 Price observations

Store:

- Product ID.
- Seller.
- Country.
- Currency.
- Price.
- Availability.
- Source.
- Observed timestamp.

Display price freshness.

If no trustworthy price exists, display "Price unavailable."

Never invent prices.

### C.7 Result interface

Every result must explain:

- Why it was retrieved.
- Why it is similar.
- Why it is cheaper, where applicable.
- Target ingredient match.
- Differences in formulation.
- Routine compatibility.
- Missing data.
- Confidence.

Provide filters and direct comparison using Pipeline B.

# 8. CROSS-PIPELINE INTEGRATION

This is one of the highest-priority engineering requirements.

A user must be able to move between all three pipelines without repeating unnecessary information.

Required integrations:

Skin analysis
→ Concern
→ Ingredient category
→ Recommended product
→ Product detail
→ Alternatives
→ Compatibility
→ Routine
→ My Shelf.

Product comparison
→ Ingredient findings
→ Evidence
→ Save comparison
→ Add to routine
→ Recheck routine.

Alternative discovery
→ Candidate product
→ Comparison
→ Compatibility
→ Save
→ My Shelf.

Routine
→ Formulation resolution
→ Ingredient extraction
→ Compatibility
→ Duplication analysis
→ User preferences
→ Result.

Implement shared IDs and typed contracts.

Do not pass entire frontend components or arbitrary text between services.

# 9. SUPPORTING PRODUCT FEATURES

Implement the following.

## 9.1 Product search

Search by:
- Product.
- Brand.
- Category.
- Active ingredient.
- Partial names.
- Common misspellings.
- INCI names.

Use PostgreSQL full-text search, trigram matching and indexed aliases initially.

## 9.2 Product scanner

Support:

1. Camera permission.
2. Camera ready.
3. Barcode detection.
4. Product lookup.
5. Ambiguous result.
6. Unavailable product.
7. Retry.

Provide image and manual-entry fallbacks.

## 9.3 OCR

Image
→ OCR
→ Raw text
→ Cleaning
→ Ingredient segmentation
→ INCI normalization
→ Match confidence
→ Human review
→ Canonical ingredient list.

Implement a provider adapter.

OCR must never be considered ground truth.

Provide accept, edit, replace and remove actions.

## 9.4 Ingredient explorer

Provide ingredient search and detail pages.

Show:
- INCI name.
- Common names.
- Functions.
- Product types.
- Relevant considerations.
- Related ingredients.
- Products containing it.
- Evidence.

## 9.5 Product detail

Show:
- Brand.
- Name.
- Category.
- Image.
- Formulation.
- Ingredients.
- Functions.
- Data confidence.
- Source.
- Last verified date.
- Compatibility.
- Alternatives.
- Routine action.
- Save action.

# 10. PERSONALIZATION

## 10.1 User preferences

Support optional:

- Budget.
- Preferred brands.
- Avoided brands.
- Texture.
- Fragrance preference.
- Vegan preference where verified.
- Ingredient preferences.
- Product category.
- Routine complexity.

Do not infer sensitive attributes.

## 10.2 My Shelf

Users can:
- Add products.
- Remove products.
- Search.
- Compare two products.
- Find alternatives.
- Build routines.
- View history.

## 10.3 Routine builder

Morning:
1. Cleanser.
2. Treatment.
3. Serum.
4. Moisturizer.
5. Sunscreen.

Evening:
1. Cleanser.
2. Treatment.
3. Serum.
4. Moisturizer.

Support custom ordering.

## 10.4 Routine analysis

Routine products
→ Formulation resolution
→ Ingredient extraction
→ Pairwise compatibility
→ Duplication analysis
→ User preferences
→ Sequencing considerations
→ Evidence
→ Results.

## 10.5 History and saved results

Support:
- Skin analyses.
- Comparisons.
- Alternative searches.
- Saved products.
- Routines.

Support comprehensive deletion.

# 11. COMPLETE WEBSITE INFORMATION ARCHITECTURE

Implement the routes defined in the specification.

Primary routes:

/
 /analyze
 /compare
 /alternatives
 /products
 /products/[slug]
 /products/[slug]/alternatives
 /ingredients
 /ingredients/[slug]
 /brands/[slug]
 /routine
 /shelf
 /history
 /share/[token]
 /about
 /how-it-works
 /methodology
 /privacy
 /terms
 /admin

Add result-detail routes and account routes where needed.

Do not invent unnecessary page families.

Guest access must be supported for core comparison, product search, public pages, limited skin analysis and alternatives.

Require accounts for persistent personalized functionality.

# 12. UI/UX IMPLEMENTATION

Design a premium, modern skincare intelligence product.

Visual direction:
- Clean.
- Clinical but not sterile.
- Premium.
- Soft.
- Modern.
- Trustworthy.
- Approachable.

Avoid:
- Excessive pink.
- Generic AI dashboard appearance.
- Fake scientific charts.
- Excessive gradients.
- Giant meaningless scores.
- Fear-based warnings.

Create reusable components:

- ProductCard.
- ProductSelector.
- ProductSearch.
- IngredientChip.
- IngredientTable.
- CompatibilityBanner.
- EvidenceCard.
- ConfidenceBadge.
- AlternativeCard.
- PriceBadge.
- SkinObservationCard.
- RecommendationCard.
- RoutineStep.
- ShelfCard.
- UploadDropzone.
- CameraScanner.
- OCRReview.
- LoadingState.
- EmptyState.
- ErrorState.

Every workflow must include:

- Initial state.
- Loading state.
- Success state.
- Empty state.
- Partial-result state.
- Validation failure.
- Server failure.
- Retry.
- Mobile-responsive layout.

Implement accessibility and semantic HTML.

Test actual mobile camera/upload workflows where browser/device access permits.

# 13. BACKEND AND API CONTRACTS

Base:

`/api/v1`

Implement the API families defined in the specification.

Products:
- GET /products
- GET /products/{id}
- POST /products/identify
- POST /products/scan

Ingredients:
- GET /ingredients
- GET /ingredients/{id}

Comparisons:
- POST /comparisons
- GET /comparisons/{id}

Skin:
- POST /skin-analysis
- POST /skin-analysis/{id}/image
- GET /skin-analysis/{id}
- GET /skin-analysis/{id}/recommendations
- DELETE /skin-analysis/{id}

Alternatives:
- POST /alternatives/search
- GET /alternatives/{id}

Routines:
- POST /routines
- GET /routines
- POST /routines/{id}/analyze

Shelf:
- GET /shelf
- POST /shelf
- DELETE /shelf/{productId}

Add appropriate APIs for authentication, user preferences, history, sharing, ingredients, evidence and administration.

Use:
- Request validation.
- Response schemas.
- Pagination.
- Ownership checks.
- Authentication.
- Authorization.
- Consistent errors.
- Request IDs.
- OpenAPI documentation.

Use the error contract from the original specification.

# 14. DATABASE IMPLEMENTATION

Implement relational PostgreSQL migrations.

Core entities:

- users
- profiles
- products
- product_versions
- product_identifiers
- product_sources
- product_images
- ingredients
- ingredient_aliases
- product_ingredients
- evidence_records
- interaction_rules
- skin_analyses
- skin_observations
- recommendations
- alternative_searches
- product_alternatives
- price_observations
- routines
- routine_items
- shelf_items
- comparisons
- comparison_findings
- uploads
- ocr_results
- jobs
- shares
- analytics_events
- admin_reviews
- knowledge_versions

Implement proper:
- Primary keys.
- Foreign keys.
- Unique constraints.
- Indexes.
- Check constraints.
- Timestamps.
- Ownership.
- Audit fields.
- Deletion policies.

Preserve ingredient ordering.

Avoid inappropriate denormalization.

Create:
- Database migrations.
- Seed scripts.
- Development fixtures.
- Migration rollback strategy where practical.

Do not rely on manually created database tables.

# 15. BACKGROUND PROCESSING

Use asynchronous jobs for:

- Skin analysis.
- OCR.
- Product identification.
- Large alternative searches.
- Bulk ingestion.
- Bulk normalization.

Flow:

POST request
→ 202 Accepted
→ Job ID
→ Queue
→ Worker
→ Status updates
→ Result.

Job states:

- queued.
- processing.
- completed.
- failed.
- cancelled.

Implement:
- Retry limits.
- Idempotency.
- Failure handling.
- Timeout handling.
- Job ownership.
- Progress information.
- Dead-letter handling where supported.

Never expose internal stack traces to users.

# 16. AI / LLM / RAG ARCHITECTURE

Use AI only where it provides measurable value.

Possible uses:
- Skin computer vision.
- OCR.
- Product identification.
- Structured extraction.
- Explanation.
- Evidence-grounded question answering.

If an LLM is used:

User input
→ Intent extraction
→ Structured lookup
→ Evidence retrieval
→ Domain engine
→ Structured result
→ LLM explanation
→ Schema validation
→ User response.

The LLM must never:
- Invent formulations.
- Invent evidence.
- Override compatibility results.
- Invent prices.
- Invent products.
- Generate unsupported medical advice.

Use provider adapters.

Validate outputs.

Keep secrets server-side.

# 17. DATA INGESTION AND SOURCE GOVERNANCE

Create a reusable ingestion system.

It must support:
- Product ingestion.
- Ingredient ingestion.
- Alias ingestion.
- Formulation updates.
- Source metadata.
- Duplicate detection.
- Validation.
- Human review.
- Publication.
- Price observations.

Evaluate each external source for:
- API availability.
- Coverage.
- Freshness.
- Licensing.
- Attribution.
- Rate limits.
- Redistribution rights.
- Geographic coverage.

Do not assume publicly accessible data is freely redistributable.

Use traceable seed records for development.

Clearly distinguish verified records, imported records, unverified records and demonstration records.

Do not populate production interfaces with fabricated data.

# 18. ADMIN AND KNOWLEDGE GOVERNANCE

Build an admin interface for:

- Product review.
- Ingredient review.
- OCR review.
- Evidence management.
- Interaction rules.
- Knowledge publication.
- Version history.
- Audit logs.
- Failed jobs.
- Data-quality metrics.

Roles:
- Data reviewer.
- Knowledge reviewer.
- System administrator.

Knowledge updates must be auditable and versioned.

Support draft, review, publication and rollback workflows.

# 19. SECURITY AND PRIVACY

Treat skin images as sensitive content.

Implement:
- Secure authentication.
- Authorization.
- Ownership verification.
- Private storage.
- Upload validation.
- Rate limiting.
- Secret management.
- Input validation.
- SQL injection prevention.
- XSS prevention.
- Appropriate CSRF protection.
- Session security.
- CORS restrictions.
- Audit logging.

Skin images must never be public by default.

Implement consent, retention and deletion policies.

Deleting an analysis must remove:
- Analysis record.
- Observations.
- Recommendations.
- Original image.
- Derived temporary artifacts.

Do not use private images for model training without appropriate explicit consent.

Never log passwords, access tokens or private images.

# 20. MEDICAL AND SCIENTIFIC SAFETY

SkinIQ is a cosmetic decision-support platform.

It is not a medical diagnosis system.

Never:
- Diagnose dermatological conditions.
- Prescribe medication.
- Guarantee treatment outcomes.
- Claim universal product safety.
- Invent scientific evidence.

Use careful wording.

"Visible cosmetic observation."

"Potential caution identified."

"No notable interaction identified in the current knowledge base."

"Data is insufficient for a confident conclusion."

Include appropriate disclaimers.

# 21. SEO, SHARING AND GROWTH

Implement:

- Metadata.
- Open Graph.
- Canonical URLs.
- Sitemap.
- Robots.
- Structured data.
- Product pages.
- Ingredient pages.
- Brand pages.
- High-quality comparison pages.
- Educational content.

Index only useful, sufficiently complete public pages.

Noindex:
- Private analyses.
- Dashboards.
- Empty searches.
- Temporary jobs.
- Low-quality filter combinations.

Implement secure public sharing.

Skin analyses remain private by default.

Analytics must cover the events listed in the original specification.

Do not collect unnecessary sensitive data.

Measure:
- Acquisition.
- Activation.
- Engagement.
- Retention.
- Conversion.

# 22. PERFORMANCE AND OBSERVABILITY

Measure:
- API latency.
- Database latency.
- OCR latency.
- ML inference latency.
- Job failure rate.
- Queue depth.
- Cache hit rate.
- Upload failures.
- Error rate.

Implement:
- Structured logs.
- Request IDs.
- Health checks.
- Monitoring.
- Error reporting.
- Database indexing.
- Appropriate caching.
- Image optimization.
- Asynchronous expensive processing.

Use caching only with correct user isolation.

Invalidate results when relevant product versions, evidence, knowledge versions or price observations change.

# 23. TESTING STRATEGY

Testing is a release requirement.

## Unit testing

Test:

- normalize_ingredient()
- resolve_alias()
- compare_ingredients()
- evaluate_interaction()
- rank_alternatives()
- calculate_similarity()
- validate_upload()
- map_concern_to_category()

## Compatibility testing

C01: Identical product → duplication identified.

C02: Known interaction → caution.

C03: No relevant rule → no notable interaction, subject to data completeness.

C04: Missing ingredients → insufficient data.

C05: Unknown ingredients → unresolved.

C06: Historical formulation → version-specific result.

C07: Malformed product → validation error.

## Skin testing

Test:
- Valid image.
- Invalid file.
- Poor lighting.
- Blur.
- Unsupported format.
- Low-confidence observation.
- Multiple observations.
- No observation.
- Model timeout.
- Model failure.
- Deletion.

## Alternative testing

Test:
- Exact product.
- Ambiguous product.
- No match.
- Cheaper alternatives.
- No cheaper alternatives.
- Missing price.
- Stale price.
- Duplicate candidates.
- Low ingredient confidence.
- Ranking stability.

## OCR testing

Test:
- Clear ingredient list.
- Curved packaging.
- Low light.
- Blurry text.
- Multiple columns.
- Punctuation.
- OCR errors.
- Unknown ingredients.
- Duplicate ingredients.
- Manual correction.

## Integration testing

Test every connection:

Product → Ingredient normalization.

Product → Compatibility.

Skin analysis → Recommendations.

Recommendations → Product retrieval.

Product → Alternatives.

Alternative → Compatibility.

Shelf → Routine.

Routine → Compatibility.

## E2E scenario 1

Homepage
→ Skin analysis
→ Upload
→ Validation
→ Supported observations
→ Recommendations
→ Product detail
→ Alternatives
→ Compatibility.

## E2E scenario 2

Homepage
→ Compare
→ Product A
→ Product B
→ Compatibility
→ Evidence
→ Save
→ Sign in
→ Persistent result.

## E2E scenario 3

Product search
→ Identify reference product
→ Alternatives
→ Filters
→ Price observations
→ Compare candidate
→ Add to shelf.

Use automated browser testing.

Test real database interactions, not only mocked frontend responses.

# 24. IMPLEMENTATION ROADMAP

You must deliver the entire specified product, but implementation must be dependency-aware.

Do not confuse independent pipeline architecture with simultaneous development of every feature.

## Phase 0 — Audit and feasibility

- Repository audit.
- Full specification analysis.
- Architecture decisions.
- Requirements matrix.
- ML feasibility.
- OCR feasibility.
- Product-data source feasibility.
- Price-data feasibility.

## Phase 1 — Shared foundation

- Frontend.
- Backend.
- Database.
- Authentication.
- API contracts.
- Logging.
- Error handling.
- Design system.
- CI configuration.

## Phase 2 — Product and ingredient intelligence

- Product schema.
- Formulation versions.
- Ingredient schema.
- Aliases.
- Normalization.
- Evidence.
- Provenance.
- Knowledge versioning.
- Search.
- Product pages.

## Phase 3 — Compatibility engine

Prioritize this as the first complete intelligence workflow.

Implement:
- Formulation resolution.
- Ingredient comparison.
- Interaction rules.
- Evidence.
- Confidence.
- API.
- UI.
- Tests.

## Phase 4 — Product identification and OCR

Implement:
- Scanner.
- OCR.
- Manual correction.
- Normalization.
- Candidate matching.
- User confirmation.

## Phase 5 — Skin analysis

Implement:
- Secure upload.
- Quality assessment.
- Model adapter.
- Inference worker.
- Observations.
- Confidence.
- Concern mapping.

## Phase 6 — Recommendation engine

Implement:
- Ingredient category resolution.
- Evidence filtering.
- Product retrieval.
- Personalization.
- Compatibility filtering.
- Ranking.
- Explanation.

## Phase 7 — Alternatives engine

Implement:
- Product identification.
- Candidate retrieval.
- Filtering.
- Similarity.
- Price observations.
- Ranking.
- Explanations.
- Comparison integration.

## Phase 8 — Retention and supporting features

Implement:
- My Shelf.
- Routine.
- Routine analysis.
- History.
- Saved products.
- Sharing.

## Phase 9 — Admin and governance

Implement:
- Data review.
- Knowledge review.
- Publishing.
- Versioning.
- Audit logs.
- Data-quality dashboard.

## Phase 10 — Growth and hardening

Implement:
- SEO.
- Analytics.
- Accessibility.
- Performance.
- Security.
- CI/CD.
- Deployment.

Parallelize independent workstreams when useful.

However, establish shared schemas and contracts first.

Integrate continuously.

Do not postpone integration until the final phase.

# 25. ENGINEERING EXECUTION RULES

1. Inspect before modifying.
2. Preserve existing working implementations.
3. Implement actual functionality.
4. Use shared canonical data.
5. Keep business logic in domain services.
6. Use typed contracts.
7. Make expensive workflows asynchronous.
8. Validate all inputs.
9. Handle missing data explicitly.
10. Maintain provenance.
11. Version important knowledge.
12. Test all critical logic.
13. Test integration between pipelines.
14. Document architectural decisions.
15. Never fabricate external responses.
16. Never hide failed tests.
17. Never claim an ML model works without inference verification.
18. Never claim a deployment succeeded without verification.
19. Never leave primary buttons decorative.
20. Never present demonstration records as verified data.
21. Never silently omit specification requirements.
22. Never compromise scientific integrity for visual presentation.

# 26. FRONTEND-BACKEND INTEGRATION CONTRACT

Every primary feature must use actual API integration.

For each frontend workflow verify:

- Correct request.
- Correct authentication.
- Correct request validation.
- Correct API response.
- Correct state handling.
- Loading state.
- Error state.
- Retry behavior.
- Data persistence.
- Ownership enforcement.

Use shared TypeScript interfaces generated from or synchronized with backend schemas.

Avoid duplicating incompatible types.

Ensure that frontend and backend agree on:
- IDs.
- Enumerations.
- Timestamps.
- Confidence values.
- Job statuses.
- Error codes.
- Pagination.
- Result structures.

# 27. RELEASE GATES

A phase is not complete merely because code has been written.

Each phase must pass:

1. Implementation verification.
2. Type checking.
3. Unit tests.
4. Relevant integration tests.
5. API verification.
6. Error-state verification.
7. Security review.
8. Documentation update.

Critical failures block progression.

For unavailable external integrations, use explicit integration gates and document required credentials, weights, datasets or approvals.

Do not fake a passing test.

# 28. DEPLOYMENT

Prepare:

- Development.
- Staging.
- Production.

Implement:
- Environment configuration.
- Docker.
- Database migrations.
- Worker startup.
- Health checks.
- CI/CD.
- Logging.
- Monitoring.
- Backups.
- Recovery instructions.

CI/CD:

Git push
→ Lint
→ Type check
→ Unit tests
→ Integration tests
→ Build
→ Security checks
→ Staging
→ Smoke tests
→ Production.

Keep secrets out of source control.

Never use production secrets for local development.

Document manual provider configuration.

# 29. REQUIRED DOCUMENTATION

Create:

docs/
├── implementation-audit.md
├── requirements-traceability.md
├── srs.md
├── architecture.md
├── architecture-decisions/
├── data-dictionary.md
├── dfd.md
├── er.md
├── api.md
├── security.md
├── privacy.md
├── model-evaluation.md
├── data-governance.md
├── test-plan.md
├── test-cases.md
├── risk-register.md
├── deployment.md
└── uml/
    ├── use-case.md
    ├── class.md
    ├── sequence-comparison.md
    ├── sequence-skin-analysis.md
    ├── sequence-alternatives.md
    ├── activity.md
    ├── state.md
    └── component.md

Also provide:
- README.md.
- .env.example.
- Database migrations.
- Seed scripts.
- Docker configuration.
- API documentation.
- Worker documentation.

# 30. FINAL ACCEPTANCE CRITERIA

The final product must demonstrate all five quality dimensions defined in the source specification.

## Product

Users can complete actual skincare decisions.

## Scientific and data integrity

The system distinguishes:
- Observation.
- Confidence.
- Evidence.
- Data quality.

Unknown information remains unknown.

## Engineering

The system has:
- Modular architecture.
- Shared data.
- Versioned knowledge.
- Tests.
- Security.
- Observability.

## UX

The system is:
- Fast.
- Simple.
- Visual.
- Mobile-friendly.
- Accessible.
- Transparent.

## Growth

The system has:
- SEO.
- Sharing.
- Guest utility.
- Personalization.
- Retention.
- Analytics.

Use the original specification's final acceptance criteria as the definitive checklist.

# 31. FINAL DEMONSTRATION

Demonstrate one connected user journey:

1. Open SkinIQ.
2. Analyze skin.
3. Upload an image.
4. Validate image quality.
5. Display supported observations.
6. Show ingredient categories.
7. Show product recommendations.
8. Open a recommended product.
9. Inspect ingredients and provenance.
10. Find alternatives.
11. Compare original and alternative.
12. Show compatibility findings.
13. Inspect evidence.
14. Add products to My Shelf.
15. Create morning and evening routines.
16. Analyze the routines.
17. Show history and saved results.
18. Demonstrate admin/data governance.
19. Show architecture and UML.
20. Show actual test results.

The final experience must feel like one coherent application.

# 32. FINAL DELIVERY REPORT

When implementation is complete, provide:

### A. Product delivery

- Implemented features.
- Completed user workflows.
- Working routes.
- Frontend functionality.

### B. Backend delivery

- API endpoints.
- Domain services.
- Database schema.
- Migrations.
- Background workers.

### C. Three-pipeline status

For each pipeline:
- Input.
- Processing.
- Output.
- Actual integration status.
- Test results.
- Known limitations.

### D. AI/ML status

Clearly identify:
- Real model integrations.
- Verified model inference.
- Development adapters.
- Missing model weights.
- Missing datasets.
- Evaluation status.
- External dependencies.

### E. Data status

Identify:
- Verified records.
- Development seed records.
- External sources.
- Licensing limitations.
- Unverified information.
- Missing product coverage.

### F. Testing

Report actual:
- Unit test results.
- Integration test results.
- E2E test results.
- Build results.
- Security checks.
- Accessibility checks.

Never report tests as passing if they were not executed.

### G. Running the application

Provide:
- Installation instructions.
- Environment setup.
- Database setup.
- Migration commands.
- Seed commands.
- Frontend startup.
- Backend startup.
- Worker startup.

### H. Deployment

Provide:
- Deployment architecture.
- Hosting configuration.
- Required credentials.
- Environment variables.
- Deployment steps.
- Known blockers.

### I. Remaining limitations

List everything that is not genuinely complete.

---

# 33. FINAL EXECUTION DIRECTIVE

Start by reading the complete attached specification and inspecting the existing repository.

Do not ask the user to manually provide information that already exists in the repository or specification.

If something genuinely requires external credentials, a dataset, a model checkpoint, a licensed source or human review, identify it precisely.

Then implement the application incrementally.

Keep the application runnable throughout development.

Use the terminal to create and modify files, run migrations, start services and execute tests.

Use browser automation to inspect and test the actual application when available.

If multiple coding agents are available, delegate the three primary pipeline workstreams after establishing common interfaces and database contracts.

Do not delegate the shared architecture without assigning one lead agent responsibility for integration and consistency.

Maintain a requirements checklist and update it as implementation progresses.

Do not stop because the response context is running low. Preserve your implementation state, update the progress documentation and continue from the last verified checkpoint.

Do not claim that a feature is complete merely because its frontend exists.

Do not claim that the entire product is complete when external model, dataset or data-source requirements remain unmet.

**THE FINAL OBJECTIVE**

Deliver a complete, integrated, maintainable, secure and genuinely functional SkinIQ platform.

Three independent intelligence pipelines.

One shared product and ingredient knowledge system.

One unified user experience.

Real data.

Real processing.

Deterministic domain logic.

Evidence-backed explanations.

Comprehensive testing.

Honest integration status.

Deployable engineering.

**Build SkinIQ as a real software product, not an AI-themed website.**