# Admin guide

Admins are created only from the command line:
`docker compose exec -e SKINSYNC_ADMIN_PASSWORD api python -m skinsync.cli create-admin you@example.org`.
Every admin action is written to the append-only audit log with your reason.

## Publish knowledge (rules, evidence, concern mappings)

1. Edit `knowledge/evidence.yaml`, `rules.yaml`, `concern_map.yaml` (formats in `data-governance.md`).
   Every rule and mapping must cite at least one evidence record with a real citation.
2. Get the change reviewed (pull request). Then rebuild/redeploy so the API sees the files.
3. Admin → Knowledge versions → enter an id such as `kv-2026-11` → **Import reviewed files as a draft**.
   Files marked `fixture: true` or evidence with `source_type: fixture` are refused.
4. **Send to review**, check the rules and the "can't be published yet" list.
5. **Publish**. Blocked if any rule has no evidence, is not marked reviewed, relies only on insufficient or
   unknown evidence, uses fixture evidence, or has an open conflicting-evidence flag. The database
   re-checks. Publishing retires the previous version; saved results made with it are marked out of date.
6. **Roll back** by re-publishing a retired version.

Published versions never change. To fix one, import a new version.

## Review queue

* **unknown ingredient / fuzzy match**: add the ingredient or alias (`POST /api/v1/admin/ingredients`), or
  correct one entry (`POST /api/v1/admin/ingredient-mappings` with `product_version_id`, `position`,
  `ingredient_id` or `null` for "genuinely unknown", and a reason). Corrections create a new formulation
  version and teach the alias to future imports.
* **missing ingredient list**: import the list via the team CSV.
* **low OCR confidence**: check the user's confirmed text if relevant; no automatic action.
* **user report**: verify against the label or manufacturer, correct, then resolve with a note.

Resolve or dismiss each item with a note; the note goes to the audit log.
