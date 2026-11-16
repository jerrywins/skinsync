# Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner / status |
|---|---|---|---|---|---|
| R1 | No reviewed interaction rules: real comparisons only say "insufficient evidence" or "data incomplete" | Certain today | High (core value) | Admin workflow + file formats ready; publish knowledge v1 after scientific review | Team: **open** |
| R2 | Users read a demo result as real advice | Medium | High | DEMO badges on every demo screen; separate demo knowledge; demo off by default; prod refuses demo mode | Mitigated |
| R3 | Skin model gives misleading observations | Certain with mock | High | Mock labelled everywhere; real model gated by `model-evaluation.md` criteria | Team: **open** |
| R4 | Wrong ingredient match produces a false finding | Medium | High | Fuzzy similarity never resolves; reviewed aliases only; admin corrections create new versions | Mitigated |
| R5 | Crowd-sourced OBF data incomplete or wrong | High | Medium | Provenance + retrieved date shown; completeness shown; user reports; flags queue | Partly mitigated |
| R6 | Thin Indian product coverage (51 of 2,557 imported) | Certain | Medium | Team CSV import format; prioritise curated Indian products | Team: **open** |
| R7 | ODbL share-alike not honoured on redistribution | Low | Medium | Attribution shipped; obligations in `data-governance.md` | Mitigated (process) |
| R8 | Skin photo leak | Low | High | Encryption at rest, deletion after analysis, no public URLs, no sharing, retention job | Mitigated |
| R9 | Account takeover | Low | High | Argon2id, rate limits, refresh reuse detection, verified email; no MFA yet | Partly mitigated |
| R10 | Medical-claim drift in copy or mappings | Medium | High | Observation vocabulary without condition names; mapping loader rejects condition/diagnosis words; review | Mitigated |
| R11 | Prices shown as current when stale | Low | Medium | Freshness states; cheaper/premium only with fresh same-currency prices | Mitigated |
| R12 | Untested deployment path (Docker, Trivy, gitleaks not run here) | Medium | Medium | Run `make up` and CI on a machine with Docker before any demo | **Open** |
| R13 | Single-region, single-node deployment | Medium | Medium | Backups (`make backup`), documented restore | Accepted for student project |
