# ADR 0002: Compatibility result taxonomy and status precedence

**Status:** Accepted. **Date:** 2026-11-03

**Conflict.** SkinSync §11 suggests labels ("Notable interaction", "Possible redundancy", ...). SkinIQ §34 and
the implementation prompt require exactly five categories.

**Decision.** Use the five SkinIQ categories (`no_notable_interaction`, `caution`, `strong_caution`,
`insufficient_evidence`, `data_incomplete`). The clear case uses the SkinSync mandatory wording verbatim:
"No notable interaction identified in the current knowledge base for the formulations supplied."

Precedence, most conservative first:
1. A fired reviewed rule sets `strong_caution` / `caution` (we say what we know).
2. Otherwise a missing list or any unresolved ingredient sets `data_incomplete` (unknown never becomes clear).
3. Otherwise an empty knowledge version sets `insufficient_evidence`.
4. Otherwise `no_notable_interaction`.

Shared key actives are reported as a **factual** finding (both contain X) with evidence strength `unknown`.
They never raise the status by themselves, because that would be a scientific claim without evidence.

**Consequence.** With no reviewed rules shipped, real comparisons return `data_incomplete` or
`insufficient_evidence`. This is intended.
