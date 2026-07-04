# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing — see `README.md` . Read `docs/price_list_run_notes.md` for full context, source systems, and the key lessons learned so far, before doing new data collection work; it contains hard-won gotchas (non-monotonic bulk pricing, JS-rendered source sites, ingredient-name mismatches) that are easy to re-discover the hard way otherwise.

## Current workflow notes

- **`recipes/compare_recipes.csv` schema:** `recipe,glazy_url,material,amount,is_addition,notes`. One row per ingredient. `amount` is parts by weight as written in the source recipe. `is_addition` marks ingredients added on top of a base glaze ingredients.
- **`ingredients/ingredient_prices.csv` schema:** `material_name,price,unit,bulk_price,bulk_unit,imco_url,match_confidence,notes`. `price`/`unit` is the smallest available quantity tier; `bulk_price`/`bulk_unit` is the *cheapest per-unit* tier available (usually but not always the largest quantity — verify, don't assume). `match_confidence` is `exact`, `fuzzy`, or `not_found`. Never fabricate a price — if a material can't be found or verified, leave the price fields empty and mark `not_found`, with a note on what was tried.
- **Verifying scraped data:** both Glazy and the IMCO supplier site are JS-rendered SPAs. Data collection and verification both require a tool that actually renders JavaScript (real browser automation), not a plain text-fetch tool — a text-fetch tool returning empty content proves nothing about whether a browser-collected claim is real.

## Open items / natural next steps

- The Glazy/IMCO data collection so far has been done by driving a browser interactively (via an AI coding agent with browser automation). A real scraping script (e.g. Playwright/Puppeteer) would make future price-refresh runs cheaper and repeatable without a full agent session.
- No dated-snapshot convention exists yet for price CSVs — prices will drift over time, and right now a re-run overwrites the previous numbers. Consider a `YYYY-MM-DD-ingredient_prices.csv` pattern once this becomes a recurring workflow.
- One material used in multiple recipes here (EP Kaolin) was found completely out of stock at the supplier as of the last price-collection run — worth rechecking before relying on any cost estimate that includes it.
