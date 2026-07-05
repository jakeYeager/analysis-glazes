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
- **7 of the original 16 raku recipes bulk-imported from a personal spreadsheet (2026-07-04, via `scripts/import_csv_recipes.py`) still have `is_addition=false` on every ingredient by default — not yet confirmed.** Each has a `notes` flag saying so. As each gets manually added to Glazy, re-run `import_glazy_recipe.py <url> --force` on it to pick up the real base/addition split — this now also works when the recipe was only ever bulk-imported (no `glazy_url` yet), since the existing-recipe check matches by name as well as URL. Until confirmed, don't trust `is_addition` for: Clear Crackle, Fern Green Crackle, Sky Blue Crackle, Ferguson White Crackle, Marble White Crackle, Del Favero Luster, Ballingham Black Luster. (Blue Moon is also still unconfirmed on `is_addition`, but is reference-only — see below; Kelly's Lo-Fire Shino, also reference-only, is now confirmed — see below.) **Copper Sand, Bill's Neon Blue 2024→2025, Reynolds Wrap, Forbes Midnight Blue, Post Pac Man, and Forbes Emerald Green Flash are now confirmed**: re-importing Copper Sand (added to Glazy 2026-07-04, `glazy.org/recipes/561485`) picked up a different CMC Gum amount than the spreadsheet had (4.0 vs. Glazy's 2.0; new total $656.00/113.75 lb = $5.77/lb, was $676.00/115.75 lb = $5.84/lb). Per Jake, this isn't a data-quality concern: CMC Gum is a "to taste" application aid (brushability, not chemistry), so its amount is expected to vary between sources — see "Recipes" in `.claude/rules/conventions.md`. Don't read a CMC Gum difference the same way as a flux/colorant one when confirming the remaining recipes.
- **`Custer Feldspar`** (used in Ballingham Black Luster, Forbes Midnight Blue) is priced via the G-200 substitute (same SKU as "Potash Feldspar") since Custer is confirmed discontinued (extinct as of 2024) — see that material's `notes`. Chemistry isn't identical; a recipe may need reformulation to hit original targets, which this cost analysis doesn't address. **Forbes Midnight Blue's own recipe on Glazy is locked** (Jake can't edit it to reflect the substitute), so its `recipes.notes` carries a `STAKEHOLDER NOTE` flagging that its `$/lb` is computed via G-200, not literal Custer — confirmed 2026-07-05.
- **`Ball Clay`** (used in Ferguson White Crackle, Hasselle Copper Matte, Reynolds Wrap) is priced as OM4 (Old Mine #4) — these recipes don't specify a grade, and OM4 was Jake's pick among several real options (2026-07-04). Confirm against the actual recipe if the grade matters. (Corrected 2026-07-05: this was originally attributed to Post Pac Man's spreadsheet version, which specified plain Ball Clay — that recipe was since reformulated on Glazy without any ball clay at all, so it no longer belongs on this list.)
- **Resolved:** "Bill's Neon Blue 2024" (the spreadsheet version) and "Bill's Neon Blue 2025" (`glazy.org/recipes/561486`) are the same recipe — confirmed 2026-07-04 by comparing ingredient-for-ingredient (identical except CMC Gum, which per the note above isn't a real discrepancy). The "2024" row was deleted in favor of the Glazy-sourced "2025" one (correct `is_addition` split, real `glazy_url`), matching Glazy's own naming rather than keeping both.
- **Resolved:** "Reynolds Wrap" confirmed 2026-07-05 against `glazy.org/recipes/561482` — exact match on every ingredient amount (no CMC-Gum-style variance this time); `is_addition` split applied: Gerstley Borate/Nepheline Syenite/Silica/Ball Clay/Barium Carbonate are base, Copper Carbonate/Bentonite are additions. New total $465.26/114 lb = $4.08/lb. Note: this Glazy recipe is **unpublished** (owner-only), so `import_glazy_recipe.py`'s headless Playwright fetch returned "Recipe does not exist" — had to view it via a logged-in browser session (Claude in Chrome) and apply the DB update by hand, matching the script's same fast-path/name-match/delete-and-reinsert logic. If more unpublished recipes come up, this is the workaround until/unless the script supports an authenticated session.
- **Resolved:** "Kelly's Lo-Fire Shino" confirmed 2026-07-05 against `glazy.org/recipes/64166` — this is a **public recipe by a different Glazy user** ("Irene Ives," titled "Raku - Kelly's Low-Fire Shino"), which Jake bookmarked on his account rather than adding as his own. Its page has no "Total base recipe" subtotal row at all, meaning every ingredient is base with no additions — this matches the `is_addition=false` default already in place, so no data change was needed there. Only `glazy_url` was attached (for provenance) via a direct DB update rather than the normal `import_glazy_recipe.py --force` re-import, since that script matches by name and would have created a duplicate row under Glazy's differently-worded title instead of updating this one.
- **Resolved:** "Forbes Midnight Blue" confirmed 2026-07-05 against `glazy.org/recipes/561455` — normal `import_glazy_recipe.py --force` re-import (published recipe, no auth needed). `is_addition` split applied: Ferro Frit 3110 ("Frit 3110")/Custer Feldspar/EP Kaolin are base, Lithium Carbonate/Copper Carbonate/Cobalt Carbonate/Bentonite are additions. New total $458.15/107 lb = $4.28/lb. This recipe calls for Custer Feldspar (discontinued, see above) and is locked on Glazy — Jake can't edit it there to note the substitute, so a `STAKEHOLDER NOTE` was added to `recipes.notes` here instead.
- **Resolved:** "Forbes Emerald Green Flash" confirmed 2026-07-05 against `glazy.org/recipes/836248` — Glazy's title differs from the spreadsheet name ("Emerald Green Copper Flash"), so the normal by-name match wouldn't have caught it; renamed to match Glazy's title (same precedent as Bill's Neon Blue) via a manual delete-and-reinsert rather than the script. Ingredients matched exactly except CMC Gum (2.0 vs. spreadsheet's 4.0 — expected "to taste" variance, not a discrepancy). `is_addition` split applied: Frit 3110 (from "Ferro Frit 3110")/Gerstley Borate/Frit 3134 (from "Ferro Frit 3134")/Nepheline Syenite are base, Copper Carbonate/CMC Gum are additions. New total $353.80/107 lb = $3.31/lb. Credited to Steven Forbes (per the Glazy page) in `recipes.notes`, same as Forbes Midnight Blue.
- **Resolved:** "Metallic Turquoise" (Gerstley Borate/Nepheline Syenite/Copper Carbonate, bulk-imported 2026-07-04) was **dropped entirely** 2026-07-05, per Jake — never added to Glazy, he doesn't recognize it, likely abandoned. Deleted from `recipes`/`recipe_ingredients` rather than left unconfirmed; no longer tracked here.
- **Resolved:** "Post Pac Man" confirmed 2026-07-05 against `glazy.org/recipes/836233` — a reformulated version ("Reformulated with gerstley borate per original recipe," per its own Glazy notes) that **drops Ball Clay entirely** compared to the original spreadsheet version (see the corrected Ball Clay item above). `is_addition` split applied: Gerstley Borate/Bone Ash/Nepheline Syenite are base, Copper Carbonate/Manganese Dioxide/Red Iron Oxide are additions. New total $575.75/114.70 lb = $5.02/lb. **Bug found and fixed here**: `import_glazy_recipe.py --force` was deleting-and-reinserting the whole `recipes` row without preserving `recipes.notes`, which silently wiped this recipe's existing thin-application `STAKEHOLDER NOTE` (Glazy has no equivalent field to read it back from) — restored by hand, and the script now carries `notes` forward across a `--force` re-import instead of clobbering it. Worth double-checking any other re-imported recipe that had a custom note added *before* its Glazy re-import (Copper Sand's note was added after, so unaffected; Reynolds Wrap never had one).
