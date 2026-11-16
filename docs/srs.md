# Software requirements specification (summary)

IEEE 830-style summary. The full requirement text is in `SPEC.md` (SkinSync, source of truth) and
`SPEC_SKINIQ_MASTER.md`; implementation status per requirement is in `requirements-traceability.md`.

## 1. Introduction
**Purpose:** an evidence-aware skincare decision-support web application. **Scope:** compare two products,
find alternatives, analyse visible cosmetic skin features, plus search, scanning, shelf, routines,
sharing and knowledge governance. **Out of scope:** diagnosis, treatment, universal safety claims,
automated purchasing.

## 2. Overall description
* **Users:** guest, registered user, admin, viewer of shared links.
* **External systems:** Open Beauty Facts (product data), Tesseract (OCR), skin model adapter (mock today),
  SMTP (email).
* **Constraints:** deterministic rules decide compatibility; unknown data stays unknown; skin data private by
  default; no invented evidence or prices; India first (INR, DPDP principles); runs on free tooling.
* **Assumptions:** see `../ASSUMPTIONS.md`.

## 3. Specific requirements
* **Functional:** FR-01 … FR-20 (`SPEC.md` §15) — 20 requirements.
* **Non-functional:** NFR-01 … NFR-10 (`SPEC.md` §14).
* **Use cases:** UC01 … UC12 (`SPEC.md` §7, `uml/use-case.md`).
* **Acceptance:** story cards SC-01 … SC-05 and SkinIQ compatibility cases C01 … C07.

## 4. Verification
`test-plan.md`, `test-cases.md`; every test name carries its requirement id.
