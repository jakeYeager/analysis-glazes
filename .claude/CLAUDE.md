# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing — see `README.md`. The workflow below is self-contained: you shouldn't need to read anything else to price a recipe, add a new one, or resolve an unpriced material. `docs/archive/price_list_run_notes.md` is a historical log of how this workflow was built (manual browser-driven collection, then automation, then the SQLite migration) — useful for the "why" behind a design decision, not required reading for day-to-day work.

## Workflow

### One-time setup

```
uv run --with playwright playwright install chromium
```
Playwright's browser binary is a real local install, not ephemeral like the rest of this project's tooling.

### Every session

`db/glazes.db` is gitignored and disposable. If it doesn't exist (fresh clone, new session), hydrate it from the git-tracked checkpoint CSVs:

```
python3 scripts/db_build.py
```

Idempotent — always safe to re-run to discard local DB state and rebuild from the last commit.

### Add a new recipe

```
uv run --with playwright scripts/import_glazy_recipe.py <glazy_recipe_url> [--firing-type mid-fire|raku] [--force]
```

Fetches the recipe once and inserts `recipes`/`recipe_ingredients`/new `materials` rows (new materials start `match_confidence='not_found'`, no price data). Recipes don't drift like prices — no staleness window; re-running against an already-imported `glazy_url` is a no-op unless `--force`. `firing_type` is auto-detected from the page's Atmospheres field (`raku` if it mentions raku, else `mid-fire`) unless overridden. `is_addition` is detected from Glazy's own "Total base recipe" subtotal row — everything after it and before the final "Total" row is an addition; a recipe with no additions has no subtotal row at all.

**Watch for cross-recipe material duplicates** after importing: Glazy isn't consistent about material naming across recipes. The known case — a manufacturer prefix, e.g. "Ferro" — is caught automatically (`get_or_create_material()` checks whether stripping a prefix in `KNOWN_MANUFACTURER_PREFIXES` matches an existing material before creating a new row, and `find_material_candidates.py` tries the stripped name as an IMCO search term too). Anything not covered by that list will still create a second `materials` row — check for near-duplicate `canonical_name`s and merge by hand if needed (see "Material name variants" in `.claude/rules/conventions.md`). Never auto-merge an unconfirmed case.

### Add a new recipe that isn't on Glazy yet

```
python3 scripts/import_csv_recipes.py <csv_path> --firing-type mid-fire|raku
```

For recipes sourced somewhere other than Glazy (e.g. a personal spreadsheet dropped in the gitignored `_inbox/` for review before porting in) that don't have a `glazy_url` yet. Expects a wide/pivoted CSV: first column is material name, one column per recipe, header row is the recipe name. Skips a column if a recipe with that name already exists — not meant for repeated re-import the way Glazy recipes are (no `--force`). `KNOWN_MATERIAL_ALIASES` maps a known exact-name synonym (e.g. `"EPK"` → `"EP Kaolin"`) to an existing material instead of creating a duplicate — same idea as `KNOWN_MANUFACTURER_PREFIXES`, just a full-name match rather than a prefix.

**`is_addition` is defaulted to `false` for every ingredient imported this way**, since a flat spreadsheet has no equivalent of Glazy's "Total base recipe" subtotal marker to tell base ingredients from additions. Each such recipe's `notes` flags this explicitly. Once you manually add the recipe to Glazy, re-run `import_glazy_recipe.py <url> --force` on it to pick up the real base/addition split from the live page — don't leave the `false` default as the final word.

### Price a recipe

```
uv run --with playwright scripts/price_batch.py "<recipe name>"
```

For each ingredient: uses the cached price if `last_verified` is within `STALENESS_DAYS` (90, set at the top of the script); otherwise refreshes it via `scrape_imco_price.py` and logs a `price_snapshots` row. A `not_found` material triggers `find_material_candidates.py` (below) and is excluded from the total rather than priced with a guess. Prints an itemized cost table with cached/refreshed/unresolved status per line.

### Resolve a `not_found` or `fuzzy` material

1. `price_batch.py` (or a direct call to `scripts/find_material_candidates.py <recipe_glazy_url> "<material name>"`) logs IMCO search candidates to `name_candidates_log` — scrapes Glazy's "Child materials" alternate-name list for that material, tries each name (plus a manufacturer-prefix-stripped variant) against IMCO search, and keeps only results that share a real word with the search term. IMCO returns unrelated "trending" products for a bad query rather than zero hits, so raw hit count alone isn't trustworthy — and even a genuine word-overlap hit can be a false positive (e.g. "Tin Oxide" incidentally matched "Chrome Oxide Green" on the word "oxide"), so spot-check a multi-hit candidate live before trusting it.
2. Review the logged candidates (`sqlite3 db/glazes.db "SELECT * FROM name_candidates_log WHERE material_name = '...'"`, or browse the table in Datasette) and pick the right one. A single generic product with no grade ambiguity is usually enough to confirm; if the material could have multiple grades (seen before with Bentonite, Wollastonite), check the live product page or ask before picking one.
3. Apply it directly to the `materials` row — only once you're confident, per the never-fabricate rule:
   ```sql
   UPDATE materials SET imco_url = '<confirmed URL>', match_confidence = 'exact' -- or 'fuzzy'
   WHERE canonical_name = '<material name>';
   -- rename here too if canonical_name should drop a manufacturer prefix, e.g.:
   -- UPDATE materials SET canonical_name = 'Frit 3124', match_confidence = 'fuzzy', imco_url = '...'
   -- WHERE canonical_name = 'Ferro Frit 3124';
   ```
   Leave `last_verified` unset — the next `price_batch.py` run treats the row as "confirmed but stale" and auto-refreshes it through the normal `scrape_imco_price.py` path. No separate pricing step needed.
4. Re-run `price_batch.py` for any recipe using that material to confirm it now prices correctly.

### Generate the stakeholder price summary

```
python3 scripts/generate_price_summary.py
scripts/md2pdf.sh reports/glaze_price_summary.md
```

Reads `db/glazes.db` (no scraping — reports on whatever's currently cached; run `price_batch.py` first for each recipe if you want fresher numbers reflected) and writes `reports/glaze_price_summary.md` (grouped by `firing_type`, one row per recipe: `$/lb`, batch weight, total cost, oldest `last_verified` among its ingredients as "Last Priced," and a flag if any ingredient is still unpriced) plus a `reports/glaze_price_summary.csv` twin for spreadsheet use. The `md2pdf.sh` step turns it into the actual file you hand to stakeholders. Regenerate both before sharing an updated copy — it's cheap and keeps the deliverable honest about staleness.

### Before committing

```
python3 scripts/db_export.py
```

Flushes `db/glazes.db` state back into the four checkpoint CSVs (`recipes/recipe_metadata.csv`, `recipes/compare_recipes.csv`, `ingredients/ingredient_prices.csv`, `ingredients/name_candidates_log.csv`) so git history stays the diffable record of what changed. Commit those CSVs, never the `.db` file.

### Browsing / ad-hoc queries

`datasette db/glazes.db` for a local read-only browser and SQL UI. CRUD stays in the scripts above, not through Datasette.

## Schema (`db/schema.sql`)

- **`materials`** — one row per raw material: `price`/`unit` (smallest *tracked* tier, 1 lb and up), `bulk_price`/`bulk_unit` (cheapest true per-unit tier at its real quantity — not always the largest size, verify don't assume), `price_1lb`…`price_100lb` (tier breakdown at standard sizes), `imco_url`, `match_confidence` (`exact`/`fuzzy`/`not_found`), `notes`, `last_verified`, `glazy_material_url`.
- **`recipes`** — one row per recipe: `name`, `glazy_url`, `firing_type` (`mid-fire`/`raku`), `cone`, `atmosphere`, `status`, `imported_date`, `notes`.
- **`recipe_ingredients`** — links a recipe to its materials: `amount`, `is_addition`.
- **`price_snapshots`** — one row per material per day it was actually refreshed (history; replaces the old full-sheet-copy convention in `ingredients/snapshots/*.csv`, which stays as historical record but won't gain new dated files).
- **`name_candidates_log`** — logged IMCO search candidates for unresolved materials, per "Resolve a `not_found` or `fuzzy` material" above.

`db/glazes.db` is the live working copy — agents/scripts read and write it directly via `sqlite3`; the four checkpoint CSVs are what's git-tracked and reviewed. Think of it like a build artifact: there's no "keeping the DB in sync" chore, because the DB is *supposed to* be rebuilt on demand from the CSVs (`db_build.py`), and the CSVs are *supposed to* be refreshed from the DB before every commit (`db_export.py`). `glazy_url` appears in both `recipe_metadata.csv` and `compare_recipes.csv` (once per recipe vs. once per ingredient row) — kept that way deliberately so `compare_recipes.csv`'s shape didn't change for anything already reading it (e.g. `reports/frit3134_vs_gerstley_borate_cost_comparison.md`).

## Conventions

See `.claude/rules/conventions.md` for: firing-type detection/inference, the ingredient price-tier bucketing rules (sub-1lb drop, closest-standard-column mapping for non-standard pack sizes), confirmed material name variants (manufacturer prefixes), the 100-part base-glaze recipe convention, and report formatting/versioning.

**Never fabricate a price or a match.** If a material can't be found or verified, leave price fields null and mark `not_found`, with a note on what was tried. A `fuzzy` match means inferred equivalence, not a literal name match — worth a spot-check, not blind trust.

## Technical gotchas

Confirmed live against Glazy and IMCO. Both are JS-rendered SPAs — data collection and verification both require a tool that actually renders JavaScript (real browser automation), not a plain text-fetch tool; a text-fetch tool returning empty content proves nothing about whether a browser-collected claim is real.

- `wait_until="networkidle"` hangs indefinitely on IMCO's Square Online pages (persistent background connections never go idle) — use `"load"` plus a short fixed wait instead. Already applied in every script here; don't reintroduce it.
- IMCO's weight-tier `<select>` includes a disabled placeholder option (`"Select one"`) — `scrape_imco_price.py` filters out disabled/empty options before looping over tiers.
- IMCO's search doesn't return zero results for a bad query — it falls back to unrelated "trending" products, so raw hit count isn't a relevance signal on its own; `find_material_candidates.py` filters by word-overlap instead. Even that can false-positive on a shared word (e.g. "oxide" matching both "Tin Oxide" and "Chrome Oxide Green") — treat a multi-hit candidate as worth a live spot-check, not an automatic pick.
- Manufacturer-prefix name variants (e.g. "Ferro Frit NNNN" = "Frit NNNN") are a *confirmed* class, not a guess — see "Material name variants" in `.claude/rules/conventions.md`.
- A tier-price `<select>` can include a non-quantity option that doesn't start with a number (seen live: a bare `"Oz"` option on Cobalt Carbonate's page, alongside its normal 1/4–55.14 lb tiers) — `price_batch.py`'s `refresh_material()` catches the resulting `parse_quantity` failure per-tier and skips just that option rather than crashing the whole refresh.

## Open items

- One material used in multiple recipes here (EP Kaolin) was found completely out of stock at the supplier as of the last price-collection run — worth rechecking before relying on any cost estimate that includes it.
- **16 raku recipes bulk-imported from a personal spreadsheet (2026-07-04, via `scripts/import_csv_recipes.py`) have `is_addition=false` on every ingredient by default — not yet confirmed.** Each has a `notes` flag saying so. As each gets manually added to Glazy, re-run `import_glazy_recipe.py <url> --force` on it to pick up the real base/addition split. Until then, don't trust `is_addition` for: Clear Crackle, Fern Green Crackle, Sky Blue Crackle, Ferguson White Crackle, Marble White Crackle, Del Favero Luster, Metallic Turquoise, Ballingham Black Luster, Reynolds Wrap, Copper Sand, Emerald Green Copper Flash, Post Pac Man, Forbes Midnight Blue, Bill's Neon Blue 2024, Blue Moon, Kelly's Lo-Fire Shino.
- **`Custer Feldspar`** (used in Ballingham Black Luster, Forbes Midnight Blue) is priced via the G-200 substitute (same SKU as "Potash Feldspar") since Custer is confirmed discontinued (extinct as of 2024) — see that material's `notes`. Chemistry isn't identical; a recipe may need reformulation to hit original targets, which this cost analysis doesn't address.
- **`Ball Clay`** (used in Post Pac Man) is priced as OM4 (Old Mine #4) — the source recipe didn't specify a grade, and OM4 was Jake's pick among several real options (2026-07-04). Confirm against the actual recipe if the grade matters.
- "Bill's Neon Blue 2024" (from that same import) is closely related to but distinct from "Looks Expensive" — Glazy's page for "Looks Expensive" already says it's a *"Revision of Bill's Neon Blue 2025,"* so the "2024" spreadsheet version is very likely the prior iteration, not a duplicate. Both are tracked separately; worth confirming that relationship once "Bill's Neon Blue 2024" (or a later revision of it) is added to Glazy.
