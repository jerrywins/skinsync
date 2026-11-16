# Implementation roadmap

| Phase | Content | Status |
|---|---|---|
| 0 | Audit, specs, ADRs, traceability | Done |
| 1 | Foundation: config, DB, errors, request ids, logging, metrics, migrations | Done |
| 2 | Product + ingredient intelligence: OBF importer, normalisation, provenance, search, pages | Done |
| 3 | Compatibility engine, knowledge versions, comparison API + UI | Done (rules awaiting review) |
| 4 | Identification + OCR: barcode, label OCR, confirm/correct, candidates | Done |
| 5 | Skin analysis: upload, validation, encrypted storage, worker, adapter | Done with demo adapter |
| 6 | Recommendations: concern mapping, product retrieval, routine filtering | Done (mappings awaiting review) |
| 7 | Alternatives engine and UI | Done |
| 8 | Shelf, routines, history, sharing | Done |
| 9 | Admin and governance | Done |
| 10 | SEO, analytics, accessibility, performance, security, CI/CD, deployment | Done; Docker/CI not executed here |

## Next (outside code)
1. Scientific review → knowledge v1 → publish.
2. Real skin model + evaluation; then switch `SKINSYNC_SKIN_MODEL_ADAPTER`.
3. Price source; curated Indian catalogue.
4. Run CI and `make up` on a Docker host; Lighthouse CI; manual screen-reader pass.
