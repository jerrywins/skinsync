# ADR 0005: Confidence is the weakest link, separate from evidence

**Status:** Accepted. **Date:** 2026-11-03

Result confidence = min(formulation completeness, lowest normalization confidence among resolved
ingredients, lowest fired-rule confidence; 0 if the knowledge version has no rules). It is never an average
(SkinIQ §173). Evidence strength is a separate field taken from the strongest evidence behind a fired rule.
Thresholds for labels: high ≥ 0.85, moderate ≥ 0.6, else low. These are design parameters.
