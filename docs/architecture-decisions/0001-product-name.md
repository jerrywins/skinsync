# ADR 0001: Product name

**Status:** Accepted, open to change. **Date:** 2026-11-03

**Conflict.** `SPEC.md` says the product is **SkinSync** and that "SkinIQ" is an earlier name. The SkinIQ
master spec and implementation prompt use **SkinIQ** throughout.

**Decision.** Use **SkinSync** in code and UI, because the SkinSync spec explicitly supersedes the older name.
The display name will be a single config value (`APP_NAME`) so switching is a one-line change.

**Consequence.** If the team prefers SkinIQ, change `APP_NAME`; nothing else depends on the name.
