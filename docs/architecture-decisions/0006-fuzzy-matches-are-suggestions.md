# ADR 0006: Fuzzy ingredient matches are suggestions, never resolutions

**Status:** Accepted (supersedes A2 in ASSUMPTIONS). **Date:** 2026-11-04

**Context.** After importing Open Beauty Facts, a spot check showed fuzzy matching at a 0.92 similarity
threshold mapping different chemicals onto each other: polyglyceryl-2 caprate → -4 caprate, palmitoyl
tripeptide-1 → -5, sodium oleth sulfate → coceth sulfate. They were flagged for review, but the engine
still treated them as known ingredients.

**Decision.** Fuzzy similarity only produces a `candidate` suggestion; the ingredient stays unresolved
until a person confirms it. No suggestion is made when the numbers in the two names differ.
"INCI / common name" labels resolve to the first-written name at confidence 0.8, flagged for review.

**Consequence.** Lower completeness on imported data (average 0.764), but no silent wrong matches.
