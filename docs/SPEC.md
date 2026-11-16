# SkinSync: Complete Product and Build Specification

**Audience:** an LLM or developer reading this from scratch, with no other context, to design and build the SkinSync website.
**Origin:** UCS503 Software Engineering project, Group 3C25, Thapar Institute of Engineering & Technology, Patiala (Saksham Jain, Ishika Walia, Abharaj Singh). Source material: a project deck and a mid-semester report (bid, use cases, SRS in IEEE format, user stories).
**Tagline:** "Check before you layer."
**Core promise:** "Understand your skin. Understand your products. Make better skincare decisions."

**How to read this document**
- Sections marked **[SOURCE]** come directly from the project documents.
- Sections marked **[PROPOSED]** are additions or fleshed-out details that the documents imply but do not specify. Treat them as recommended defaults the team can change.
- Where the two conflict, [SOURCE] wins.
- Earlier diagrams in the source material were found to be incorrect and were ignored. The structure below is derived from the text only. The domain model in section 8 is indicative and should be refined during schema design.
- An earlier name "SkinIQ" may appear in old artifacts. The product name is **SkinSync**.

---

## 1. What SkinSync Is

SkinSync is a responsive, web-based **evidence-aware skincare decision-support platform**. It is not a shopping site, a dermatology tool, or a chatbot. It helps a user make three recurring decisions that are currently answered by fragmented, unstructured sources (brand claims, forums, influencer routines, ingredient blogs, marketplace listings):

1. **What does my skin appear to need?** Visible characteristics are judged informally and described with inconsistent vocabulary.
2. **Can I use these products together?** Ingredient lists are long, inconsistently named, and rarely compared against explicit interaction knowledge.
3. **What are my alternatives to this product?** Substitutes are found by browsing rather than by comparing formulation, category, price and routine fit.

SkinSync unifies these into one decision engine.

### 1.1 The central architectural idea [SOURCE]
- **AI/ML assists with perception only:** image analysis of skin photos, OCR of product/ingredient labels, product recognition, and optionally phrasing.
- **Conclusions rest on structured data, explicit deterministic rules, confidence, and evidence records.** An LLM or model never decides whether two products are compatible. A rule engine over normalized ingredient sets does, and every finding cites evidence and the knowledge version that produced it.
- **Risk ordering:** the deterministic core (search, ingredients, compatibility) ships before OCR and the skin model, so uncertainty in AI-assisted features can never block the product. If OCR or the model is down, search and comparison must still work.

### 1.2 Design principles (apply to every screen and API) [SOURCE + PROPOSED]
1. **Explain everything.** Every result states what data was used, how confident it is, where evidence or data is incomplete, and why it was produced (NFR-10).
2. **Unknown stays unknown.** Unresolved ingredients and incomplete formulations are shown as unresolved or incomplete, never silently treated as inert or safe.
3. **Confidence is not evidence strength.** They are two separate indicators and must be displayed separately.
4. **No diagnosis, no universal safety claims, no guaranteed outcomes.**
5. **Deterministic and reproducible.** Same inputs plus same knowledge version gives the same result. Results are stored with the versions used and can be retired when a rule changes.
6. **Private by default.** Skin images and skin analyses are never public unless explicitly and knowingly shared.
7. **Graceful degradation.** Optional services failing must not take down core flows.
8. **Don't invent data.** No invented prices, ingredients or evidence. Show "unavailable" instead.
9. **Guest-first.** Core tools work without an account. Persistence requires registration.
10. **Neutrality.** Commercial relationships, if ever introduced, must not influence compatibility results or evidence strength.

---

## 2. Scope [SOURCE]

### 2.1 In scope (initial release)
Responsive web app; product and ingredient data; ingredient normalization; two-product compatibility; OCR/barcode scanning; skin-image analysis pipeline; concern mapping and recommendations; alternatives; routines; My Shelf; search; saved results and history; sharing; admin data/knowledge governance; analytics; testing; deployment planning.

### 2.2 Explicitly out of scope
Medical or dermatological diagnosis; prescription treatment; guaranteed outcomes; universal "safe/unsafe" claims; fully autonomous medical recommendations; automated purchasing without user confirmation.

### 2.3 Medical boundary wording (mandatory in UI)
- Skin analysis shows **supported visible cosmetic observations only**. It never names or diagnoses acne, rosacea, melasma, eczema or any medical condition, and offers no treatment or prescription.
- Every analysis states that results are **estimates affected by lighting, camera quality, makeup, filters and angle**.
- Compatibility "clear" wording must be: **"No notable interaction identified in the current knowledge base for the formulations supplied."** Never "safe" or "compatible for everyone."
- Suggest consulting a professional for persistent or concerning skin issues (generic, non-diagnostic).

---

## 3. Users, Actors and Stakeholders [SOURCE]

| Actor | Type | Description |
|---|---|---|
| Guest User | Primary | Searches products, views details, compares two products, analyses skin, finds alternatives. **Cannot persist anything.** |
| Registered User | Primary (specialises Guest) | Everything a guest can do plus My Shelf, routines, routine checking, saved results, sharing, history, profile. |
| Admin | Secondary | Reviews data-quality flags, approves corrections, publishes reviewed compatibility/recommendation knowledge as a version. |
| Viewer | Secondary | Anyone opening a public share link. Read-only. |
| OCR Service | External system | Extracts text and positions from product/ingredient-label images. Low-confidence output requires review. |
| Skin Analysis Model | External system | Returns structured observations, confidence, severity and model version for a validated image. |
| Product Data Source | External system | Supplies product, formulation, ingredient and provenance data. |
| Price Data Source | External system | Supplies observed prices with seller, currency, source, availability and timestamp. |

**Stakeholders (influence requirements, do not act on the system):** beginner user (simple explanations, comparison, routine help), ingredient-conscious user (INCI, evidence), budget-conscious user (cheaper alternatives, value), routine builder (shelf, ordering, compatibility), skincare enthusiast (detailed formulation/evidence), admin/data reviewer, faculty evaluator.

---

## 4. Architecture and Tech Stack [SOURCE]

**Style:** modular monolith (avoid premature microservices). Each domain service maps to a capability in the use-case model.

| Layer | Choice |
|---|---|
| Presentation | Next.js, React, TypeScript; responsive across desktop, tablet, mobile |
| API | Python FastAPI with Pydantic validation; versioned `/api/v1`; request IDs on every response; predictable error codes; auth and rate limiting |
| Domain services | Product, Ingredient, Compatibility, Skin Analysis, Recommendation, Alternative, Routine, Shelf, Search |
| Data | PostgreSQL (primary store), Redis (cache, coordination, rate limits), object storage (private skin and label images) |
| Async workers | OCR, skin analysis, ingestion (price refresh, product data refresh) |
| External adapters | OCR provider, skin analysis model, product data source, price data source. Each is reached via an adapter, and **its output is validated before domain logic uses it** |

**Data stores at rest (conceptual):** Product Store; Ingredient/Evidence (Knowledge) Store; Compatibility Rules; User/Shelf/Routine Store; Upload Store; Recommendation Store.

**Adapter contracts**
- OCR adapter: send label image, receive text plus positions plus confidence. Low confidence flags the result for review.
- ML adapter: accept an image, return observations, confidence, severity and **model version**.
- Product data: product, formulation, ingredients, provenance.
- Price data: amount, currency, seller, source, availability, observed timestamp.

---

## 5. Product Pipeline (end to end) [SOURCE]

```
Actor and intent   ->  Data preparation                       ->  Reasoning and response
User (guest/reg.)      Input validation                           Domain logic:
Workflow selection:    Data acquisition                             Skin concern mapping
 Analyze Skin          Ingredient and product normalization         Compatibility engine
 Compare Products      Knowledge + evidence retrieval               Recommendation engine
 Find Alternatives                                                  Similarity engine
 Explore Ingredients                                              Personalization
 Build Routine                                                    Result + confidence + completeness
 My Shelf                                                         Explanation -> user action
```

---

## 6. Complete User Journey

The journey is guest-first, with account creation offered only at moments of demonstrated value.

### Stage 1: Arrive and orient (Guest)
- Entry points: search engine (indexable product and ingredient pages), shared result link, direct visit.
- Homepage shows the promise "Check before you layer" and three primary entry tiles: **Analyze my skin**, **Compare two products**, **Find alternatives**, plus a global search bar and a scan button.
- A short, visible notice explains what SkinSync does and does not do (cosmetic observations, not diagnosis).
- No signup wall. Nothing is required to start.

### Stage 2: Find and identify a product
- User searches by product, brand, category or ingredient, or scans a barcode or label photo.
- Search normalizes the query, searches the index, ranks, and displays candidates.
- **Ambiguity:** if the match is unclear, the user picks from candidates (confirmation step). Low-confidence scan results are never presented as certain.
- **Failure paths:** no results (offer broader search, scan, or manual add request), camera permission denied (offer upload or manual search), OCR low confidence (show extracted text for user correction).

### Stage 3: Inspect product and ingredients
- Product page shows: name, brand, category, **current formulation version** (label, observed date), normalized ingredient list with position, stated role and key-active flag, function classes, price observations with seller and timestamp, data completeness indicator, provenance.
- Tapping an ingredient opens its detail: canonical name, INCI name, function class, considerations, evidence records, products containing it, and a data-status note if sparse.
- Registered users see "Add to shelf" and "Save".

### Stage 4: Core decisions (Guest or Registered)

**4a. Compare two products** (UC02)
1. Select Product A, then Product B (search or scan).
2. System validates inputs and resolves the current formulation version of each.
3. Ingredients are normalized to canonical names.
4. Interaction rules are evaluated.
5. Supporting evidence records are retrieved.
6. Result screen: overall status; list of findings (category, plain-language explanation, per-finding confidence, evidence strength); data completeness; unresolved ingredients; knowledge version used; timestamp.
7. Exceptions: product not found (offer search/scan); formulation incomplete (show partial completeness and limit findings); insufficient evidence (return "insufficient evidence", not a verdict).
8. Actions: save (registered), share (appropriate), find alternatives to either product, add to routine.

**4b. Analyze my skin** (UC01)
1. Enter skin type (and optionally concerns/sensitivities).
2. Consent screen for image handling (what is stored, for how long, how to delete).
3. Upload or capture a skin image, with guidance (natural light, no filters, no makeup, face camera on).
4. Validation: file type, size, decoding, image quality. Invalid or poor quality shows a clear error and retake guidance.
5. Analysis runs asynchronously with a progress state.
6. Result: supported cosmetic observations, each with confidence and severity; concerns mapped to recommendation categories; ingredient and product recommendations with evidence; persistent limitations and no-diagnosis notice; low-confidence observations clearly marked.
7. Exceptions: poor image, model failure (graceful message, retry), low confidence.
8. Actions: save (registered, private), explore recommended ingredients/products, compare products, delete image now.

**4c. Find alternatives** (UC03)
1. Identify a reference product (search/scan).
2. Choose mode: cheaper, similar, premium, ingredient-focused, routine-compatible (the last needs a shelf or routine).
3. System extracts product features, retrieves candidates, removes duplicates, applies hard filters, then ranks by similarity, price, and preference.
4. Result: ranked list with **visible ranking reasons**, price with timestamp and seller, price freshness flag, similarity dimensions, data completeness.
5. Exceptions: no match, stale or unavailable price (shown as unavailable, never invented), low identification confidence.
6. Actions: compare with the reference, save, add to shelf or routine, share.

### Stage 5: Value moment and conversion
- After a useful result, an inline prompt appears: "Save this result" or "Add to My Shelf". It appears only after value is delivered.
- Guests who sign up keep the current result (it is attached to the new account).
- Sign-up: email and password (or social sign-in, [PROPOSED]), with a brief profile step that can be skipped.

### Stage 6: Personalize (Registered)
- **Profile:** skin type, sensitivities, preferences (budget, fragrance-free, etc.), consent settings.
- **My Shelf:** add, remove, search or scan owned products; mark as owned or wishlist [PROPOSED]; duplicates and unavailable products handled with clear messages.
- **Build Routine:** create morning or evening routines from shelf products; order the steps; set frequency and notes; duplicate steps flagged.
- **Check Routine:** pairwise compatibility across routine products, duplicated actives surfaced, missing data surfaced, evidence available, never treating missing data as safe.
- **Saved results and History:** all saved comparisons, analyses and alternatives, reopenable with the formulation and knowledge versions they used.
- Rankings (alternatives, recommendations) now factor in profile, shelf and routine, but personalization changes ranking, never the compatibility conclusion.

### Stage 7: Share and retain
- Share a comparison, product or alternatives result by link (revocable token). **Skin analysis results are private by default** and never exposed through ordinary sharing.
- Returning users see "outdated" flags on saved results when a formulation changes, a price changes, or the knowledge version is superseded, with a one-click refresh.
- Settings: manage consent, delete individual analyses and images, delete account and all associated analysis data (FR-20).

### Stage 8: Admin loop (behind the scenes)
- Admin sees a queue of data-quality flags (reason and source shown), low-confidence OCR extractions, unresolved ingredients, conflicting evidence.
- Admin validates sources, edits or corrects records, approves.
- Admin assembles reviewed rules and evidence into a **knowledge version**, assigns a version label, and publishes it to the engine. Unsupported claims and missing evidence stay unpublished until resolved. Publication status is recorded.

### Journey summary map
```
Arrive -> Search/Scan -> Identify (confirm if ambiguous) -> Product/Ingredient page
 -> [Compare | Analyze Skin | Alternatives] -> Result with explanation
 -> Save/Share prompt -> Sign up -> Profile -> Shelf -> Routine -> Check Routine
 -> History / outdated alerts -> Share / Delete data
(Admin: Flags -> Review -> Edit -> Version -> Publish -> Engine)
```

---

## 7. Use-Case Catalogue [SOURCE]

| ID | Name | Actor | Goal | Main flow | Exceptions |
|---|---|---|---|---|---|
| UC01 | Analyze Skin | Guest/Registered | Identify supported visible cosmetic observations | Validate, analyze, observations, map concerns, recommend | Poor-quality image; model failure; low confidence |
| UC02 | Compare Products | Guest/Registered | Relevant compatibility concerns for two formulations | Resolve versions, normalize, rules, evidence, explain | Ambiguous product; incomplete ingredients; no evidence |
| UC03 | Find Alternatives | Guest/Registered | Cheaper, similar, premium or routine-compatible options | Features, candidates, filters, similarity ranking | No match; stale price; low identification confidence |
| UC04 | Search Product | Guest/Registered | Locate product by name, brand, category, ingredient | Normalize query, search index, rank, display | No results; ambiguous query |
| UC05 | Scan Product | Guest/Registered | Identify from barcode or label image | Capture, barcode/OCR, candidates, confirm | Permission denied; low OCR confidence; product unavailable |
| UC06 | Inspect Ingredient | Guest/Registered | Understand an ingredient via canonical INCI form | Resolve, functions, considerations, evidence, display | Unknown ingredient; insufficient data |
| UC07 | Build Routine | Registered | Morning/evening routine from saved products | Select, order steps, save, optionally analyze | Missing product data; duplicate steps |
| UC08 | Manage Shelf | Registered | Save and organize products | Add/remove/search/scan, persist | Duplicate or unavailable product |
| UC09 | Save Result | Registered | Persist a useful comparison or analysis | Validate, associate with user, persist | Unauthorized; persistence failure |
| UC10 | Share Result | Registered / Viewer | Create or view a shareable result | Share token, privacy policy, render public result | Sensitive analysis; revoked token |
| UC11 | Review Data | Admin | Review data-quality flags, approve corrections | Inspect flags, validate sources, edit, publish | Missing source; unresolved evidence |
| UC12 | Publish Knowledge | Admin | Publish reviewed knowledge as a version | Review, assign version, publish to engine | Review incomplete; conflicting evidence |

Also referenced: **Check Routine** (extends product details/routine work; evaluates a saved routine), **Validate Inputs** (included by Compare Products and Analyze Skin), **View History**, **Manage Knowledge Data** (admin umbrella). Register these formally if not already covered by UC07/UC09.

### Detailed template: UC02 Compare Products
- **Primary actor:** Guest or Registered. **Supporting actor:** OCR Service when a product is supplied by scan.
- **Preconditions:** two products identified; a formulation version resolvable for each.
- **Normal course:** (1) select A, (2) select B, (3) retrieve current formulation version of each, (4) normalize both ingredient sets, (5) evaluate applicable interaction rules, (6) retrieve supporting evidence, (7) display findings, confidence and data completeness.
- **Alternate A1:** ambiguous input, so present candidates; user confirms; resume at step 3.
- **Exceptions:** E1 product not found (report, offer search/scan). E2 formulation incomplete (report partial completeness, limit findings). E3 insufficient evidence (return "insufficient evidence" instead of a verdict).
- **Postcondition:** a Comparison and its findings are generated and may be stored by a registered user.

### Activity flow: Skin Analysis
Upload image, validate quality. If invalid: show upload error and end. If valid: analyze image, identify visible observations, **fork** into (map concerns) and (retrieve evidence), **join**, generate recommendations, end.

### Swimlane: Product Comparison
User (select two products, view result/save) / SkinSync application (submit comparison, validate and normalize ingredients, evaluate compatibility, generate explanation) / Knowledge and data services (retrieve rules and evidence). Normalized ingredient sets flow outward; rules, evidence and knowledge version flow back.

---

## 8. Domain Model (indicative) [SOURCE entities, PROPOSED attributes]

Entities and key relationships:

- **User**: id, email, role (guest not persisted / registered / admin). Has one optional **Profile** (skinType, sensitivities, preferences, consents). Has many ShelfItems, Routines, SkinAnalyses, Comparisons, AlternativeSearches.
- **Product**: name, brand, category. Has many **ProductVersion** (composition).
- **ProductVersion**: versionLabel, observedAt, completeness, market/region. Has many **ProductIngredient** (association class: position, statedRole, isKeyActive) linking to **Ingredient**.
- **Ingredient**: inciName, canonicalName, functionClass, aliases (for normalization), considerations.
- **PriceObservation**: amount, currency, seller, source, availability, observedAt. Belongs to Product (or version).
- **InteractionRule**: ruleCode, severity, condition (over ingredient/function-class sets), explanation template, `appliesTo(a, b)`. Belongs to a **KnowledgeVersion**.
- **EvidenceRecord**: sourceType, citation, strength (High / Moderate / Limited / Insufficient / Unknown). Linked to rules and findings.
- **KnowledgeVersion**: versionId, publishedAt, status (draft / in review / published / retired).
- **Comparison**: createdAt, status, completeness; binds to the two ProductVersions used and the KnowledgeVersion. Has many **ComparisonFinding** (category, explanation, confidence, `isConclusive()`), each linked to EvidenceRecords and the rule.
- **SkinAnalysis**: imageRef, status, createdAt, modelVersion. Has many **SkinObservation** (characteristic, confidence, severity) and many **Recommendation** (targetConcern, rationale, rank).
- **AlternativeSearch**: mode, constraints, createdAt. Has many **ProductAlternative** (category, similarity, rank, reasons).
- **ShelfItem**: addedAt, note, isOwned. **Routine**: name, timeOfDay, isActive. **RoutineItem**: stepOrder, frequency, note.
- **OCRResult**: rawText, confidence, status (pending review / confirmed / rejected).
- **ShareToken** [PROPOSED]: token, targetType, targetId, createdAt, revokedAt.
- **DataQualityFlag** [PROPOSED]: target, reason, source, status, resolvedBy.
- **AuditLog** [PROPOSED]: actor, action, target, timestamp.

**Rationale (keep when implementing)**
- *Versioning (SRS constraint 4.2.4):* a product is not its ingredient list. Formulations change, so comparisons bind to the ProductVersion actually used.
- *Evidence as first-class (NFR-10):* each finding records its evidence and the knowledge version, so results are reproducible and can be retired when a rule changes.
- *High cohesion, low coupling; separation of concerns:* knowledge can be revised without touching catalogue or user data; cross-object behaviour lives in services.
- *Traceability:* comparisons and analyses are stored records, not transient results.

---

## 9. Features (comprehensive)

### A. Discovery and product intelligence
1. Search by product, brand, category, ingredient; typo tolerance, synonyms, ranking, filters, pagination. Target under 1 to 2 s.
2. Autocomplete suggestions [PROPOSED].
3. Barcode scanning via camera or image upload.
4. Label/ingredient OCR with a confirm-and-correct step.
5. Product pages: versioned formulation, ingredients with position/role/key-active, function classes, price observations, provenance, completeness, last-updated.
6. Ingredient normalization to canonical INCI with confidence and source; alias table; unresolved ingredients flagged.
7. Ingredient explorer (UC06): functions, considerations, evidence, related products.
8. Category and brand browse pages (SEO-indexable).
9. "Report incorrect data" action feeding the admin flag queue [PROPOSED].

### B. Compatibility engine
1. Two-product comparison with deterministic rule evaluation over normalized ingredient sets and function classes.
2. Finding types: interaction, redundancy (duplicate actives), uncertainty/insufficient data. Each has a severity level.
3. Evidence records per finding with evidence strength; confidence displayed separately.
4. Knowledge version and formulation versions stamped on every result.
5. Overall status uses cautious language, never universal safety.
6. Insufficient-evidence path returns "insufficient evidence", not a verdict.
7. Cached results (target under 2 s) invalidated when formulation or knowledge version changes.
8. Routine-level pairwise analysis (all pairs in a routine).

### C. Skin analysis
1. Skin-type input; optional concern/sensitivity input.
2. Consent step and clear data-handling statement.
3. Image upload and capture with guidance overlay and tips.
4. Validation of file type, size, decoding, quality (blur, lighting, face presence as applicable); actionable rejection messages.
5. Async analysis via worker and model adapter; progress and retry states.
6. Observations list: characteristic, confidence, severity; low-confidence flagged.
7. Concern mapping to recommendation categories (structured mapping table, not free-form AI).
8. Recommendations: ingredient categories and products with evidence and user fit (FR-11).
9. Persistent limitations panel and medical boundary notice.
10. Private storage, minimal retention, delete-now control.

### D. Alternatives
1. Modes: cheaper, similar, premium, ingredient-focused, routine-compatible (where data supports it).
2. Feature extraction from the reference product (category, key actives, function classes, price band, constraints).
3. Candidate retrieval, de-duplication, hard filters (category, sensitivities, region, availability), then ranking by similarity, price and preference.
4. Visible ranking reasons and similarity dimensions per result.
5. Price observations with seller, currency, timestamp; stale and unavailable states; no invented prices.
6. Low-identification-confidence warning.

### E. Personalization (registered)
1. Profile: skin type, sensitivities, preferences.
2. My Shelf with search, scan, add, remove, owned/wishlist, notes.
3. Routine builder: AM/PM, drag-to-order steps, frequency, notes.
4. Routine check: pairwise compatibility, duplicated actives, missing data, evidence drill-down.
5. Saved results and history with filters and search.
6. Outdated indicators and refresh on formulation, price or knowledge changes.

### F. Sharing and privacy
1. Share links with revocable tokens for comparisons, products, alternatives, routines.
2. Skin-analysis results private by default; no accidental exposure via any share path.
3. Public share view: read-only, no personal data, indicates knowledge version and date.
4. Consent management, retention controls, per-item delete, full account deletion that includes associated analysis data and images.
5. Cookie/analytics consent [PROPOSED].

### G. Explainability layer (cross-cutting, NFR-10)
1. Every result screen has a standard panel: **What was used** (product versions, knowledge version, model version), **How confident** (confidence), **Evidence strength**, **What's missing** (completeness, unresolved items).
2. Expandable evidence with citations and source types.
3. Plain-language summary first, details on expand (serves beginners and enthusiasts).

### H. Admin and governance
1. Data-quality flag queue showing reason and source.
2. OCR and ingredient-normalization review (low-confidence items).
3. Source validation; edit or approve corrections.
4. Rule and evidence authoring and review.
5. Knowledge versioning: assign version, publish to engine, record publication status, roll back or retire rules.
6. Conflicting-evidence and incomplete-review blocking (cannot publish).
7. Audit trail of admin actions.
8. Admin-only access with role-based authorization.

### I. Platform and engineering
1. Responsive UI (desktop, tablet, mobile); mobile camera-friendly flows.
2. Accessibility (NFR-07): keyboard navigation, semantic markup, visible focus, labels, screen-reader support, adequate contrast. Target WCAG 2.1 AA [PROPOSED].
3. Loading, success, empty, partial and error states on every workflow.
4. Graceful degradation, retries, fallbacks (NFR-03).
5. Security: authentication, authorization, upload validation, private storage, secrets management, rate limiting (NFR-02).
6. Performance: caching with Redis, DB indexes, stateless API, workers (NFR-01, NFR-05).
7. Versioned API with request IDs and predictable error codes.
8. SEO for product and ingredient pages; structured data [PROPOSED].
9. Analytics (privacy-respecting) and error monitoring.
10. CI/CD, environments (dev, staging, prod), automated tests.

### J. Suggested additions [PROPOSED, optional]
- Onboarding quiz for beginners (skin type, goals, sensitivities).
- Ingredient glossary with "explain like I'm new" mode.
- Patch-test reminders and general layering guidance (non-medical).
- Notifications for formulation changes or price drops on shelf items.
- Opt-in private skin progress timeline.
- Feedback buttons on findings feeding the admin queue.
- Multi-language support and regional currency (e.g. INR).
- Export routine or result as PDF.
- Dark mode.

---

## 10. Pages and Navigation [PROPOSED]

**Primary nav:** Analyze Skin, Compare, Alternatives, Products, Ingredients, and (when signed in) My Shelf, Routines, History. Search bar and scan button are global. Account menu holds Profile, Settings, Privacy, Sign out. Footer links to About, How it works, Safety and medical boundary, Privacy, Terms, Contact.

| Route | Purpose | Access |
|---|---|---|
| `/` | Landing, three entry tiles, search | All |
| `/analyze` | Skin analysis flow (type, consent, upload, result) | All |
| `/compare` | Two-product selector and result | All |
| `/alternatives` | Reference product, mode, ranked results | All |
| `/products` and `/products/[slug]` | Browse and product detail | All |
| `/ingredients` and `/ingredients/[slug]` | Ingredient explorer and detail | All |
| `/scan` | Barcode/label capture | All |
| `/shelf` | My Shelf | Registered |
| `/routines` and `/routines/[id]` | Routine list, builder, check | Registered |
| `/history` and `/history/[id]` | Saved results | Registered |
| `/profile`, `/settings/privacy` | Profile, consent, deletion | Registered |
| `/share/[token]` | Public read-only result | Viewer |
| `/auth/*` | Sign in, sign up, reset | All |
| `/how-it-works`, `/safety` | Methodology, medical boundary | All |
| `/admin/*` | Flags, OCR review, rules, evidence, knowledge versions, audit | Admin |

---

## 11. UI/UX Guidance [PROPOSED]

- **Tone:** calm, clear, non-alarmist, non-clinical. Plain language first, technical detail on demand.
- **Visual direction (matches the project deck):** warm cream background (about `#F5EBD9`), deep charcoal text, terracotta/burnt-orange accent (about `#8B4A1B` and `#C8703A`), soft sage-green panels for evidence/knowledge, soft peach panels for highlighted content; bold serif display headings with a clean sans-serif body; rounded pill and card components. Designers may refine.
- **Result-screen template (reuse everywhere):** headline answer, then findings list, then the explainability panel (used / confidence / evidence / missing), then actions (save, share, next step).
- **Status language:** use graded, neutral labels for findings, for example "Notable interaction", "Possible redundancy", "Insufficient evidence", "No notable interaction identified in current knowledge". Pair with icons and text, never color alone.
- **Confidence vs evidence:** show as two distinct, labelled indicators.
- **Skin photo UX:** live guidance (light, angle, no filters), preview with retake, privacy reminder, visible "delete image" control.
- **Empty/partial states:** always state what is missing and offer a recovery action (NFR-06).
- **Mobile first** for scanning and photo capture.

---

## 12. Algorithms and Logic (specification level) [SOURCE intent, PROPOSED detail]

### 12.1 Ingredient normalization
Input: raw ingredient strings (from data source or OCR). Steps: clean text (case, punctuation, separators), split list, match against alias table to canonical/INCI name (exact, then fuzzy with threshold), attach function class and confidence and source, keep position and stated role, and flag unresolved items. Unresolved items stay in the result as "unknown" and reduce completeness.

### 12.2 Compatibility evaluation
For each rule in the active published KnowledgeVersion: check `appliesTo(A, B)` against normalized ingredient or function-class sets (including concentration or position conditions where data allows). Collect findings with severity. Attach evidence records and per-finding confidence (reduced by unresolved ingredients and low normalization confidence). If no rule has sufficient evidence for the pair of relevant ingredients, emit an "insufficient evidence" finding. Output is deterministic for a given (ProductVersions, KnowledgeVersion). Determine overall status conservatively.

### 12.3 Skin analysis and concern mapping
Model adapter returns observations (characteristic, confidence, severity, model version). Observations below a confidence threshold are shown as low confidence or suppressed. A structured mapping table maps supported observations to concern categories, then to recommendation categories (ingredient classes), then to products via structured knowledge, evidence and user fit.

### 12.4 Alternatives ranking
Candidates are scored on a weighted combination of feature/ingredient similarity (function classes, key actives), category match, price delta (for cheaper/premium), and preference fit. Hard filters (sensitivities, category, availability, region) are applied before ranking. Each result keeps its per-dimension scores to display reasons. Routine-compatible mode additionally runs compatibility against the user's routine and drops or flags conflicts.

### 12.5 Personalization
Skin type, sensitivities, preferences, shelf and routine adjust **ranking and filtering only**. They never alter a compatibility conclusion.

---

## 13. API Design Sketch [PROPOSED]

Versioned under `/api/v1`, JSON, request ID header on every response, consistent error envelope `{ code, message, details, request_id }`, rate limiting, cursor pagination.

- `GET /products?q=&brand=&category=&ingredient=`; `GET /products/{id}`; `GET /products/{id}/versions`
- `POST /products/identify` (barcode or image -> candidates; async for OCR)
- `GET /ingredients/{id}`; `POST /ingredients/normalize`
- `POST /comparisons` (two product/version ids) -> comparison with findings; `GET /comparisons/{id}`
- `POST /skin-analyses` (multipart image + skin type) -> job id; `GET /skin-analyses/{id}` (status/result); `DELETE /skin-analyses/{id}`
- `POST /alternatives` (reference, mode, constraints); `GET /alternatives/{id}`
- Auth: `POST /auth/signup`, `/auth/login`, `/auth/logout`, `/auth/refresh`; `DELETE /me` (account deletion)
- `GET/PUT /me/profile`
- `GET/POST/DELETE /me/shelf`
- `GET/POST/PUT/DELETE /me/routines`; `POST /me/routines/{id}/check`
- `GET/POST/DELETE /me/history`
- `POST /shares` (target) -> token; `DELETE /shares/{token}`; `GET /public/shares/{token}`
- Admin: `GET /admin/flags`; `PATCH /admin/flags/{id}`; `GET/POST/PUT /admin/rules`; `GET/POST /admin/evidence`; `POST /admin/knowledge-versions`; `POST /admin/knowledge-versions/{id}/publish`; `GET /admin/audit`

Async jobs (OCR, skin analysis, ingestion) return a job/resource id and a status of `queued | running | succeeded | failed`, polled or pushed.

---

## 14. Non-Functional Requirements [SOURCE]

| ID | Attribute | Requirement |
|---|---|---|
| NFR-01 | Performance | Product search under 1 to 2 s; cached compatibility under 2 s; alternative search under 3 s where data exists; OCR and skin analysis asynchronous |
| NFR-02 | Security | Authentication, authorization, upload validation, private storage, secret management, rate limiting |
| NFR-03 | Availability | Retries, fallback states, graceful degradation; OCR or model outage never takes down search and comparison |
| NFR-04 | Maintainability | Modular domain services, typed interfaces, tests, documentation |
| NFR-05 | Scalability | Stateless API where possible, worker architecture, DB indexes, caching |
| NFR-06 | Usability | Core workflows minimize friction; always offer an understandable explanation and recovery action |
| NFR-07 | Accessibility | Keyboard nav, semantic markup, visible focus, labels, screen-reader support, adequate contrast |
| NFR-08 | Privacy | Private skin images with consent, minimal retention, deletion controls, private access policies |
| NFR-09 | Data integrity | Product fields, evidence, prices and formulations traceable to source, confidence and timestamp |
| NFR-10 | Explainability | Important results expose why they were produced and distinguish confidence from evidence strength |

---

## 15. Functional Requirements [SOURCE]

| ID | Name | Requirement |
|---|---|---|
| FR-01 | Product search | Search by supported product, brand, category and ingredient information |
| FR-02 | Product comparison | Compare two products |
| FR-03 | Ingredient normalization | Normalize ingredients to canonical representations with confidence and source |
| FR-04 | Compatibility evaluation | Generate findings from structured interaction rules |
| FR-05 | Compatibility explanation | Explain findings; expose evidence and confidence |
| FR-06 | Skin image upload | Allow users to upload skin images |
| FR-07 | Image validation | Validate file type, size, decoding and image quality before analysis |
| FR-08 | Skin observations | Generate supported visual cosmetic observations |
| FR-09 | Observation confidence | Attach confidence to observations |
| FR-10 | Concern mapping | Map supported observations to recommendation categories |
| FR-11 | Product recommendations | Retrieve relevant products using structured knowledge, evidence and user fit |
| FR-12 | Product image input | Accept product images |
| FR-13 | Product identification | Identify products from search, barcode and image/OCR inputs |
| FR-14 | Alternative search | Find alternatives for an identified product |
| FR-15 | Alternative categories | Support cheaper, similar and premium categories |
| FR-16 | Routine-compatible alternatives | Support where data supports the comparison |
| FR-17 | Save products | Registered users can save products |
| FR-18 | Create routines | Registered users can create routines |
| FR-19 | Share results | Public sharing for appropriate results; sensitive skin-analysis results private by default |
| FR-20 | Account deletion | Account deletion and comprehensive deletion of associated analysis data where applicable |

---

## 16. Safety, Privacy and Ethics Requirements [SOURCE]
1. Observations are estimates, with the lighting/camera/makeup/filter/angle disclaimer shown on every analysis.
2. No medical claims: no diagnosis of acne, rosacea, melasma, eczema or other conditions; no prescription or treatment.
3. No universal safety claims; "no notable interaction identified" refers only to the current knowledge base and supplied formulations.
4. Unknowns stay unknown: unresolved ingredients and incomplete formulations are surfaced as incomplete.
5. Private by default: consent, minimal retention, private access; sharing never exposes a skin analysis by default.
6. No commercial influence on compatibility results or evidence strength.
7. Scientific claims must be supported by evidence records.

**[PROPOSED] additional safeguards:** images stored encrypted, in private buckets, with signed short-lived URLs; strip EXIF/location metadata on upload; default retention window (for example delete raw images after analysis unless the user saves them); do not use user images to train models without explicit opt-in; rate-limit uploads; age-appropriate terms (e.g. 18+ or parental guidance) as a policy decision; compliance with applicable data-protection law (e.g. India's DPDP Act).

---

## 17. Data and Content Needs [PROPOSED]
The site is only as good as its data. Before launch, seed:
- **Ingredient master:** canonical/INCI names, aliases, function classes, considerations (a few hundred to start).
- **Products and formulations:** a starter catalogue (for example 200 to 1,000 products) with ingredient lists, brands, categories, observed dates, sources.
- **Interaction rules and evidence records** for well-known pairs (retinoids with AHAs/BHAs, retinoids with benzoyl peroxide, vitamin C with certain actives, niacinamide interactions, duplicated exfoliating acids, etc.), each with citation and strength, authored via the admin tool and published as KnowledgeVersion 1. The exact rule content must be reviewed against credible sources; do not rely on unreviewed claims.
- **Concern mapping table:** observation, concern category, recommended ingredient classes.
- **Price observations** with seller/currency/timestamp, refreshed by a worker.
- A clear data-licensing and provenance plan for product and price sources.

---

## 18. States and Error Handling Matrix [PROPOSED]

| Flow | Loading | Empty | Partial | Error |
|---|---|---|---|---|
| Search | skeleton list | "No results" with broaden/scan/report | n/a | retry with request ID |
| Compare | step progress | n/a | incomplete formulation notice, limited findings | not found, ambiguous (candidates), service error |
| Analyze skin | upload and analysis progress | n/a | some low-confidence observations | invalid image, model down (retry later), upload failed |
| Alternatives | skeleton | "No alternatives found" with relax-filters tip | stale/unavailable prices | low identification confidence |
| Shelf/Routine | skeleton | onboarding prompt | missing product data | duplicate item, persistence failure |
| Share | n/a | n/a | n/a | revoked token, sensitive result refusal |
| Admin | skeleton | "Queue clear" | conflicting evidence | publish blocked with reasons |

---

## 19. Testing and Validation [SOURCE + PROPOSED]
- **Verification** (built it right): every FR has at least one test that can fail. **Validation** (built the right thing): acceptance criteria and the three user questions.
- **Unit:** ingredient normalization, rule evaluation, image-validation predicates, similarity scoring.
- **Integration:** comparison through the API; skin-analysis worker pipeline; alternatives with price enrichment.
- **System/E2E:** full workflows with loading, success, empty, partial and error states.
- **Black box:** low-quality image rejection, ambiguous product confirmation, missing-price behaviour.
- **White box:** branch coverage of the rule engine including the insufficient-evidence path.
- **Non-functional:** timed search/comparison targets; security review; accessibility audit; disable OCR or the model and confirm search and comparison still work.
- **Definition of done:** unit, integration and E2E tests, security and accessibility review, CI/CD, error monitoring.

### Acceptance criteria [SOURCE]
- **Product:** search and product pages work; ingredient lists normalized; product versions exist.
- **Compatibility:** two products can be compared; results deterministic; evidence and unknown data shown.
- **Skin:** images upload; quality checks work; observations have confidence; recommendation mapping structured; medical boundary visible.
- **Alternatives:** products identified; alternatives retrieved; cheaper/similar categories work; price timestamps and ranking reasons shown.
- **User:** signup, save, shelf, routine and history workflows work.
- **Engineering:** unit/integration/E2E tests, security/accessibility checks, CI/CD, error monitoring present.

---

## 20. Agile Plan and Build Order [SOURCE]
Ten one-week sprints (a student planning estimate, each ending in working software):

| Sprint | Output |
|---|---|
| 0 | Architecture, repo, environments, database, auth, UI system, CI/CD |
| 1 | Product and ingredient schema, search, product pages |
| 2 | Compatibility rules, comparison API and UI, evidence |
| 3 | Scanner, OCR, ingredient normalization and review |
| 4 | Skin upload, quality pipeline, model adapter |
| 5 | Concern mapping and recommendations |
| 6 | Alternatives, similarity, price observations |
| 7 | My Shelf and routine building |
| 8 | Sharing, SEO, analytics |
| 9 | Security, testing, accessibility, performance |

**Recommended order for an LLM building this:** schema and seed data, then search and product pages, then ingredient normalization, then compatibility engine and comparison UI (this is the heart; get it right first), then auth, then shelf/routine, then alternatives, then OCR/scan, then skin analysis, then sharing, admin tooling, hardening. Keep the deterministic core independent of OCR and ML.

### SDLC and requirements phases
Life cycle phases: feasibility and selection, requirements analysis, modelling, design, construction, testing, deployment, maintenance and evolution (knowledge versioning, data review, price refresh, formulation changes). Requirements engineering: inception, elicitation, elaboration, negotiation, specification, validation, management. Traceability chain: user need, requirement, use case, behaviour, structure, data flow, architecture, backlog, validation. Example: "Can I use these two products together?" maps to FR-02/04/05, UC02, comparison swimlane, Product/ProductVersion/Ingredient/InteractionRule/EvidenceRecord/Comparison/ComparisonFinding, the Compatibility service behind `/api/v1` over PostgreSQL and Redis, US-002 and story card SC-01 in Sprint 2, and rule/normalization/integration tests plus SC-01 acceptance criteria.

---

## 21. User Stories and Story Cards [SOURCE]

| ID | Story | Priority | Traces to |
|---|---|---|---|
| US-001 | As a skincare user, I want to search for a product so that I can inspect it before deciding what to use | Medium | FR-01 |
| US-002 | As a skincare user, I want to compare two products so that I can understand relevant ingredient interactions before adding both to my routine | High | FR-02, 04, 05 |
| US-003 | As a data reviewer, I want raw ingredient labels normalized to canonical ingredients so that comparison logic operates on consistent data | High | FR-03 |
| US-004 | As a skincare user, I want to upload a skin image so that I can see supported cosmetic observations with confidence | High | FR-06 to 10 |
| US-005 | As a user, I want to scan or upload a product so that I do not have to identify it manually | Medium | FR-12, 13 |
| US-006 | As a user, I want alternatives to a product so that I can consider cheaper, similar or premium options | High | FR-14 to 16 |
| US-007 | As a registered user, I want to save products so that I can reuse them in comparisons and routines | Medium | FR-17 |
| US-008 | As a registered user, I want to create a morning or evening routine so that I can organize my products and analyze their compatibility | High | FR-18 |
| US-009 | As a user, I want to share an appropriate result so that another person can inspect the same information | Low | FR-19 |
| US-010 | As a registered user, I want to delete my account and associated analysis data so that my private information is removed | High | FR-20 |

**Story cards (acceptance criteria)**
- **SC-01 Compare Two Products:** Given two identified products, when the user starts the comparison, then SkinSync resolves formulations, normalizes ingredients, evaluates interaction rules, displays status, explanation and evidence, and shows confidence and unresolved data. Constraints: versions resolved; deterministic; no unsupported universal safety claim.
- **SC-02 Analyze Skin:** image uploads; invalid images rejected; quality checked; observations carry confidence; limitations shown; no diagnosis claimed. Private image handling and deletion rules apply.
- **SC-03 Find Alternatives:** product identified; ambiguous matches need confirmation; alternatives ranked with visible reasons; price timestamps shown; unavailable prices not invented; low-confidence identification not presented as certain.
- **SC-04 Build and Analyze Routine:** products can be added and ordered; routine saves; pairwise compatibility evaluated; duplicated actives and missing data surfaced; evidence available; missing data never silently treated as safe.
- **SC-05 Review Product Data:** flags show reason and source; reviewer can correct or approve; knowledge versioned; publication status recorded; unsupported claims stay unpublished.

---

## 22. Glossary [SOURCE]
- **INCI:** International Nomenclature of Cosmetic Ingredients, the standard ingredient naming used for normalization.
- **Compatibility:** structured evaluation of relevant ingredient interactions, redundancy, uncertainty and evidence for two formulations.
- **Observation:** a visible cosmetic feature detected from a skin image; not a medical diagnosis.
- **Evidence strength:** controlled scale: High, Moderate, Limited, Insufficient, Unknown.
- **Confidence:** how certain the system is about an identification, normalization, observation or finding. Distinct from evidence strength.
- **Knowledge version:** identifier of the published compatibility/recommendation knowledge used to produce a result.
- **Product version:** formulation-specific representation of a product (ingredients, market, observed date).
- **My Shelf:** a registered user's saved products.
- **Completeness:** how fully a product's formulation or a result's inputs are known.

---

## 23. Open Decisions and Assumptions [PROPOSED]
1. Source of product and price data (licensed API, scraping with permission, curated dataset)? Affects legality and freshness.
2. Skin analysis model: build, fine-tune, or use a third-party service? Which observations are "supported" in v1 (for example redness, shine/oiliness, visible texture, dark spots, dryness signs)? Must stay cosmetic.
3. OCR provider and barcode source (for example open product databases).
4. Authentication method (email/password only vs social sign-in) and age policy.
5. Image retention default and legal basis.
6. Initial scope of interaction rules and who reviews them for scientific accuracy.
7. Regions and currencies at launch (India first? INR?).
8. Hosting, budget and deployment target.
9. Whether an LLM is used at all (for phrasing explanations only, never for deciding results).
10. Monetization, if any, and how neutrality (principle 10) is enforced.

---

## 24. Instructions for an LLM Building This Site
1. Treat sections 1.1, 2, 12 and 16 as hard constraints: deterministic rules decide compatibility; no diagnosis; unknown stays unknown; private by default.
2. Build the deterministic core first (schema, seed data, search, normalization, compatibility, explainability panel). OCR and skin-model features must be pluggable behind adapters and optional at runtime.
3. Implement the explainability panel as one reusable component used on every result.
4. Version everything that changes over time (formulations, prices, knowledge) and stamp it on stored results.
5. Implement every flow with the full state set in section 18.
6. Write tests alongside features, tracing each to an FR/NFR ID.
7. Where this document is silent, choose the simplest option consistent with the principles in 1.2 and list the choice in an `ASSUMPTIONS.md`.
8. Do not invent scientific claims, ingredient interactions or prices. All such content must come from reviewed seed data with citations.
