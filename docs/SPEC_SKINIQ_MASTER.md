# SkinIQ --- Complete 10/10 Website Master Specification

**Product:** SkinIQ\
**Tagline:** **Check before you layer.**\
**Product category:** Skincare intelligence / personalized skincare
decision platform\
**Document status:** Implementation-ready master product, UX,
architecture, data, AI/ML, software-engineering and growth
specification\
**Primary goal:** Build a technically defensible, highly usable skincare
platform that can attract organic users, provide immediate utility
without mandatory signup, and create strong retention through
personalization.

------------------------------------------------------------------------

# 1. Executive Summary

SkinIQ is a web platform that helps people make better skincare
decisions through four connected capabilities:

1.  **Skin Analysis** --- a user provides their skin type and a skin
    image; the system performs image-based cosmetic observations such as
    visible pores, fine lines/wrinkles, dark circles, acne/acne marks
    and pigmentation, with confidence and limitations.
2.  **Product Discovery & Recommendations** --- SkinIQ maps relevant
    skin concerns to evidence-aware ingredient categories and then to
    suitable products.
3.  **Product Compatibility** --- the user selects two skincare products
    and SkinIQ compares their ingredients to identify relevant
    interactions, redundancies, concerns, unknowns and evidence
    strength.
4.  **Product Alternatives** --- the user enters or uploads a product
    and SkinIQ finds alternatives across cheaper, similar, premium,
    ingredient-focused and routine-compatible categories.

Supporting capabilities include:

-   Product search
-   Product image scanning
-   Ingredient-list OCR
-   Manual ingredient entry
-   Ingredient explorer
-   Product pages
-   Routine builder
-   My Shelf
-   Saved products
-   History
-   Public shareable results
-   SEO landing pages
-   Analytics
-   Admin/data-quality workflows

SkinIQ is therefore **not merely a skincare database** and not merely a
chatbot.

It is a **skincare decision engine**:

``` text
USER INPUT
    ↓
PRODUCT / INGREDIENT / SKIN IMAGE DATA
    ↓
STRUCTURED REPRESENTATION
    ↓
NORMALIZATION + KNOWLEDGE + EVIDENCE
    ↓
DETERMINISTIC DOMAIN LOGIC
    ↓
PERSONALIZED RESULT
    ↓
TRANSPARENT EXPLANATION
    ↓
USER DECISION
```

The most important architectural rule is:

> **AI can assist with perception, extraction and explanation, but
> high-impact skincare conclusions should be grounded in structured
> data, explicit rules, confidence and evidence rather than an opaque
> model-generated answer.**

------------------------------------------------------------------------

# 2. Product Vision

## 2.1 Vision

Make skincare decisions understandable enough that a user can go from:

> "I have this skin concern and these products. What should I use, what
> should I avoid combining, and what alternatives are worth
> considering?"

to a clear, evidence-aware answer in minutes.

## 2.2 Mission

SkinIQ should reduce three major sources of skincare confusion:

-   uncertainty about visible skin concerns,
-   uncertainty about product compatibility,
-   uncertainty about which product is actually worth buying.

## 2.3 Core promise

> **Understand your skin. Understand your products. Make better skincare
> decisions.**

------------------------------------------------------------------------

# 3. The Three Primary Questions

SkinIQ should answer three high-frequency questions.

### Question 1 --- Skin

> **What does my skin appear to need?**

Input:

-   skin type,
-   skin image,
-   optional preferences.

Output:

-   supported visual observations,
-   confidence,
-   concern-specific ingredient categories,
-   product recommendations.

### Question 2 --- Compatibility

> **Can I use these products together?**

Input:

-   Product A,
-   Product B.

Output:

-   relevant ingredient interactions,
-   evidence,
-   conflicts/duplication,
-   uncertainty,
-   practical layering guidance.

### Question 3 --- Alternatives

> **What are my alternatives to this product?**

Input:

-   product name,
-   image,
-   barcode,
-   URL where supported,
-   saved product.

Output:

-   cheaper alternatives,
-   similar alternatives,
-   premium alternatives,
-   ingredient-focused alternatives,
-   routine-compatible alternatives,
-   transparent comparison dimensions.

------------------------------------------------------------------------

# 4. What Makes SkinIQ Different

The product should differentiate itself through the combination of:

``` text
Skin analysis
      +
Product intelligence
      +
Ingredient normalization
      +
Evidence
      +
Compatibility
      +
Alternatives
      +
Personalization
```

Most product features should connect to the same underlying
product/ingredient/evidence graph.

For example:

``` text
Skin concern
    ↓
Ingredient category
    ↓
Product candidates
    ↓
Alternative products
    ↓
Compatibility with current shelf
    ↓
Routine
```

This reuse makes the system technically coherent and gives the user a
reason to keep returning.

------------------------------------------------------------------------

# 5. Target Users

## 5.1 Beginner skincare user

Needs:

-   simple explanations,
-   product comparison,
-   ingredient education,
-   routine help.

## 5.2 Ingredient-conscious user

Needs:

-   ingredient lists,
-   INCI normalization,
-   evidence,
-   compatibility analysis.

## 5.3 Budget-conscious user

Needs:

-   cheaper alternatives,
-   price comparisons,
-   value-oriented recommendations.

## 5.4 Routine builder

Needs:

-   product shelf,
-   morning/evening routine,
-   compatibility checks,
-   sequence guidance.

## 5.5 Skincare enthusiast

Needs:

-   detailed ingredient information,
-   advanced comparison,
-   evidence,
-   product versions,
-   formulation differences.

------------------------------------------------------------------------

# 6. Product Scope

## 6.1 In scope

-   Web application
-   Responsive desktop/tablet/mobile UI
-   Guest comparison
-   User accounts
-   Product database
-   Ingredient database
-   Ingredient normalization
-   Compatibility engine
-   Skin-analysis pipeline
-   Product alternative engine
-   OCR
-   Product scanner
-   Recommendations
-   Routine builder
-   My Shelf
-   Search
-   SEO pages
-   Sharing
-   Analytics
-   Admin/data governance
-   Testing
-   Deployment

## 6.2 Out of scope for the initial release

-   Medical diagnosis
-   Dermatological diagnosis
-   Prescription treatment
-   Guaranteed treatment outcomes
-   Universal "safe/unsafe" claims
-   Fully autonomous medical recommendations
-   Automated purchasing without user confirmation
-   Claims that a product is objectively "best" without a defined
    methodology

------------------------------------------------------------------------

# 7. Complete Website Information Architecture

``` text
/
├── Home
├── Analyze My Skin
│   ├── Upload / Capture
│   ├── Image Quality Check
│   ├── Analysis
│   └── Results
├── Compare Products
│   ├── Select Product A
│   ├── Select Product B
│   ├── Ingredient Comparison
│   ├── Compatibility Result
│   └── Evidence
├── Find Alternatives
│   ├── Product Search
│   ├── Product Upload
│   ├── Product Identification
│   ├── Filters
│   └── Alternative Results
├── Products
│   ├── Product detail
│   └── Alternatives
├── Ingredients
│   ├── Ingredient explorer
│   └── Ingredient detail
├── Brands
│   └── Brand pages
├── Routine
│   ├── Create routine
│   ├── Analyze routine
│   └── Routine results
├── My Shelf
│   ├── Saved products
│   └── Scan shelf
├── History
├── Shared Results
├── About
├── How It Works
├── Evidence / Methodology
├── Privacy
├── Terms
└── Admin
```

------------------------------------------------------------------------

# 8. Navigation

Desktop:

``` text
SkinIQ
────────────────────────────────────────────────────────
Analyze Skin | Compare | Alternatives | Ingredients
Products | Routine | My Shelf                    [Sign in]
```

Mobile:

``` text
[SkinIQ]                         [☰]

Analyze Skin
Compare
Alternatives
Products
Ingredients
Routine
My Shelf
Sign in
```

The three primary CTAs should remain visually dominant:

-   **Analyze My Skin**
-   **Compare Products**
-   **Find Alternatives**

------------------------------------------------------------------------

# 9. Homepage

## 9.1 Hero

Headline:

> **Understand your skin. Choose your products with confidence.**

Subheadline:

> Analyze visible skin concerns, compare skincare products, and discover
> better alternatives --- all in one place.

Primary actions:

``` text
[ Analyze My Skin ]
[ Compare Products ]
[ Find Alternatives ]
```

Secondary:

``` text
No account required for basic comparison.
```

## 9.2 Hero interaction

A high-value homepage should let users immediately start a workflow.

Example:

``` text
What do you want to do?

[ Analyze my skin ]
[ Compare two products ]
[ Find an alternative ]
```

## 9.3 Trust section

Explain:

-   ingredient-based analysis,
-   evidence-aware results,
-   transparent uncertainty,
-   product-data freshness,
-   no medical diagnosis.

## 9.4 Example result preview

Show a realistic but clearly labeled demo result.

## 9.5 SEO content

Homepage should contain useful explanatory copy around:

-   skincare ingredient compatibility,
-   product comparison,
-   skincare routines,
-   ingredient analysis,
-   product alternatives.

------------------------------------------------------------------------

# 10. Guest Experience

The user should not be forced to register before experiencing the
product's core value.

Guest users can:

-   search products,
-   compare two products,
-   inspect ingredients,
-   perform limited skin analysis,
-   find alternatives,
-   view public pages.

Signup is encouraged when the user wants:

-   save,
-   history,
-   routine,
-   My Shelf,
-   repeated analyses,
-   personalized preferences,
-   share management.

This creates:

``` text
VALUE FIRST
    ↓
TRUST
    ↓
OPTIONAL ACCOUNT
    ↓
PERSONALIZATION
```

------------------------------------------------------------------------

# 11. Account Experience

After login:

``` text
Dashboard
├── My Skin Profile
├── My Shelf
├── My Routines
├── Saved Products
├── Saved Comparisons
├── Skin Analyses
└── History
```

------------------------------------------------------------------------

# 12. Skin Analysis --- Product Definition

## 12.1 User flow

``` text
Analyze My Skin
      ↓
Select skin type
      ↓
Upload / capture image
      ↓
Image quality validation
      ↓
Skin image analysis
      ↓
Structured observations
      ↓
Confidence + severity
      ↓
Concern mapping
      ↓
Ingredient recommendations
      ↓
Product recommendations
      ↓
Compatibility check
      ↓
Save / routine / alternatives
```

## 12.2 Skin type input

Options:

-   Dry
-   Oily
-   Combination
-   Normal
-   Sensitive / easily irritated
-   Unsure

The user should be able to choose:

> "I'm not sure"

because forcing a classification would create false precision.

------------------------------------------------------------------------

# 13. Skin Image Requirements

The system should provide guidance before capture:

``` text
For better results:
✓ Use natural or even lighting
✓ Keep face unobstructed
✓ Avoid beauty filters
✓ Avoid heavy makeup
✓ Keep camera focused
✓ Use a clear, front-facing image
```

Optional later enhancement:

-   left profile,
-   right profile,
-   close-up areas.

------------------------------------------------------------------------

# 14. Image Upload Validation

Validate:

-   file extension,
-   MIME type,
-   actual file signature,
-   file size,
-   image dimensions,
-   image decoding,
-   corruption,
-   unsafe content,
-   quality.

Do not trust only the browser-provided MIME type.

OWASP recommends allowlisting safe extensions, validating file
type/signature, generating safe filenames, applying size limits and
controlling access to uploaded files. citeturn1search2

------------------------------------------------------------------------

# 15. Skin Image Quality Pipeline

``` text
UPLOAD
  ↓
TYPE VALIDATION
  ↓
SIZE VALIDATION
  ↓
DECODE
  ↓
IMAGE QUALITY MODEL
  |
  +── Good → continue
  |
  +── Poor → explain why
              ↓
          Retake image
```

Possible failure reasons:

-   too dark,
-   too bright,
-   blurry,
-   too distant,
-   face/skin region not sufficiently visible,
-   heavy filter,
-   obstruction,
-   low resolution.

------------------------------------------------------------------------

# 16. Skin Analysis Outputs

Initial supported observations:

-   fine lines / wrinkles,
-   visible pores,
-   dark circles,
-   acne/acne-like visible lesions,
-   acne marks,
-   pigmentation/dark spots,
-   uneven-looking tone,
-   redness where model performance supports it.

Important:

These are **visual cosmetic observations**, not diagnoses.

Example:

``` text
VISIBLE SKIN OBSERVATIONS

Fine lines
Moderate confidence

Visible pores
High confidence

Dark circles
Moderate confidence

Acne marks
High confidence

Pigmentation
Moderate confidence
```

------------------------------------------------------------------------

# 17. Confidence Model

Every observation should have:

``` text
observation
confidence
severity_estimate
model_version
```

Example:

``` json
{
  "concern": "visible_pores",
  "confidence": 0.86,
  "severity": "moderate",
  "model_version": "skin-model-0.3"
}
```

Do not expose raw probability without context unless useful.

Prefer:

-   High confidence
-   Moderate confidence
-   Low confidence

------------------------------------------------------------------------

# 18. Skin Analysis Recommendation Engine

The image model must not directly invent a product.

Correct architecture:

``` text
IMAGE
  ↓
MODEL
  ↓
OBSERVATION
  ↓
KNOWLEDGE BASE
  ↓
RELEVANT INGREDIENT CATEGORIES
  ↓
EVIDENCE
  ↓
PRODUCT RETRIEVAL
  ↓
PERSONALIZATION
  ↓
RECOMMENDATIONS
```

This separates perception from recommendation.

------------------------------------------------------------------------

# 19. Concern → Ingredient Mapping

The knowledge base should contain:

``` text
Concern
Ingredient/category
Intended role
Evidence level
Contraindication notes
Compatibility notes
Supported product types
Source references
Last reviewed
Reviewer
```

Example structure:

``` text
Concern:
Acne marks

Ingredient category:
[example category]

Purpose:
Support appearance of post-acne discoloration

Evidence:
Moderate / High / Limited

Notes:
Do not represent as treatment of a medical condition.
```

The exact ingredient mappings must be reviewed against reliable sources
before production.

COSMILE Europe provides verified cosmetic ingredient information,
including ingredient functions, product types and INCI terminology, and
currently describes information for almost 30,000 cosmetic ingredients.
citeturn0search1turn0search2

------------------------------------------------------------------------

# 20. Product Recommendation Ranking

Candidate products should be ranked using:

``` text
Concern relevance
+
Ingredient/category match
+
Evidence strength
+
Skin-type fit
+
User preferences
+
Product-data confidence
+
Routine compatibility
+
Price preference
```

No single opaque "magic score" should determine the result.

------------------------------------------------------------------------

# 21. Skin Analysis Result Page

``` text
┌──────────────────────────────────────────────┐
│ YOUR SKIN ANALYSIS                           │
│                                              │
│ [IMAGE]       Skin type: Combination         │
│                                              │
│ VISIBLE OBSERVATIONS                         │
│                                              │
│ Fine lines       Moderate confidence         │
│ Visible pores    High confidence             │
│ Dark circles     Moderate confidence         │
│ Acne marks       High confidence             │
│ Pigmentation     Moderate confidence         │
└──────────────────────────────────────────────┘

WHAT YOU CAN EXPLORE

[Acne marks]
Relevant ingredient categories
[See products]

[Pores]
Relevant ingredient categories
[See products]

[Pigmentation]
Relevant ingredient categories
[See products]

[Build a routine]
```

------------------------------------------------------------------------

# 22. Skin Analysis Safety Boundary

The interface must clearly communicate:

> Image analysis is an estimate based on the uploaded image. Lighting,
> camera quality, makeup, filters and image angle can affect results.
> This feature is for cosmetic skincare guidance and is not a medical
> diagnosis.

If concerning symptoms are described by the user, SkinIQ should not
attempt diagnosis.

------------------------------------------------------------------------

# 23. Product Input Methods

Every product workflow should support:

1.  Search by name
2.  Search by brand
3.  Barcode
4.  Product image
5.  Ingredient-list image
6.  Manual ingredient entry
7.  Saved product
8.  Product URL where supported

------------------------------------------------------------------------

# 24. Product Search

Search should support:

-   product name,
-   brand,
-   category,
-   active ingredient,
-   partial names,
-   common misspellings,
-   INCI names where useful.

Ranking:

``` text
Exact product
→ exact brand + product
→ strong textual match
→ ingredient/category match
→ popularity/data confidence
```

------------------------------------------------------------------------

# 25. Product Scanner

User:

``` text
[ Scan Product ]
```

Camera states:

1.  Permission request
2.  Camera ready
3.  Detecting barcode
4.  Barcode found
5.  Product found
6.  Product ambiguous
7.  Product unavailable
8.  Retry

Fallback:

``` text
Can't find it?
[Upload product image]
[Enter product name]
```

------------------------------------------------------------------------

# 26. Ingredient OCR

If the user uploads an ingredient-list image:

``` text
IMAGE
 ↓
OCR
 ↓
RAW OCR TEXT
 ↓
TEXT CLEANING
 ↓
INGREDIENT SEGMENTATION
 ↓
INCI NORMALIZATION
 ↓
MATCH CONFIDENCE
 ↓
USER REVIEW
 ↓
CANONICAL INGREDIENT LIST
```

Cloud Vision's OCR supports text detection and dense document text
detection, including extracted text and positional information.
citeturn0search7turn0search10

OCR output is never automatically treated as ground truth.

------------------------------------------------------------------------

# 27. OCR Review UI

Example:

``` text
WE FOUND 28 INGREDIENTS

✓ Aqua
✓ Glycerin
✓ Niacinamide

⚠ Tocopher...?
     Possible match:
     Tocopherol

     [Accept] [Change] [Remove]
```

Unknown ingredients must remain unknown rather than being silently
mapped.

------------------------------------------------------------------------

# 28. Ingredient Normalization

Canonical representation:

``` text
Raw label
    ↓
Clean text
    ↓
Alias resolution
    ↓
INCI candidate
    ↓
Canonical ingredient
    ↓
Confidence
    ↓
Source
```

Store:

``` text
raw_value
canonical_value
normalization_method
confidence
source
review_status
```

------------------------------------------------------------------------

# 29. Product Data Model

A product is not just a name.

``` text
Product
├── brand
├── name
├── category
├── country/market
├── barcode(s)
├── ingredients
├── formulation/version
├── product images
├── source records
├── observed prices
├── availability
└── timestamps
```

------------------------------------------------------------------------

# 30. Product Versioning

Formulations change.

Therefore:

``` text
Product
  ├── Version A
  ├── Version B
  └── Version C
```

Each version should support:

-   ingredient list,
-   source,
-   observed date,
-   market,
-   formulation notes.

Compatibility should ideally use the most relevant/current formulation.

------------------------------------------------------------------------

# 31. Product Provenance

Every important product field should be traceable to:

``` text
source
source_type
retrieved_at
confidence
verification_status
```

Example:

``` text
Ingredient list
Source: manufacturer label
Retrieved: 2026-09-06
Confidence: high
```

------------------------------------------------------------------------

# 32. Product Data Sources

Candidate sources should be evaluated for:

-   coverage,
-   freshness,
-   licensing,
-   attribution,
-   API availability,
-   rate limits,
-   redistribution rights,
-   geographic coverage.

Do not copy commercial databases without verifying rights.

COSMILE Europe is useful as an ingredient-information reference and
provides verified ingredient/function information, but product-data
licensing and redistribution must be checked separately before use.
citeturn0search2

------------------------------------------------------------------------

# 33. Product Compatibility --- Core Feature

## User question

> **Can I use these two products together?**

Inputs:

``` text
Product A
Product B
```

Pipeline:

``` text
Product A
  ↓
Canonical ingredients
  ↓
Evidence / interaction knowledge

Product B
  ↓
Canonical ingredients
  ↓
Evidence / interaction knowledge

          ↓

PAIRWISE EVALUATION
          ↓
RESULT
```

------------------------------------------------------------------------

# 34. Compatibility Taxonomy

Use a controlled result taxonomy.

### A. No notable interaction identified

Meaning:

> No relevant interaction is currently identified in SkinIQ's knowledge
> base for the supplied formulations.

This does **not** mean universally safe for everyone.

### B. Potential interaction / caution

A relevant concern exists but does not justify a categorical
prohibition.

### C. Strong caution

The combination has a sufficiently important concern that the user
should reconsider the combination or seek more specific guidance.

### D. Insufficient evidence

The system does not have enough reliable information to make a strong
conclusion.

### E. Data incomplete

One or both formulations are incomplete or uncertain.

------------------------------------------------------------------------

# 35. Compatibility Result UI

``` text
PRODUCT A
+
PRODUCT B

COMPATIBILITY

Potential caution

WHY?
Both products contain ingredients
with a relevant interaction pattern.

WHAT WE FOUND

Product A:
[Ingredient]

Product B:
[Ingredient]

Evidence:
Moderate

WHAT TO DO

Consider separating use or simplifying
the routine if irritation occurs.

[See evidence]
[View ingredients]
[Save comparison]
```

------------------------------------------------------------------------

# 36. Compatibility Engine

The engine should be deterministic.

Inputs:

``` text
product_a_id
product_b_id
formulation_versions
canonical_ingredients
evidence_records
knowledge_version
```

Output:

``` json
{
  "status": "caution",
  "confidence": "moderate",
  "findings": [],
  "shared_ingredients": [],
  "unresolved_ingredients": [],
  "evidence": [],
  "knowledge_version": "2026-09"
}
```

------------------------------------------------------------------------

# 37. Ingredient Interaction Record

``` text
InteractionRule
----------------
ingredient_a
ingredient_b
interaction_type
severity
evidence_strength
mechanism_summary
practical_guidance
source_ids
review_status
last_reviewed
knowledge_version
```

Possible interaction types:

-   redundancy,
-   irritation concern,
-   formulation conflict,
-   pH-sensitive concern,
-   duplicate active load,
-   evidence-limited interaction,
-   no notable concern.

Do not encode scientific claims without evidence.

------------------------------------------------------------------------

# 38. Ingredient Comparison

The comparison page should have:

``` text
SHARED INGREDIENTS

Ingredient A
Ingredient B

PRODUCT A ONLY

...

PRODUCT B ONLY

...

UNRESOLVED

...

WHY IT MATTERS

...
```

------------------------------------------------------------------------

# 39. "Why Was This Flagged?"

Every important result should be explainable.

Example:

``` text
Why was this flagged?

1. Ingredient X was identified in Product A.
2. Ingredient Y was identified in Product B.
3. SkinIQ has a knowledge-base rule connecting this
   combination with a potential irritation concern.
4. Current evidence strength: Moderate.
5. This result is based on knowledge version 2026-09.
```

------------------------------------------------------------------------

# 40. Evidence Model

Evidence should be stored separately from the UI text.

``` text
EvidenceRecord
--------------
id
claim
source_type
source_reference
evidence_strength
publication_date
retrieved_at
review_status
notes
```

Potential source categories:

-   official regulatory/ingredient databases,
-   peer-reviewed literature,
-   professional guidance,
-   manufacturer information,
-   curated expert-reviewed knowledge.

------------------------------------------------------------------------

# 41. Evidence Strength

Suggested controlled values:

``` text
High
Moderate
Limited
Insufficient
Unknown
```

Evidence strength is not the same as model confidence.

Keep separate:

``` text
Data confidence
Ingredient identification confidence
Model confidence
Evidence strength
```

------------------------------------------------------------------------

# 42. Product Alternative Finder

## User question

> **What are the alternatives to this product?**

Inputs:

-   product name,
-   product image,
-   barcode,
-   ingredient image,
-   saved product.

------------------------------------------------------------------------

# 43. Alternative Search Pipeline

``` text
USER INPUT
    ↓
PRODUCT IDENTIFICATION
    ↓
CANONICAL PRODUCT
    ↓
FEATURE EXTRACTION
    |
    +── ingredients
    +── category
    +── target use
    +── formulation
    +── price
    +── brand
    +── user preferences
    ↓
CANDIDATE RETRIEVAL
    ↓
FILTERING
    ↓
RANKING
    ↓
ALTERNATIVE RESULTS
```

------------------------------------------------------------------------

# 44. Alternative Categories

### Cheaper

Lower observed price while maintaining meaningful similarity.

### Similar

Similar formulation/ingredient profile.

### Premium

Higher-priced alternatives with relevant differentiating attributes.

### Ingredient-focused

Prioritize products containing selected target ingredients.

### Routine-compatible

Prioritize products compatible with the user's current routine.

### Sensitive-preference

Products matching user-defined ingredient preferences where the
underlying data supports the comparison.

------------------------------------------------------------------------

# 45. Alternative Ranking

Do not use an unexplained "best product" score.

Expose dimensions:

``` text
Ingredient similarity
Target-ingredient match
Product category match
Price difference
Routine compatibility
Data confidence
Evidence strength
Preference match
```

Example:

``` text
WHY THIS ALTERNATIVE?

✓ 82% ingredient-profile similarity
✓ 28% lower observed price
✓ Same product category
✓ Similar target ingredients
△ Different texture/formulation
```

------------------------------------------------------------------------

# 46. Similarity Algorithm

A transparent first implementation can combine:

``` text
Category similarity
Ingredient-set similarity
Target-active similarity
Formulation attributes
User preference match
```

Ingredient similarity can use weighted overlap rather than raw Jaccard
similarity.

Example conceptual formula:

``` text
Similarity =
    0.35 × ingredient_similarity
  + 0.20 × target_match
  + 0.15 × category_match
  + 0.15 × preference_match
  + 0.15 × formulation_similarity
```

The weights must be treated as product-design parameters and validated
with test cases rather than presented as scientific truth.

------------------------------------------------------------------------

# 47. Price Model

Store observations:

``` text
product_id
seller
country
currency
price
availability
source
observed_at
```

Never represent a time-sensitive price as permanently current.

Display:

> Price observed on \[date\].

If no trustworthy price is available:

> Price unavailable.

Never invent prices.

------------------------------------------------------------------------

# 48. "Better Quality" Definition

The product must not claim:

> Product B is objectively higher quality.

Instead decompose quality into measurable dimensions:

-   ingredient transparency,
-   evidence-backed target ingredients,
-   formulation fit,
-   data completeness,
-   preference fit,
-   price/value,
-   source reliability.

Use:

> **Better match for your preferences**

rather than an unsupported universal "better."

------------------------------------------------------------------------

# 49. Alternative Results UI

``` text
YOUR PRODUCT
[Image]
Product A

ALTERNATIVES

┌────────────────────────────────────────────┐
│ Product B                                  │
│ Similar formula                            │
│ 31% lower observed price                   │
│ Ingredient similarity: High                │
│ [Compare] [Save]                           │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ Product C                                  │
│ Premium alternative                        │
│ Similar target ingredients                  │
│ [Compare] [Save]                           │
└────────────────────────────────────────────┘
```

Filters:

``` text
[All]
[Cheaper]
[Similar]
[Premium]
[Ingredient-focused]
[Routine-compatible]
```

------------------------------------------------------------------------

# 50. Ingredient Explorer

Users can search:

-   INCI name,
-   common name,
-   ingredient category.

Ingredient page:

``` text
Ingredient Name

What it is
What it does
Common product types
Relevant skincare functions
Known considerations
Related ingredients
Products containing it
Evidence / sources
```

COSMILE Europe explicitly supports searching cosmetic ingredients by
common or INCI name and provides function/product-type information.
citeturn0search1

------------------------------------------------------------------------

# 51. Product Pages

Every product page should include:

``` text
Product image
Brand
Name
Category

Ingredients
Ingredient functions
Data confidence
Source / last verified

Compatibility
[Compare with another product]

Alternatives
[Cheaper]
[Similar]
[Premium]

Routine
[Add to routine]

Shelf
[Save]
```

SEO-friendly routes:

``` text
/products/{slug}
/products/{slug}/alternatives
```

------------------------------------------------------------------------

# 52. Routine Builder

Routine structure:

``` text
Morning
1. Cleanser
2. Treatment
3. Serum
4. Moisturizer
5. Sunscreen

Evening
1. Cleanser
2. Treatment
3. Serum
4. Moisturizer
```

Allow custom ordering.

------------------------------------------------------------------------

# 53. Routine Analysis

Pipeline:

``` text
ROUTINE PRODUCTS
      ↓
FORMULATION RESOLUTION
      ↓
INGREDIENT EXTRACTION
      ↓
PAIRWISE COMPATIBILITY
      ↓
DUPLICATION ANALYSIS
      ↓
USER PREFERENCES
      ↓
ROUTINE RESULT
```

Output:

-   potential conflicts,
-   duplicated actives,
-   missing data,
-   sequencing considerations,
-   evidence.

------------------------------------------------------------------------

# 54. My Shelf

Users can:

-   save products,
-   remove products,
-   search shelf,
-   scan shelf,
-   compare any two,
-   build routines,
-   find alternatives.

The shelf becomes a personalization layer for future recommendations.

------------------------------------------------------------------------

# 55. Cross-Feature Personalization

Example:

``` text
Skin Analysis
      ↓
Pigmentation concern
      ↓
User saves Product A
      ↓
Product A added to shelf
      ↓
SkinIQ checks current routine
      ↓
Alternative Product B suggested
      ↓
Product B compared against shelf
```

This is one of the strongest retention loops in the product.

------------------------------------------------------------------------

# 56. Sharing

Every useful result should be shareable.

Routes:

``` text
/share/{token}
```

Possible shared results:

-   product comparison,
-   alternative list,
-   ingredient page,
-   routine,
-   educational page.

Sensitive skin-analysis results should default to private.

------------------------------------------------------------------------

# 57. SEO Strategy

SEO should be a first-class subsystem.

Next.js supports metadata, Open Graph, robots, sitemap and structured
data mechanisms useful for SEO and shareability.
citeturn0search0turn0search3turn0search4

Target page families:

``` text
/products/{product}
products/{product}/alternatives
/ingredients/{ingredient}
/brands/{brand}
/compare/{a}-vs-{b}
/guides/{topic}
```

Only high-quality, sufficiently complete pages should be indexed.

Avoid generating millions of thin pages.

------------------------------------------------------------------------

# 58. SEO Content Strategy

Examples:

-   "Can I use X with Y?"
-   "X alternatives"
-   "Cheaper alternatives to X"
-   "X ingredient list"
-   "What does X do in skincare?"
-   "X vs Y"
-   "Skincare ingredient compatibility"
-   "How to build a routine"

Pages should provide actual utility rather than keyword stuffing.

------------------------------------------------------------------------

# 59. Structured Data

Where appropriate:

-   Product
-   BreadcrumbList
-   Article
-   WebSite
-   Organization

Validate generated structured data.

------------------------------------------------------------------------

# 60. Growth Loop

Core loop:

``` text
Google / Social
      ↓
SEO page
      ↓
Useful product/ingredient information
      ↓
Compare / Alternative / Analyze
      ↓
Useful result
      ↓
Share
      ↓
New visitor
```

------------------------------------------------------------------------

# 61. Retention Loop

``` text
Analyze skin
      ↓
Recommendations
      ↓
Save products
      ↓
Build shelf
      ↓
Build routine
      ↓
Compare new products
      ↓
Find alternatives
      ↓
Return
```

------------------------------------------------------------------------

# 62. Analytics

Core events:

``` text
landing_view
comparison_started
product_search
product_selected
comparison_completed

skin_analysis_started
skin_image_uploaded
skin_image_quality_failed
skin_analysis_completed
skin_observation_viewed
skin_recommendation_clicked

alternative_search_started
alternative_product_identified
alternative_search_completed
alternative_clicked
alternative_compared

ingredient_viewed
routine_created
routine_analyzed
product_saved
share_created
share_viewed

signup_started
signup_completed
```

------------------------------------------------------------------------

# 63. Growth Metrics

Track:

### Acquisition

-   unique visitors,
-   organic sessions,
-   landing page CTR,
-   share traffic.

### Activation

-   first comparison completed,
-   first skin analysis completed,
-   first alternative search completed.

### Engagement

-   comparisons/session,
-   products/session,
-   ingredient pages/session.

### Retention

-   returning users,
-   saved products,
-   routine creation,
-   repeat comparisons.

### Conversion

-   guest → account,
-   analysis → product click,
-   alternative → comparison,
-   product → shelf.

------------------------------------------------------------------------

# 64. Technical Architecture

Recommended initial architecture:

``` text
                    BROWSER
                       |
                       v
                NEXT.JS FRONTEND
                       |
                       v
                APPLICATION API
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
   PostgreSQL        Redis        Object Storage
        |
        v
   Domain Services
        |
  +-----+------+-------+-------+
  |            |       |       |
  v            v       v       v
Products   Ingredients Evidence Compatibility
  |            |       |       |
  +------------+-------+-------+
                       |
                       v
                 Recommendation
                       |
          +------------+------------+
          |                         |
          v                         v
     Skin Analysis             Alternatives
          |
          v
       ML/OCR
```

Start as a **modular monolith**, not microservices.

------------------------------------------------------------------------

# 65. Frontend Stack

Recommended:

-   Next.js
-   React
-   TypeScript
-   Tailwind CSS
-   accessible component primitives
-   React Hook Form or equivalent
-   Zod or equivalent validation
-   TanStack Query where client-side server-state management is useful

Vercel provides native deployment support for Next.js, including
framework-aware deployment and caching capabilities. citeturn1search6

------------------------------------------------------------------------

# 66. Backend Stack

Recommended:

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy or equivalent ORM
-   PostgreSQL
-   Redis
-   background worker
-   object storage

FastAPI supports background tasks and explicitly recommends larger task
systems such as Celery-style worker architectures when heavy processing
should run independently of the application process. citeturn1search0

------------------------------------------------------------------------

# 67. Database

Recommended:

-   PostgreSQL

Supabase provides full PostgreSQL databases plus Auth and Storage
integrations, making it a reasonable implementation option for this
project. citeturn1search1turn1search3

------------------------------------------------------------------------

# 68. Authentication

Options:

-   Supabase Auth,
-   Auth.js,
-   another managed authentication service.

If using Supabase:

``` text
Browser
  ↓
Supabase Auth
  ↓
JWT/session
  ↓
Backend
  ↓
Postgres / RLS
```

Supabase Auth uses JWT-based authentication and integrates with
Postgres; access controls should be enforced carefully at the
database/application boundaries. citeturn1search3

------------------------------------------------------------------------

# 69. Storage

Separate storage from relational data.

Buckets:

``` text
skin-images-private
product-images
ocr-inputs-private
share-assets
```

Private user images should not be publicly accessible by default.

Supabase Storage supports buckets, access policies and integration with
Postgres authorization mechanisms. citeturn1search4turn1search5

------------------------------------------------------------------------

# 70. Domain Modules

Backend:

``` text
app/
├── auth/
├── users/
├── products/
├── ingredients/
├── evidence/
├── compatibility/
├── skin_analysis/
├── recommendations/
├── alternatives/
├── routines/
├── shelf/
├── search/
├── scans/
├── ocr/
├── pricing/
├── sharing/
├── analytics/
├── admin/
└── common/
```

Each module should own its domain logic.

------------------------------------------------------------------------

# 71. Separation of Concerns

Frontend:

``` text
UI
 ↓
API client
 ↓
DTO
```

Backend:

``` text
Route
 ↓
Application service
 ↓
Domain service
 ↓
Repository
 ↓
Database
```

AI:

``` text
AI adapter
 ↓
structured output
 ↓
validation
 ↓
domain logic
```

------------------------------------------------------------------------

# 72. Coupling and Cohesion

High cohesion:

``` text
compatibility/
```

should contain compatibility logic rather than spreading rules across UI
components.

Low coupling:

``` text
skin_analysis
```

should produce structured observations rather than directly writing
recommendation UI state.

------------------------------------------------------------------------

# 73. API Design

Base:

``` text
/api/v1
```

Products:

``` text
GET    /products
GET    /products/{id}
POST   /products/identify
POST   /products/scan
```

Ingredients:

``` text
GET /ingredients
GET /ingredients/{id}
```

Compatibility:

``` text
POST /comparisons
GET  /comparisons/{id}
```

Skin:

``` text
POST   /skin-analysis
POST   /skin-analysis/{id}/image
GET    /skin-analysis/{id}
GET    /skin-analysis/{id}/recommendations
DELETE /skin-analysis/{id}
```

Alternatives:

``` text
POST /alternatives/search
GET  /alternatives/{id}
```

Routine:

``` text
POST /routines
GET  /routines
POST /routines/{id}/analyze
```

Shelf:

``` text
GET    /shelf
POST   /shelf
DELETE /shelf/{productId}
```

------------------------------------------------------------------------

# 74. API Error Contract

All APIs should return predictable errors.

``` json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "We could not identify this product.",
    "request_id": "..."
  }
}
```

Common codes:

``` text
INVALID_INPUT
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
PRODUCT_NOT_FOUND
AMBIGUOUS_PRODUCT
OCR_LOW_CONFIDENCE
IMAGE_QUALITY_LOW
ANALYSIS_UNAVAILABLE
RATE_LIMITED
INTERNAL_ERROR
```

------------------------------------------------------------------------

# 75. Asynchronous Jobs

Use asynchronous processing for:

-   skin image analysis,
-   OCR,
-   product-image identification,
-   large alternative searches,
-   data ingestion,
-   bulk normalization.

Flow:

``` text
POST
 ↓
202 Accepted
 ↓
job_id
 ↓
worker
 ↓
status updates
 ↓
result
```

------------------------------------------------------------------------

# 76. Job State Machine

``` text
queued
  ↓
processing
  ↓
completed

queued
  ↓
processing
  ↓
failed

processing
  ↓
cancelled
```

Store:

``` text
job_id
type
status
created_at
started_at
completed_at
error_code
retry_count
```

------------------------------------------------------------------------

# 77. AI / ML Architecture

SkinIQ has several AI-adjacent systems.

### 1. Skin analysis

Computer vision model.

### 2. Product OCR

OCR service.

### 3. Product identification

Image/text matching.

### 4. Optional LLM explanation

Converts structured results into friendly explanations.

The LLM should not be the source of scientific truth.

------------------------------------------------------------------------

# 78. Skin Analysis Model Interface

Abstract model behind an adapter:

``` python
class SkinAnalysisModel:
    def analyze(self, image) -> SkinAnalysisOutput:
        ...
```

Output:

``` python
SkinAnalysisOutput(
    observations=[
        SkinObservation(
            concern="visible_pores",
            confidence=0.86,
            severity="moderate"
        )
    ],
    model_version="..."
)
```

This allows changing models without rewriting the application.

------------------------------------------------------------------------

# 79. Model Evaluation

Create a labeled validation dataset.

Metrics should be tracked separately for each concern:

-   precision,
-   recall,
-   F1,
-   calibration,
-   false-positive rate.

Also evaluate across:

-   lighting conditions,
-   skin tones,
-   camera quality,
-   age ranges,
-   image angles.

Do not launch a skin-analysis feature based only on an impressive demo.

------------------------------------------------------------------------

# 80. Bias and Fairness

Skin analysis must be tested for performance variation across diverse
skin appearances.

The product should not claim equal performance without measuring it.

Low-confidence results should be shown as low confidence.

------------------------------------------------------------------------

# 81. Product Image Identification

Pipeline:

``` text
Image
 ↓
OCR
 ↓
Visual embedding / image features
 ↓
Candidate retrieval
 ↓
Text similarity
 ↓
Brand/product match
 ↓
Candidate ranking
 ↓
User confirmation
```

Never silently choose a low-confidence product.

------------------------------------------------------------------------

# 82. LLM Usage

Good uses:

-   explaining structured results,
-   simplifying technical ingredient descriptions,
-   generating user-friendly summaries,
-   answering questions using retrieved evidence.

Bad use:

``` text
User: Can I combine X and Y?
LLM: Yes, probably.
```

Better:

``` text
Compatibility engine
→ structured finding
→ evidence
→ LLM explanation
```

------------------------------------------------------------------------

# 83. RAG Architecture

If an LLM is used:

``` text
User question
      ↓
Intent extraction
      ↓
Structured database lookup
      ↓
Evidence retrieval
      ↓
Compatibility/recommendation engine
      ↓
Structured answer
      ↓
LLM explanation
```

Never allow arbitrary model memory to override the database result.

------------------------------------------------------------------------

# 84. Caching

Cache:

-   product pages,
-   ingredient pages,
-   static SEO pages,
-   common product searches,
-   public comparisons,
-   immutable evidence records.

Do not cache private user data without correct isolation.

------------------------------------------------------------------------

# 85. Security

Security layers:

``` text
Browser validation
      ↓
API validation
      ↓
Authentication
      ↓
Authorization
      ↓
Database permissions
      ↓
Storage permissions
```

------------------------------------------------------------------------

# 86. File Upload Security

Required:

-   allowlisted extensions,
-   MIME validation,
-   file-signature validation,
-   size limits,
-   generated filenames,
-   private storage,
-   access authorization,
-   image decoding safeguards,
-   malware scanning where practical,
-   rate limiting.

OWASP explicitly recommends these layered controls for file uploads.
citeturn1search2

------------------------------------------------------------------------

# 87. Privacy

Skin images should be treated as sensitive user content.

Controls:

-   clear consent,
-   minimal retention,
-   deletion,
-   private storage,
-   access logging,
-   no unnecessary sharing,
-   no training use without appropriate consent.

------------------------------------------------------------------------

# 88. Data Deletion

When user deletes an analysis:

``` text
Analysis record
↓
Observation records
↓
Recommendation records
↓
Image/object storage
↓
Derived temporary artifacts
```

Deletion must be comprehensive.

------------------------------------------------------------------------

# 89. Rate Limiting

Protect:

``` text
POST /skin-analysis
POST /products/scan
POST /alternatives/search
POST /comparisons
```

Rate-limit by:

-   IP,
-   account,
-   endpoint,
-   anonymous session.

Expensive operations require stricter limits.

------------------------------------------------------------------------

# 90. Accessibility

Follow accessible design principles:

-   keyboard navigation,
-   semantic HTML,
-   visible focus,
-   adequate contrast,
-   labels for inputs,
-   screen-reader support,
-   alt text,
-   reduced-motion support,
-   error messages that explain how to recover.

------------------------------------------------------------------------

# 91. Responsive Design

Breakpoints should support:

-   mobile,
-   tablet,
-   desktop.

Mobile is especially important because:

-   users take skin photos on phones,
-   product scans occur on phones,
-   social links open on phones.

------------------------------------------------------------------------

# 92. UI Design Direction

Visual identity:

-   clean,
-   clinical but not sterile,
-   premium,
-   soft,
-   trustworthy,
-   modern.

Avoid:

-   excessive pink,
-   pseudo-medical claims,
-   fake scientific dashboards,
-   overwhelming gradients,
-   giant meaningless scores.

------------------------------------------------------------------------

# 93. Design Tokens

Example:

``` text
Background
Surface
Surface-muted
Text-primary
Text-secondary
Border
Accent
Success
Warning
Danger
Info
```

Typography:

``` text
Display
Heading
Body
Caption
Mono
```

Spacing:

``` text
4
8
12
16
24
32
48
64
```

------------------------------------------------------------------------

# 94. Core Components

``` text
ProductCard
ProductSelector
ProductSearch
IngredientChip
IngredientTable
CompatibilityBanner
EvidenceCard
ConfidenceBadge
AlternativeCard
PriceBadge
SkinObservationCard
RecommendationCard
RoutineStep
ShelfCard
UploadDropzone
CameraScanner
OCRReview
LoadingState
EmptyState
ErrorState
```

------------------------------------------------------------------------

# 95. Loading States

Never show a blank screen.

Skin analysis:

``` text
Uploading image...
Checking image quality...
Analyzing visible features...
Preparing recommendations...
```

Alternatives:

``` text
Identifying product...
Finding similar products...
Comparing ingredient profiles...
Checking price observations...
Ranking alternatives...
```

------------------------------------------------------------------------

# 96. Failure States

Every major workflow needs:

``` text
Loading
Success
Empty
Partial
Error
Retry
```

Examples:

> We couldn't identify this product confidently.

Actions:

``` text
[Try another image]
[Enter product name]
[Enter ingredients manually]
```

------------------------------------------------------------------------

# 97. Database Schema

Core tables:

``` text
users
profiles
products
product_versions
product_identifiers
product_sources
product_images
ingredients
ingredient_aliases
product_ingredients
evidence_records
interaction_rules
skin_analyses
skin_observations
recommendations
alternative_searches
product_alternatives
price_observations
routines
routine_items
shelf_items
comparisons
comparison_findings
uploads
ocr_results
jobs
shares
analytics_events
admin_reviews
knowledge_versions
```

------------------------------------------------------------------------

# 98. Key Relationships

``` text
Product 1 ─── N ProductVersion

ProductVersion N ─── N Ingredient

Ingredient N ─── N Ingredient

SkinAnalysis 1 ─── N SkinObservation

SkinAnalysis 1 ─── N Recommendation

Product 1 ─── N PriceObservation

AlternativeSearch 1 ─── N ProductAlternative

User 1 ─── N Routine

Routine 1 ─── N RoutineItem

User 1 ─── N ShelfItem
```

------------------------------------------------------------------------

# 99. Product Ingredient Table

``` text
product_ingredients
--------------------
product_version_id
ingredient_id
raw_name
position
normalized_confidence
source_id
```

Preserve ingredient order because ingredient-list position can matter
for interpretation.

------------------------------------------------------------------------

# 100. Knowledge Versioning

Compatibility and recommendation rules should be versioned.

``` text
knowledge_version
-----------------
id
name
created_at
published_at
status
```

Every result stores:

``` text
knowledge_version
```

This makes results reproducible.

------------------------------------------------------------------------

# 101. Compatibility Result Versioning

Store:

``` text
comparison_id
product_version_a
product_version_b
knowledge_version
engine_version
created_at
result
```

If the knowledge base changes, the same pair can produce a newly
versioned result.

------------------------------------------------------------------------

# 102. Data Quality Dashboard

Admin should see:

``` text
Products
- total
- verified
- stale
- incomplete

Ingredients
- total
- normalized
- unresolved

OCR
- low confidence rate

Skin analysis
- success rate
- failure rate

Compatibility
- rules reviewed
- rules pending
```

------------------------------------------------------------------------

# 103. Admin Workflow

``` text
New data
   ↓
Automated validation
   ↓
Quality flags
   ↓
Human review
   ↓
Publish
   ↓
Version
```

Admin roles:

-   data reviewer,
-   knowledge reviewer,
-   system admin.

------------------------------------------------------------------------

# 104. Data Quality Rules

Flag:

-   missing ingredient list,
-   contradictory product data,
-   unknown ingredient,
-   duplicate product,
-   stale price,
-   unsupported claim,
-   low OCR confidence,
-   missing evidence,
-   incomplete source metadata.

------------------------------------------------------------------------

# 105. Testing Strategy

The project must demonstrate:

-   unit testing,
-   integration testing,
-   system testing,
-   black-box testing,
-   white-box testing,
-   end-to-end testing,
-   regression testing.

This directly supports the software-engineering testing requirements of
the course.

------------------------------------------------------------------------

# 106. Unit Tests

Examples:

``` text
normalize_ingredient()
resolve_alias()
compare_ingredients()
evaluate_interaction()
rank_alternatives()
calculate_similarity()
validate_upload()
map_concern_to_category()
```

------------------------------------------------------------------------

# 107. Compatibility Test Cases

Example:

  Test   Input                Expected
  ------ -------------------- -------------------------
  C01    identical product    duplication identified
  C02    known interaction    caution
  C03    no relevant rule     no notable interaction
  C04    missing ingredient   insufficient data
  C05    unknown ingredient   unresolved
  C06    old formulation      version-specific result
  C07    malformed product    validation error

------------------------------------------------------------------------

# 108. Skin Analysis Tests

Test:

-   valid image,
-   invalid file,
-   poor lighting,
-   blurry image,
-   unsupported image,
-   low-confidence observation,
-   multiple observations,
-   no observation,
-   model timeout,
-   model failure,
-   deletion.

------------------------------------------------------------------------

# 109. Alternative Tests

Test:

-   exact product,
-   ambiguous product,
-   no match,
-   cheaper alternatives,
-   no cheaper alternatives,
-   missing price,
-   stale price,
-   duplicate candidates,
-   low ingredient confidence,
-   ranking stability.

------------------------------------------------------------------------

# 110. OCR Tests

Test:

-   clear ingredient list,
-   curved packaging,
-   low light,
-   blurry text,
-   multiple columns,
-   punctuation,
-   misspelled OCR,
-   unknown ingredient,
-   duplicate ingredient,
-   manual correction.

------------------------------------------------------------------------

# 111. Integration Testing

Examples:

``` text
Product → ingredient normalization
Product → compatibility
Skin analysis → recommendation
Recommendation → product retrieval
Product → alternatives
Alternative → compatibility
Shelf → routine
Routine → compatibility
```

------------------------------------------------------------------------

# 112. End-to-End Test

### Scenario A

``` text
Open homepage
→ Analyze Skin
→ select combination
→ upload image
→ receive observations
→ open recommendation
→ view product
→ find alternatives
→ compare alternative
```

### Scenario B

``` text
Open homepage
→ Compare
→ search Product A
→ search Product B
→ compare
→ inspect evidence
→ save
→ sign in
→ result persists
```

------------------------------------------------------------------------

# 113. Black-Box Testing

Test based on user-visible behavior.

Example:

``` text
Input:
Product A + Product B

Expected:
Result page with status, explanation and evidence.
```

No knowledge of internal implementation is required.

------------------------------------------------------------------------

# 114. White-Box Testing

Test internal branches.

Example:

``` python
if ingredient_a and ingredient_b:
    evaluate_rule()
elif unresolved:
    return insufficient_data
else:
    return no_notable_interaction
```

All branches should be covered.

------------------------------------------------------------------------

# 115. TDD

For critical domain logic:

``` text
Write test
↓
Implement minimal behavior
↓
Run test
↓
Refactor
```

Especially:

-   compatibility rules,
-   normalization,
-   alternative ranking,
-   recommendation mapping.

------------------------------------------------------------------------

# 116. Debugging

Every backend request should have:

``` text
request_id
user/session ID where permitted
endpoint
duration
status
error code
```

Never log:

-   passwords,
-   auth tokens,
-   private skin images,
-   unnecessary personal data.

------------------------------------------------------------------------

# 117. Observability

Track:

``` text
API latency
database latency
OCR latency
ML latency
job failure rate
queue depth
cache hit rate
error rate
upload failure rate
```

------------------------------------------------------------------------

# 118. Performance Targets

Initial product targets:

``` text
Static page load: fast
Product search: < 1–2 seconds target
Compatibility from cached product data: < 2 seconds target
OCR: asynchronous
Skin analysis: asynchronous
Alternative search: < 3 seconds target where data is available
```

Targets are engineering goals, not guarantees.

------------------------------------------------------------------------

# 119. Scalability

Initial:

``` text
Modular monolith
+
PostgreSQL
+
Redis
+
worker
```

Scale later:

``` text
API replicas
worker replicas
database read replicas
dedicated search
object storage CDN
ML inference service
```

Do not introduce microservices until actual scaling or team boundaries
justify them.

------------------------------------------------------------------------

# 120. CI/CD

Pipeline:

``` text
Git push
 ↓
Lint
 ↓
Type check
 ↓
Unit tests
 ↓
Integration tests
 ↓
Build
 ↓
Security checks
 ↓
Deploy staging
 ↓
Smoke tests
 ↓
Production
```

------------------------------------------------------------------------

# 121. Environment Separation

``` text
development
staging
production
```

Separate:

-   databases,
-   storage buckets,
-   API keys,
-   auth configuration,
-   analytics projects.

Never use production secrets locally.

------------------------------------------------------------------------

# 122. Repository Structure

``` text
skiniq/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── types/
│   ├── ui/
│   └── config/
├── workers/
│   ├── ocr/
│   ├── skin_analysis/
│   └── ingestion/
├── database/
│   ├── migrations/
│   └── seeds/
├── docs/
│   ├── requirements/
│   ├── architecture/
│   ├── uml/
│   └── testing/
└── README.md
```

------------------------------------------------------------------------

# 123. Software Engineering Deliverables

For the UCS503 project, produce:

``` text
1. Problem statement
2. Stakeholder analysis
3. Functional requirements
4. Non-functional requirements
5. SRS
6. Use-case diagram
7. Use-case descriptions
8. DFD Level 0
9. DFD Level 1
10. Data dictionary
11. ER diagram
12. Class diagram
13. Sequence diagrams
14. Activity diagrams
15. State diagrams
16. Component diagram
17. Deployment diagram
18. UI wireframes
19. Architecture document
20. Database design
21. Test plan
22. Test cases
23. Traceability matrix
24. Agile backlog
25. Sprint plan
26. Risk register
27. Final implementation
```

The UCS503 syllabus specifically covers requirements engineering,
DFD/data dictionary, ER/UML modeling, architectural/component design,
MVC/client-server concepts, testing/V&V, Agile/Scrum artifacts and
software project management. SkinIQ should deliberately produce these
artifacts rather than treating them as separate paperwork.
fileciteturn1file0

------------------------------------------------------------------------

# 124. Requirements Engineering

## Functional requirements

### FR-01

The system shall allow users to search products.

### FR-02

The system shall allow users to compare two products.

### FR-03

The system shall normalize product ingredients.

### FR-04

The system shall generate compatibility findings from structured rules.

### FR-05

The system shall explain compatibility findings.

### FR-06

The system shall allow users to upload skin images.

### FR-07

The system shall validate skin images.

### FR-08

The system shall generate supported visual skin observations.

### FR-09

The system shall attach confidence to observations.

### FR-10

The system shall map observations to recommendation categories.

### FR-11

The system shall recommend relevant products.

### FR-12

The system shall accept product images.

### FR-13

The system shall identify products from supported inputs.

### FR-14

The system shall find product alternatives.

### FR-15

The system shall support cheaper/similar/premium alternatives.

### FR-16

The system shall support routine-compatible alternatives.

### FR-17

The system shall allow products to be saved.

### FR-18

The system shall allow routines to be created.

### FR-19

The system shall support public sharing where appropriate.

### FR-20

The system shall support account deletion.

------------------------------------------------------------------------

# 125. Non-Functional Requirements

### Performance

-   responsive UI,
-   asynchronous expensive processing,
-   caching,
-   optimized images.

### Security

-   authentication,
-   authorization,
-   upload protection,
-   secret management.

### Availability

-   graceful degradation,
-   retries,
-   fallback states.

### Maintainability

-   modular architecture,
-   typed interfaces,
-   tests,
-   documentation.

### Scalability

-   stateless API,
-   worker architecture,
-   database indexing,
-   caching.

### Usability

-   clear workflows,
-   minimal friction,
-   understandable explanations.

### Accessibility

-   keyboard access,
-   semantic markup,
-   screen-reader compatibility.

------------------------------------------------------------------------

# 126. Use Case Model

Actors:

``` text
Guest User
Registered User
Admin
External OCR Service
Skin Analysis Model
Product Data Source
Price Data Source
```

Major use cases:

``` text
UC01 Analyze Skin
UC02 Compare Products
UC03 Find Alternatives
UC04 Search Product
UC05 Scan Product
UC06 Inspect Ingredient
UC07 Build Routine
UC08 Manage Shelf
UC09 Save Result
UC10 Share Result
UC11 Review Data
UC12 Publish Knowledge
```

------------------------------------------------------------------------

# 127. DFD Level 0

``` text
                 USER
                   |
                   v
             +-----------+
             |  SKINIQ   |
             +-----------+
              /    |    \
             /     |     \
            v      v      v
       Product   Skin   User Data
        Data    Images
```

External entities:

``` text
User
Product Data Provider
OCR Provider
ML Model
Price Provider
Admin
```

------------------------------------------------------------------------

# 128. DFD Level 1

``` text
User
 |
 +--> Product Search
 |
 +--> Skin Analysis
 |       |
 |       +--> Image Storage
 |       +--> ML
 |       +--> Recommendation
 |
 +--> Compatibility
 |       |
 |       +--> Product DB
 |       +--> Ingredient DB
 |       +--> Evidence DB
 |
 +--> Alternatives
         |
         +--> Product DB
         +--> Price DB
         +--> Similarity Engine
```

------------------------------------------------------------------------

# 129. ER Diagram --- Conceptual

``` text
USER
 |
 +----< SHELF_ITEM >---- PRODUCT
 |
 +----< ROUTINE >----< ROUTINE_ITEM >---- PRODUCT
 |
 +----< SKIN_ANALYSIS >----< SKIN_OBSERVATION
 |                              |
 |                              +----< RECOMMENDATION >---- PRODUCT
 |
 +----< COMPARISON >---- PRODUCT
 |
 +----< ALTERNATIVE_SEARCH >----< PRODUCT_ALTERNATIVE >---- PRODUCT

PRODUCT
 |
 +----< PRODUCT_VERSION
             |
             +----< PRODUCT_INGREDIENT >---- INGREDIENT
                                               |
                                               +----< EVIDENCE
```

------------------------------------------------------------------------

# 130. Sequence --- Product Comparison

``` text
User
 ↓
Frontend
 ↓
API
 ↓
Product Service
 ↓
Ingredient Service
 ↓
Compatibility Engine
 ↓
Evidence Service
 ↓
API
 ↓
Frontend
 ↓
User
```

------------------------------------------------------------------------

# 131. Sequence --- Skin Analysis

``` text
User
 ↓
Frontend
 ↓
Upload API
 ↓
Storage
 ↓
Job Queue
 ↓
Skin Analysis Worker
 ↓
Model
 ↓
Observation Service
 ↓
Recommendation Service
 ↓
Product Service
 ↓
Result
 ↓
Frontend
```

------------------------------------------------------------------------

# 132. Sequence --- Alternatives

``` text
User
 ↓
Product identification
 ↓
Canonical product
 ↓
Feature extraction
 ↓
Candidate retrieval
 ↓
Filtering
 ↓
Similarity ranking
 ↓
Price enrichment
 ↓
Alternative results
```

------------------------------------------------------------------------

# 133. State Model --- Skin Analysis

``` text
CREATED
  ↓
IMAGE_UPLOADED
  ↓
VALIDATING
  ↓
QUALITY_CHECK
  |
  +--> REJECTED
  |
  v
QUEUED
  ↓
ANALYZING
  ↓
OBSERVATIONS_READY
  ↓
RECOMMENDATIONS_READY
  ↓
COMPLETED
```

------------------------------------------------------------------------

# 134. Component Diagram

``` text
Next.js Web
    |
    v
API Gateway
    |
    +-- Auth
    +-- Product Service
    +-- Ingredient Service
    +-- Compatibility Service
    +-- Skin Analysis Service
    +-- Recommendation Service
    +-- Alternative Service
    +-- Routine Service
    +-- Shelf Service
    +-- Search Service
    |
    +-- PostgreSQL
    +-- Redis
    +-- Object Storage
    +-- Worker
            |
            +-- OCR
            +-- ML
            +-- Ingestion
```

------------------------------------------------------------------------

# 135. Deployment Architecture

Recommended initial deployment:

``` text
                    INTERNET
                       |
                       v
                 CDN / EDGE
                       |
                       v
                Next.js / Vercel
                       |
                       v
                  API service
                       |
             +---------+---------+
             |         |         |
             v         v         v
         Postgres   Redis    Storage
             |
             v
          Worker
          /   \
        OCR   ML
```

Vercel's current Next.js platform supports framework-aware deployment
and caching capabilities; Supabase provides integrated Postgres, Auth
and Storage options. citeturn1search6turn1search1turn1search12

------------------------------------------------------------------------

# 136. Caching Architecture

Cache keys:

``` text
product:{id}
product:{id}:alternatives
ingredient:{id}
comparison:{productA}:{productB}:{knowledgeVersion}
search:{normalizedQuery}
```

Invalidate when:

-   product version changes,
-   evidence changes,
-   knowledge version changes,
-   price observation expires.

------------------------------------------------------------------------

# 137. Search Architecture

Initial:

-   PostgreSQL full-text search,
-   trigram matching,
-   indexed aliases.

Later:

-   dedicated search engine.

Search normalization:

``` text
lowercase
remove punctuation
normalize whitespace
alias mapping
brand normalization
```

------------------------------------------------------------------------

# 138. Recommendation Engine Architecture

``` text
Skin Observation
       ↓
Concern Mapper
       ↓
Ingredient Category Resolver
       ↓
Evidence Filter
       ↓
Product Candidate Retrieval
       ↓
Personal Preference Filter
       ↓
Routine Compatibility Filter
       ↓
Ranking
       ↓
Recommendation
```

------------------------------------------------------------------------

# 139. Alternatives Engine Architecture

``` text
Reference Product
      ↓
Feature Extractor
      ↓
Candidate Retriever
      ↓
Hard Filters
      ↓
Similarity
      ↓
Price
      ↓
Preference Fit
      ↓
Ranking
      ↓
Explanation
```

------------------------------------------------------------------------

# 140. Hard vs Soft Ranking Rules

Hard filters:

-   wrong product category,
-   unavailable required data,
-   user explicitly excludes,
-   duplicate reference product.

Soft ranking:

-   ingredient similarity,
-   price,
-   target match,
-   routine fit,
-   brand preference.

This prevents the ranking system from hiding important alternatives.

------------------------------------------------------------------------

# 141. Personal Preference Model

Optional preferences:

``` text
budget
preferred brands
avoided brands
texture
fragrance preference
vegan preference where reliable data exists
ingredient preferences
product category
routine complexity
```

Do not infer sensitive attributes.

------------------------------------------------------------------------

# 142. Budget Filtering

Allow:

``` text
Any price
Under ₹500
₹500–₹1,000
₹1,000–₹2,000
₹2,000+
Custom
```

Currency should adapt to locale where possible.

------------------------------------------------------------------------

# 143. Alternative Explanation

Every result should answer:

``` text
Why is this here?
Why is it cheaper?
Why is it similar?
What is different?
What data is missing?
```

This builds trust.

------------------------------------------------------------------------

# 144. No Magic Safety Score

Do not display:

``` text
87/100 SAFE
```

unless there is a defensible, documented methodology.

Instead display:

``` text
Compatibility:
Potential caution

Confidence:
Moderate

Evidence:
Moderate

Data:
Complete
```

------------------------------------------------------------------------

# 145. No False Certainty

Avoid:

> "This product is safe for you."

Prefer:

> "No notable interaction was identified in the current knowledge base."

Avoid:

> "This will remove pigmentation."

Prefer:

> "This ingredient category is commonly used to target the appearance of
> uneven pigmentation."

------------------------------------------------------------------------

# 146. Medical Boundary

SkinIQ is a cosmetic decision-support product.

It should not:

-   diagnose acne,
-   diagnose rosacea,
-   diagnose melasma,
-   diagnose eczema,
-   prescribe medication,
-   guarantee treatment,
-   replace professional evaluation.

If the user describes concerning symptoms, encourage appropriate
professional evaluation.

------------------------------------------------------------------------

# 147. Product Quality Loop

``` text
USER USE
 ↓
ANALYTICS
 ↓
ERRORS / LOW CONFIDENCE
 ↓
ADMIN REVIEW
 ↓
DATA IMPROVEMENT
 ↓
KNOWLEDGE UPDATE
 ↓
BETTER RESULTS
```

------------------------------------------------------------------------

# 148. Product Feedback

After useful workflows:

``` text
Was this result useful?

[Yes]
[Not really]
```

Optional:

``` text
What was missing?
```

Feedback should be analyzed without turning it into scientific evidence.

------------------------------------------------------------------------

# 149. Risk Register

  Risk                         Impact   Probability Mitigation
  -------------------------- -------- ------------- -------------------------
  Poor skin model accuracy       High        Medium validation + confidence
  Incorrect OCR                  High          High review UI
  Stale product data             High        Medium provenance/versioning
  Bad compatibility rule         High        Medium expert review + tests
  Price unavailable            Medium          High show unavailable
  Product ambiguity            Medium          High confirmation
  Privacy issue                  High    Low/Medium private storage
  LLM hallucination              High        Medium structured grounding
  SEO thin pages               Medium        Medium quality threshold
  Scaling cost                 Medium        Medium caching/async
  Scope explosion                High          High phased roadmap

------------------------------------------------------------------------

# 150. MVP Scope

The MVP should **not** attempt everything at once.

## MVP 1

``` text
Product search
Product database
Ingredient normalization
Two-product comparison
Compatibility engine
Evidence display
```

## MVP 2

``` text
Product scanner
OCR
Manual ingredient correction
```

## MVP 3

``` text
Skin analysis
Concern detection
Recommendation mapping
```

## MVP 4

``` text
Alternative engine
Price observations
Similarity ranking
```

## MVP 5

``` text
Routine
Shelf
Sharing
SEO expansion
```

------------------------------------------------------------------------

# 151. Recommended Development Order

### Sprint 0 --- Architecture

-   repository,
-   environments,
-   database,
-   auth,
-   UI system,
-   CI/CD.

### Sprint 1 --- Products

-   product schema,
-   ingredient schema,
-   search,
-   product pages.

### Sprint 2 --- Compatibility

-   rules,
-   comparison API,
-   result UI,
-   evidence.

### Sprint 3 --- Scanner

-   upload,
-   OCR,
-   normalization,
-   review.

### Sprint 4 --- Skin Analysis

-   upload,
-   quality,
-   model adapter,
-   observation UI.

### Sprint 5 --- Recommendations

-   concern mapping,
-   product retrieval,
-   personalized recommendations.

### Sprint 6 --- Alternatives

-   identification,
-   similarity,
-   pricing,
-   ranking.

### Sprint 7 --- Routine/Shelf

-   saved products,
-   routine,
-   analysis.

### Sprint 8 --- Growth

-   SEO,
-   share,
-   analytics,
-   public pages.

### Sprint 9 --- Hardening

-   security,
-   testing,
-   accessibility,
-   performance.

------------------------------------------------------------------------

# 152. Agile Backlog

## Epic 1 --- Product Data

``` text
US-001 Search products
US-002 View product
US-003 Normalize ingredients
US-004 Track product versions
US-005 Track provenance
```

## Epic 2 --- Compatibility

``` text
US-010 Select two products
US-011 Compare ingredients
US-012 Evaluate interactions
US-013 Show evidence
US-014 Explain result
```

## Epic 3 --- Skin Analysis

``` text
US-020 Upload skin image
US-021 Validate image
US-022 Analyze image
US-023 Show observations
US-024 Recommend ingredient categories
US-025 Recommend products
```

## Epic 4 --- Alternatives

``` text
US-030 Identify product
US-031 Find similar products
US-032 Find cheaper products
US-033 Find premium alternatives
US-034 Compare alternatives
```

## Epic 5 --- Retention

``` text
US-040 Save product
US-041 Build shelf
US-042 Build routine
US-043 Analyze routine
US-044 View history
```

------------------------------------------------------------------------

# 153. Example User Story

> **As a skincare user, I want to compare two products so that I can
> understand whether there are relevant ingredient interactions before
> adding both to my routine.**

Acceptance criteria:

``` text
Given two identified products
When the user clicks Compare
Then SkinIQ resolves their formulations
And evaluates relevant interaction rules
And displays a result
And displays why
And displays evidence/confidence
And identifies unresolved data
```

------------------------------------------------------------------------

# 154. Story Card --- Skin Analysis

``` text
Title:
Analyze visible skin concerns

As a user,
I want to upload a skin image,
so that I can see supported cosmetic observations.

Acceptance:
- image uploads successfully
- invalid images are rejected
- quality is checked
- observations have confidence
- limitations are shown
- no diagnosis is claimed
```

------------------------------------------------------------------------

# 155. Story Card --- Alternatives

``` text
Title:
Find product alternatives

As a user,
I want to upload or search for a product,
so that I can discover cheaper, similar and other alternatives.

Acceptance:
- product is identified
- ambiguous matches require confirmation
- alternatives are ranked
- ranking reasons are visible
- price timestamps are shown
- unavailable prices are not invented
```

------------------------------------------------------------------------

# 156. Technical Spikes

Before implementing expensive features:

``` text
SP-01 Skin model feasibility
SP-02 Skin model accuracy
SP-03 OCR accuracy
SP-04 Product image identification
SP-05 Product data licensing
SP-06 Price data availability
SP-07 Alternative similarity methodology
SP-08 Evidence source methodology
```

Each spike should produce a short decision record.

------------------------------------------------------------------------

# 157. Cost Model

Major cost categories:

``` text
Hosting
Database
Storage
OCR
ML inference
LLM usage
Monitoring
Email/auth
Third-party data
```

Do not hard-code provider pricing in the product specification because
pricing changes.

Measure cost per:

``` text
skin analysis
OCR scan
alternative search
comparison
monthly active user
```

------------------------------------------------------------------------

# 158. Cost Optimization

Use:

-   cached product data,
-   asynchronous jobs,
-   image compression,
-   model batching,
-   smaller models where adequate,
-   result reuse,
-   rate limits,
-   CDN,
-   database indexes.

------------------------------------------------------------------------

# 159. Product Analytics Architecture

``` text
Frontend event
 ↓
Analytics API
 ↓
Event validation
 ↓
Event store
 ↓
Dashboard
```

Events should include:

``` text
event_name
timestamp
anonymous/session ID
user ID if available
route
metadata
```

Do not collect unnecessary sensitive information.

------------------------------------------------------------------------

# 160. Product Funnel

Primary funnel:

``` text
Visitor
 ↓
Workflow started
 ↓
Input completed
 ↓
Result received
 ↓
Product clicked
 ↓
Save / compare / routine
 ↓
Signup
 ↓
Return
```

Measure drop-off at every step.

------------------------------------------------------------------------

# 161. SEO Indexing Rules

Index:

-   useful product pages,
-   useful ingredient pages,
-   high-quality alternatives pages,
-   high-value comparison pages,
-   guides.

Noindex:

-   empty searches,
-   low-quality filter combinations,
-   private dashboards,
-   temporary job pages,
-   personalized private analyses.

Next.js documentation distinguishes directives such as `noindex` and
discusses robots/canonical behavior for controlling indexability.
citeturn0search3

------------------------------------------------------------------------

# 162. Accessibility of Results

Compatibility status should not rely only on color.

Example:

``` text
⚠ Potential caution
```

rather than:

``` text
[yellow box]
```

Confidence should have text labels.

------------------------------------------------------------------------

# 163. Internationalization

Architecture should be i18n-ready.

Do not hard-code user-visible strings throughout components.

Potential future languages:

-   English,
-   Hindi,
-   other high-demand markets.

Ingredient names should preserve canonical INCI values even when UI
language changes.

------------------------------------------------------------------------

# 164. Localization

Support:

-   currency,
-   date,
-   language,
-   product availability,
-   regional formulations.

A product in India may differ from the same product in another market.

Therefore product market should be part of product identity where
necessary.

------------------------------------------------------------------------

# 165. Observability Dashboard

Engineering dashboard:

``` text
Requests/min
p95 latency
error rate
worker queue
OCR failures
skin-analysis failures
DB CPU
DB connections
storage usage
cache hit rate
```

Product dashboard:

``` text
comparisons
skin analyses
alternative searches
recommendation clicks
saves
routines
signups
retention
```

------------------------------------------------------------------------

# 166. Admin Knowledge Base UI

Admin can:

``` text
Search ingredient
Search rule
Create rule
Edit rule
Attach evidence
Set evidence strength
Review
Publish
Version
Rollback
```

No rule should silently change production results without traceability.

------------------------------------------------------------------------

# 167. Audit Log

Track:

``` text
who changed
what changed
old value
new value
reason
timestamp
knowledge version
```

------------------------------------------------------------------------

# 168. Backup and Recovery

Back up:

-   database,
-   configuration,
-   knowledge base,
-   uploaded user data according to retention policy.

Test restoration rather than assuming backups work.

------------------------------------------------------------------------

# 169. Disaster Recovery

If ML service fails:

``` text
Skin analysis unavailable
```

Other features remain functional.

If price service fails:

``` text
Alternatives still available
Price unavailable
```

If OCR fails:

``` text
Manual ingredient entry
```

This is graceful degradation.

------------------------------------------------------------------------

# 170. Reliability Principle

No single AI/third-party service should bring down the entire product.

Architecture:

``` text
Core DB + Compatibility
        |
        +-- OCR optional
        +-- ML optional
        +-- Price optional
        +-- LLM optional
```

------------------------------------------------------------------------

# 171. Data Freshness

Every external-data record should have:

``` text
retrieved_at
source
version where available
```

Freshness classes:

``` text
Real-time
Recent
Stale
Unknown
```

The UI should expose freshness when relevant.

------------------------------------------------------------------------

# 172. Product Data Confidence

Separate from scientific evidence.

Example:

``` text
Product data:
High confidence

Ingredient identification:
High confidence

Evidence:
Moderate

Overall result:
Moderate confidence
```

------------------------------------------------------------------------

# 173. Comparison Confidence

A result's confidence should be derived from:

-   formulation completeness,
-   ingredient normalization,
-   evidence coverage,
-   rule applicability.

It should not simply be an arbitrary average.

------------------------------------------------------------------------

# 174. Skin Recommendation Confidence

Separate:

``` text
Image observation confidence
Ingredient evidence strength
Product-data confidence
```

Example:

``` text
Observation confidence: Moderate
Evidence: High
Product data: High
```

------------------------------------------------------------------------

# 175. Alternative Confidence

Separate:

``` text
Product identification confidence
Ingredient data confidence
Price freshness
Similarity confidence
```

An alternative found from poor product identification should not be
presented as certain.

------------------------------------------------------------------------

# 176. Ethical UX

Never use fear-based copy such as:

> "WARNING! Your products are damaging your skin!"

Prefer:

> "Potential caution identified."

Never manipulate users into buying products.

Recommendations should be explainable and preference-aware.

------------------------------------------------------------------------

# 177. Commercial Neutrality

If affiliate links or monetization are introduced:

-   clearly disclose,
-   do not alter scientific compatibility results,
-   separate sponsored content,
-   preserve ranking transparency.

Commercial relationships must not determine evidence strength.

------------------------------------------------------------------------

# 178. Monetization --- Future

Potential models:

### Free

-   product comparison,
-   ingredient lookup,
-   limited analysis.

### Premium

-   advanced skin history,
-   routine analytics,
-   deeper personalization,
-   advanced tracking.

### Affiliate

-   retailer links,
-   disclosed.

### B2B

-   ingredient/product intelligence APIs.

Do not let monetization compromise trust.

------------------------------------------------------------------------

# 179. Competitive Positioning

SkinIQ should position itself around:

``` text
"Understand before you buy."
"Check before you layer."
"One place for your skin + products + routine."
```

The strongest positioning is not:

> "AI skincare."

It is:

> **Evidence-aware skincare decision support.**

------------------------------------------------------------------------

# 180. Core Product Loop

The ultimate loop:

``` text
                 ┌───────────────┐
                 │  ANALYZE SKIN │
                 └───────┬───────┘
                         ↓
                  SKIN CONCERNS
                         ↓
                 INGREDIENT TYPES
                         ↓
                   PRODUCTS
                         ↓
                  ALTERNATIVES
                         ↓
                  COMPATIBILITY
                         ↓
                     ROUTINE
                         ↓
                    MY SHELF
                         ↓
                  NEW PRODUCTS
                         │
                         └───────────────→
```

------------------------------------------------------------------------

# 181. Full End-to-End Skin Pipeline

``` text
USER
 ↓
Select skin type
 ↓
Capture/upload image
 ↓
Secure upload
 ↓
Validation
 ↓
Image quality
 ↓
ML inference
 ↓
Skin observations
 ↓
Confidence
 ↓
Concern mapping
 ↓
Evidence layer
 ↓
Ingredient/category recommendations
 ↓
Product retrieval
 ↓
User preference filtering
 ↓
Routine compatibility
 ↓
Product recommendations
 ↓
Alternatives
 ↓
Save / routine / compare
```

------------------------------------------------------------------------

# 182. Full End-to-End Product Pipeline

``` text
USER
 ↓
Product name/image/barcode
 ↓
Identification
 ↓
Candidate confirmation
 ↓
Product version
 ↓
Ingredient list
 ↓
Normalization
 ↓
Evidence
 ↓
Product page
 ↓
Alternatives
 ↓
Compatibility
 ↓
Routine
```

------------------------------------------------------------------------

# 183. Full End-to-End Comparison Pipeline

``` text
Product A
 ↓
Resolve version
 ↓
Normalize ingredients
      +
Product B
 ↓
Resolve version
 ↓
Normalize ingredients
      ↓
Pairwise rule evaluation
      ↓
Evidence retrieval
      ↓
Confidence calculation
      ↓
Structured result
      ↓
Human-readable explanation
      ↓
Share / Save / Routine
```

------------------------------------------------------------------------

# 184. Full End-to-End Alternative Pipeline

``` text
Reference product
 ↓
Feature extraction
 ↓
Candidate retrieval
 ↓
Remove duplicates
 ↓
Apply hard filters
 ↓
Ingredient similarity
 ↓
Target match
 ↓
Price observation
 ↓
Preference match
 ↓
Routine compatibility
 ↓
Ranking
 ↓
Explanation
 ↓
Compare / Save
```

------------------------------------------------------------------------

# 185. Final Acceptance Criteria

The system is ready for project demonstration when:

### Product

-   [ ] Product search works
-   [ ] Product pages work
-   [ ] Ingredient lists are normalized
-   [ ] Product versions exist

### Compatibility

-   [ ] Two products can be compared
-   [ ] Results are deterministic
-   [ ] Evidence is shown
-   [ ] Unknown data is handled
-   [ ] No false certainty

### Skin

-   [ ] Skin image uploads work
-   [ ] Quality checks work
-   [ ] Observations have confidence
-   [ ] Recommendations are connected to structured rules
-   [ ] Medical boundary is clear

### Alternatives

-   [ ] Product can be identified
-   [ ] Alternatives can be retrieved
-   [ ] Cheaper/similar categories work
-   [ ] Price timestamps exist
-   [ ] Ranking is explainable

### User

-   [ ] Signup works
-   [ ] Products can be saved
-   [ ] Shelf works
-   [ ] Routine works
-   [ ] History works

### Engineering

-   [ ] Unit tests
-   [ ] Integration tests
-   [ ] E2E tests
-   [ ] Security checks
-   [ ] Accessibility checks
-   [ ] CI/CD
-   [ ] Error monitoring

------------------------------------------------------------------------

# 186. Definition of Done

A feature is not done merely because it works on the developer's
machine.

A feature is done when:

``` text
Implementation
+
Validation
+
Error states
+
Loading states
+
Accessibility
+
Security
+
Tests
+
Analytics
+
Documentation
+
Deployment
```

are complete.

------------------------------------------------------------------------

# 187. Final Project Demonstration Flow

For the UCS503 presentation, demonstrate one continuous story:

``` text
1. Open SkinIQ

2. Analyze skin
   ↓
   upload image
   ↓
   show observations
   ↓
   show recommendations

3. Open a recommended product
   ↓
   show ingredients

4. Find alternatives
   ↓
   show cheaper/similar alternatives

5. Compare original vs alternative
   ↓
   show compatibility

6. Add products to My Shelf

7. Build routine

8. Analyze routine

9. Show evidence

10. Show admin/data governance

11. Show test cases

12. Show architecture/UML
```

This demonstrates that the website is a **complete software system**,
not just a frontend prototype.

------------------------------------------------------------------------

# 188. UCS503 Mapping

  UCS503 Topic             SkinIQ Implementation
  ------------------------ -----------------------------------------
  SDLC                     Iterative/incremental development
  Requirements             SRS + user stories
  Problem analysis         Skincare decision problem
  DFD                      Data-flow models
  Data Dictionary          Product/ingredient/evidence entities
  ER Model                 Database schema
  UML                      Use case/class/sequence/state/component
  Architecture             Client-server/modular architecture
  MVC                      Next.js UI + backend domain services
  Separation of Concerns   Domain modules
  Coupling/Cohesion        Modular monolith
  Testing                  Unit/integration/system/E2E
  V&V                      Evidence + testing
  Agile                    Scrum backlog/sprints
  TDD                      Compatibility/recommendation logic
  Story Cards              Feature decomposition
  UI Sketching             Workflow wireframes
  Risk                     Risk register
  Project Management       Scope/time/cost
  CASE artifacts           UML/DFD/ER tooling

The course syllabus explicitly emphasizes these software-engineering
areas, so the implementation and documentation should make them visible
rather than hiding them behind the codebase. fileciteturn1file0

------------------------------------------------------------------------

# 189. Recommended CASE Artifacts

Create:

``` text
docs/
├── srs.md
├── use-cases.md
├── dfd.md
├── data-dictionary.md
├── er.md
├── uml/
│   ├── use-case.md
│   ├── class.md
│   ├── sequence-comparison.md
│   ├── sequence-skin-analysis.md
│   ├── sequence-alternatives.md
│   ├── activity.md
│   ├── state.md
│   └── component.md
├── architecture.md
├── test-plan.md
├── test-cases.md
└── risk-register.md
```

------------------------------------------------------------------------

# 190. Final Technical Principles

### Principle 1

**The compatibility engine is deterministic.**

### Principle 2

**OCR is an extraction aid, not truth.**

### Principle 3

**Image analysis produces observations, not diagnoses.**

### Principle 4

**Recommendations are generated from structured knowledge.**

### Principle 5

**Alternatives are ranked transparently.**

### Principle 6

**Prices are observations with timestamps.**

### Principle 7

**Product formulations are versioned.**

### Principle 8

**Evidence is stored separately from explanations.**

### Principle 9

**Unknown information remains unknown.**

### Principle 10

**Private user images remain private.**

### Principle 11

**AI explains structured results rather than inventing scientific
truth.**

### Principle 12

**Every important result should be explainable.**

------------------------------------------------------------------------

# 191. Final Product Definition

> **SkinIQ is an evidence-aware skincare intelligence platform that
> analyzes visible skin concerns, recommends relevant skincare options,
> finds meaningful product alternatives, and explains whether products
> can be used together through transparent ingredient, product and
> evidence analysis.**

------------------------------------------------------------------------

# 192. Final Product Hierarchy

``` text
                         SKINIQ
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
  SKIN ANALYSIS       COMPATIBILITY        ALTERNATIVES
       |                   |                   |
       v                   v                   v
 What does my         Can I layer?       What else can
  skin need?                                I consider?
       |                   |                   |
       +-------------------+-------------------+
                           |
                           v
                  PRODUCT KNOWLEDGE
                           |
                           v
                 INGREDIENT KNOWLEDGE
                           |
                           v
                    EVIDENCE LAYER
                           |
                           v
                   USER PERSONALIZATION
                           |
                           v
                ROUTINE / MY SHELF / HISTORY
                           |
                           v
                    SEO + SHARING
```

------------------------------------------------------------------------

# 193. The One-Sentence Product Pitch

> **SkinIQ helps you understand your skin, choose products
> intelligently, find better alternatives, and check whether your
> skincare products work together --- before you layer.**

------------------------------------------------------------------------

# 194. Implementation Priority

If development time becomes constrained, preserve this order:

``` text
1. Product + Ingredient Data
2. Compatibility Engine
3. Product Search
4. Product Pages
5. OCR / Scanner
6. Skin Analysis MVP
7. Recommendation Engine
8. Alternatives Engine
9. My Shelf
10. Routine
11. Sharing
12. SEO Expansion
13. Advanced personalization
```

The project should never sacrifice the quality of the core
compatibility/data layer merely to add more AI features.

------------------------------------------------------------------------

# 195. Final Architecture Summary

``` text
                         SKINIQ
                            |
                      NEXT.JS WEB
                            |
                      FASTAPI API
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
     PRODUCT            SKIN                 USER
    INTELLIGENCE       ANALYSIS              DATA
        |                   |                   |
        +---------+---------+-------------------+
                  |
                  v
             KNOWLEDGE LAYER
                  |
       +----------+----------+
       |          |          |
       v          v          v
  Ingredients  Evidence  Compatibility
       |                     |
       +----------+----------+
                  |
                  v
           RECOMMENDATION
                  |
             +----+----+
             |         |
             v         v
        ALTERNATIVES ROUTINE
             |         |
             +----+----+
                  |
                  v
             MY SHELF
                  |
                  v
              RETENTION
                  |
                  v
          SEO / SHARING / GROWTH
```

------------------------------------------------------------------------

# 196. Final Quality Standard

A "10/10" SkinIQ implementation should satisfy five dimensions
simultaneously:

## Product

The user can solve a real skincare decision quickly.

## Scientific / Data Integrity

The system distinguishes:

``` text
observation
confidence
evidence
data quality
```

and never pretends uncertainty does not exist.

## Engineering

The system has:

``` text
clear architecture
modular code
versioned knowledge
tests
security
observability
```

## User Experience

The system is:

``` text
fast
simple
visual
mobile-friendly
accessible
transparent
```

## Growth

The system has:

``` text
SEO
sharing
guest utility
personalization
retention loops
analytics
```

Only when all five work together does SkinIQ become a serious product
rather than a collection of disconnected AI features.

------------------------------------------------------------------------

# 197. Research / Technical References

These references were checked while preparing the technical
architecture. Provider APIs, pricing, licensing and terms should always
be re-verified before implementation.

1.  **COSMILE Europe --- Cosmetic Ingredient Database**\
    https://cosmileeurope.eu/inci/\
    Ingredient information, INCI terminology, functions and product
    types. COSMILE currently describes information for almost 30,000
    cosmetic ingredients. citeturn0search1turn0search2

2.  **COSMILE Europe --- Understanding Cosmetics**\
    https://cosmileeurope.eu/facts/\
    Information about source reliability and cosmetic ingredient
    information. citeturn0search8

3.  **Google Cloud Vision --- OCR**\
    https://docs.cloud.google.com/vision/docs/ocr\
    Text detection and document text detection capabilities.
    citeturn0search7

4.  **Next.js --- Metadata and SEO**\
    https://nextjs.org/learn/seo/metadata\
    Metadata, Open Graph and structured data concepts.
    citeturn0search0

5.  **Next.js --- Metadata API**\
    https://nextjs.org/learn/dashboard-app/adding-metadata\
    Metadata, robots, sitemap and Open Graph mechanisms.
    citeturn0search4

6.  **FastAPI --- Background Tasks**\
    https://fastapi.tiangolo.com/tutorial/background-tasks/\
    Background processing and guidance for heavier worker-based
    workloads. citeturn1search0

7.  **Supabase --- Database**\
    https://supabase.com/docs/guides/database/overview\
    PostgreSQL-based database architecture. citeturn1search1

8.  **Supabase --- Auth Architecture**\
    https://supabase.com/docs/guides/auth/architecture\
    Authentication and JWT architecture. citeturn1search3

9.  **Supabase --- Storage**\
    https://supabase.com/docs/guides/storage/quickstart\
    File storage and access policies. citeturn1search5

10. **Vercel --- Next.js**\
    https://vercel.com/frameworks/nextjs\
    Next.js deployment and caching infrastructure. citeturn1search6

11. **OWASP --- File Upload Cheat Sheet**\
    https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html\
    File validation, storage, access control and upload security.
    citeturn1search2

12. **UCS503 Software Engineering syllabus**\
    Uploaded course syllabus used as the basis for the
    software-engineering deliverables and course mapping.
    fileciteturn1file0

------------------------------------------------------------------------

# 198. Final Build Philosophy

The correct implementation mindset is:

``` text
DO NOT BUILD:
"an AI skincare chatbot"

BUILD:

A structured skincare intelligence system
        +
computer vision where useful
        +
OCR where useful
        +
deterministic compatibility logic
        +
evidence-aware recommendations
        +
transparent alternative ranking
        +
personalized routines
        +
strong UX
        +
SEO
        +
software-engineering rigor
```

That is the complete SkinIQ product.
