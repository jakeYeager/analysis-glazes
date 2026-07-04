# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing — see `README.md` . Read `docs/price_list_run_notes.md` for full context, source systems, and the key lessons learned so far, before doing new data collection work; it contains hard-won gotchas (non-monotonic bulk pricing, JS-rendered source sites, ingredient-name mismatches) that are easy to re-discover the hard way otherwise.

## Current workflow notes

- **`recipes/compare_recipes.csv` schema:** `recipe,glazy_url,material,amount,is_addition,notes`. One row per ingredient. `amount` is parts by weight as written in the source recipe. `is_addition` marks ingredients added on top of a base glaze ingredients.
- **`ingredients/ingredient_prices.csv` schema:** `material_name,price,unit,bulk_price,bulk_unit,imco_url,match_confidence,notes,last_verified,glazy_material_url`. `price`/`unit` is the smallest available quantity tier; `bulk_price`/`bulk_unit` is the *cheapest per-unit* tier available (usually but not always the largest quantity — verify, don't assume). `match_confidence` is `exact`, `fuzzy`, or `not_found`. Never fabricate a price — if a material can't be found or verified, leave the price fields empty and mark `not_found`, with a note on what was tried. `last_verified` (date) drives the staleness check in `scripts/price_batch.py`; `glazy_material_url` is cached once discovered so future runs skip re-crawling the recipe page.
- **Verifying scraped data:** both Glazy and the IMCO supplier site are JS-rendered SPAs. Data collection and verification both require a tool that actually renders JavaScript (real browser automation), not a plain text-fetch tool — a text-fetch tool returning empty content proves nothing about whether a browser-collected claim is real.

## Automated pricing workflow

Price refreshing and batch pricing no longer require a full interactive agent session — three Playwright-Python scripts in `scripts/` handle it, run via `uv run --with playwright <script>`:

- **`scripts/scrape_imco_price.py <imco_url>`** — pulls the full weight-tier price table off one IMCO product page, headless.
- **`scripts/find_material_candidates.py <recipe_glazy_url> "<material name>"`** — for a `fuzzy`/`not_found` material, scrapes Glazy's alternate-name list for that material and tries each against IMCO search, logging candidates to `ingredients/name_candidates_log.csv`. Never writes to `ingredient_prices.csv` directly — a human still confirms fuzzy matches, per the never-fabricate rule above.
- **`scripts/price_batch.py "<recipe name>"`** — the orchestrator. Prices every ingredient in a recipe from `recipes/compare_recipes.csv`, using the cached price if `last_verified` is within `STALENESS_DAYS` (90, set at the top of the script), otherwise refreshing it via `scrape_imco_price.py`. Unresolved materials trigger `find_material_candidates.py` and are excluded from the total rather than priced with a guess. Any refresh rewrites `ingredients/ingredient_prices.csv` in place and archives a dated copy to `ingredients/snapshots/`.

**One-time setup:** Playwright's browser binary is a real local install, not ephemeral like the rest of this project's tooling — run `uv run --with playwright playwright install chromium` once before first use.

## Open items / natural next steps

- One material used in multiple recipes here (EP Kaolin) was found completely out of stock at the supplier as of the last price-collection run — worth rechecking before relying on any cost estimate that includes it.
- The scraping scripts were verified end-to-end against live Glazy/IMCO pages on 2026-07-04 (see `docs/price_list_run_notes.md` Run 4). Two real gotchas worth knowing if you touch these scripts: (1) `wait_until="networkidle"` hangs on IMCO's Square Online pages (persistent background connections never go idle) — use `"load"` + a short fixed wait instead; (2) IMCO's search doesn't return zero results for a bogus query, it falls back to unrelated "trending" products, so `find_material_candidates.py` filters matches by word-overlap with the search term rather than trusting raw hit counts.
