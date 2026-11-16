# ADR 0007: Fictional demo dataset, isolated from real data

**Status:** Accepted. **Date:** 2026-11-04

**Context.** With no reviewed rules, the comparison and skin pipelines can't be demonstrated end to end
on real data, and inventing science is forbidden.

**Decision.** `knowledge/demo/` holds fictional ingredients ("DEMO RETINAL-X"), products, prices, rules and
evidence, all marked `fixture: true`. They load only with `SKINSYNC_DEMO_MODE=true` into a separate,
labelled knowledge version. Demo products can only be compared with demo products (`DEMO_MIX` error);
real products always use the real knowledge version. Prod configuration refuses demo mode.

**Consequence.** Demos are honest and complete; nothing fictional can reach a real result.
