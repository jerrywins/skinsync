# Progress

**Last verified checkpoint: 2026-11-05.** Final report: `docs/FINAL_REPORT.md`.

## Verified
* Backend: 142 tests pass (real PostgreSQL 16 + Redis); 81% coverage; engine 100% line + branch.
* Frontend: 37 routes build; 14 Playwright E2E tests pass against the production build, with axe checks.
* Ruff, Bandit (project config), pip-audit, npm audit clean. Load-test targets met.
* Docker Compose stack runs on macOS (Apple Silicon). GitHub Actions CI: all 4 jobs green (2026-11-23).
* Open Beauty Facts import: 2,557 skincare products (1,711 with ingredient lists, 51 Indian).
* Experimental heuristic skin adapter (default) with advisory YuNet face check; labelled "not validated".
* AI-drafted knowledge: 4 rules, 5 evidence records, 9 ingredient entries, all draft; publishing blocked.
* Dev/test-only random TEST prices, badged in the UI, hidden in staging/prod, removable.

## Not verified here
  Mac instructions: `docs/MAC_DOCKER_GUIDE.md`.
* Camera capture on a real phone. Real SMTP delivery. S3/MinIO storage backend.
* Heuristic adapter and face detector on real face photos.

## Needs people, not code
1. Review the drafted rules/evidence (`knowledge/rules.yaml`, `evidence.yaml`), mark reviewed, publish.
2. Reviewed concern mappings and ingredient functions.
3. A validated skin model and evaluation dataset (`docs/model-evaluation.md`).
4. A licensed price source (then `make remove-test-prices`); more Indian products via the team CSV.
