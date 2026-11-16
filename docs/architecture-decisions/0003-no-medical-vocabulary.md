# ADR 0003: Cosmetic observation vocabulary

**Status:** Accepted. **Date:** 2026-11-03

**Conflict.** SkinIQ §16 lists "acne/acne-like visible lesions" and "acne marks". SkinSync §2.3 forbids naming
acne or any condition.

**Decision.** SkinSync's [SOURCE] boundary wins. Observations use appearance words only
(`visible_blemishes`, `dark_spots_appearance`, ...). The concern-mapping loader rejects text containing
condition or diagnosis terms.
