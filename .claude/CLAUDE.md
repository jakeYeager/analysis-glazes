# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing — see `README.md` . Read `docs/price_list_run_notes.md` for full context, source systems, and the key lessons learned so far, before doing new data collection work; it contains hard-won gotchas (non-monotonic bulk pricing, JS-rendered source sites, ingredient-name mismatches) that are easy to re-discover the hard way otherwise.

## Database-backed workflow

Recipes, materials, and prices live in `db/glazes.db` (SQLite), not directly
in CSVs. `db/glazes.db` is gitignored — it's a disposable working copy, not
the source of truth. The source of truth is `db/schema.sql` (tracked) plus
three checkpoint CSVs (also tracked): `recipes/compare_recipes.csv`,
`ingredients/ingredient_prices.csv`, `ingredients/name_candidates_log.csv`.

- **`scripts/db_build.py`** — hydrates `db/glazes.db` from the checkpoint
  CSVs + `db/schema.sql`. Run this first in any new session/clone, or any
  time you want to discard local DB state and rebuild from the last commit.
  Idempotent — always safe to re-run.
- **`scripts/db_export.py`** — the reverse: flushes current DB state back
  into the same three CSVs. Run this before committing any change made
  through the DB, so git history stays the diffable record of what changed.

Think of it like a build artifact: `db/glazes.db` is what agents/scripts
actually read and write during a session (via `sqlite3`), and Datasette
(`datasette db/glazes.db`) is how a human browses/queries it — but the
checkpoint CSVs are what's committed and reviewed. There's no "keeping the
DB in sync" chore because the DB is *supposed to* be rebuilt on demand.

**Schema** (`db/schema.sql`): `materials` (one row per raw material — price
tiers, IMCO match info, same fields as the old `ingredient_prices.csv` row),
`recipes` (name, `glazy_url`, `firing_type` — `mid-fire` or `raku` — cone,
atmosphere, status), `recipe_ingredients` (links a recipe to its materials
with `amount`/`is_addition`), `price_snapshots` (one row per material per
day it was actually refreshed — replaces the old full-sheet-copy convention
in `ingredients/snapshots/*.csv`, which stays as historical record but won't
gain new dated files), `name_candidates_log` (same shape as before, now a
table).

- **Verifying scraped data:** both Glazy and the IMCO supplier site are JS-rendered SPAs. Data collection and verification both require a tool that actually renders JavaScript (real browser automation), not a plain text-fetch tool — a text-fetch tool returning empty content proves nothing about whether a browser-collected claim is real.

## Automated scripts

All run via `uv run --with playwright <script>` (one-time setup: Playwright's
browser binary is a real local install, not ephemeral like the rest of this
project's tooling — run `uv run --with playwright playwright install chromium`
once before first use). All operate on `db/glazes.db` directly.

- **`scripts/scrape_imco_price.py <imco_url>`** — pulls the full weight-tier price table off one IMCO product page, headless.
- **`scripts/find_material_candidates.py <recipe_glazy_url> "<material name>"`** — for a `fuzzy`/`not_found` material, scrapes Glazy's alternate-name list for that material and tries each against IMCO search, inserting candidates into `name_candidates_log`. Never writes to `materials` itself — a human still confirms fuzzy matches, per the never-fabricate rule.
- **`scripts/price_batch.py "<recipe name>"`** — the pricing orchestrator. Prices every ingredient in a recipe, using the cached price if `last_verified` is within `STALENESS_DAYS` (90, set at the top of the script), otherwise refreshing it via `scrape_imco_price.py` and inserting a `price_snapshots` row. Unresolved (`not_found`) materials trigger `find_material_candidates.py` and are excluded from the total rather than priced with a guess.
- **`scripts/import_glazy_recipe.py <glazy_url> [--firing-type mid-fire|raku] [--force]`** — fetches a Glazy recipe once and inserts `recipes`/`recipe_ingredients`/new `materials` rows. Recipes don't drift like prices, so there's no staleness window — re-running against an already-imported `glazy_url` is a no-op unless `--force`. This is how new recipes get added at scale (one idempotent script call each) instead of an agent browsing session per recipe.

`materials`, `price`/`unit`, `bulk_price`/`bulk_unit`, and the
`price_1lb`…`price_100lb` tier columns follow the same conventions as
before — see "Ingredient price tiers" in `.claude/rules/conventions.md` for
the sub-1lb-drop and closest-bucket rules, and "Firing type" there for the
mid-fire/raku convention. Never fabricate a price — if a material can't be
found or verified, leave price fields null and mark `not_found`, with a note
on what was tried.

## Open items / natural next steps

- One material used in multiple recipes here (EP Kaolin) was found completely out of stock at the supplier as of the last price-collection run — worth rechecking before relying on any cost estimate that includes it.
- The scraping scripts were verified end-to-end against live Glazy/IMCO pages on 2026-07-04 (see `docs/price_list_run_notes.md` Runs 4-6). Gotchas worth knowing if you touch these scripts: (1) `wait_until="networkidle"` hangs on IMCO's Square Online pages (persistent background connections never go idle) — use `"load"` + a short fixed wait instead; (2) IMCO's search doesn't return zero results for a bogus query, it falls back to unrelated "trending" products, so `find_material_candidates.py` filters matches by word-overlap with the search term rather than trusting raw hit counts; (3) `import_glazy_recipe.py`'s `is_addition` detection (a `"+"`-prefixed amount) is unconfirmed live — Frogskin, the only recipe imported from Glazy so far, has no additions on its own page. Spot-check against a recipe that has some before bulk-importing.
