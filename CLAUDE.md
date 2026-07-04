# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing — see `README.md` for full context, source systems, and the key lessons learned so far. Read `README.md` and `price_list_run_notes.md` before doing new data collection here; both contain hard-won gotchas (non-monotonic bulk pricing, JS-rendered source sites, ingredient-name mismatches) that are easy to re-discover the hard way otherwise.

## Conventions

- **`recipes.csv` schema:** `recipe,glazy_url,material,amount,is_addition,notes`. One row per ingredient. `amount` is parts by weight as written in the source recipe (not necessarily normalized to 100). `is_addition` marks ingredients added on top of a 100-part base (colorants, opacifiers) vs. base ingredients.
- **`ingredient_prices.csv` schema:** `material_name,price,unit,bulk_price,bulk_unit,imco_url,match_confidence,notes`. `price`/`unit` is the smallest available quantity tier; `bulk_price`/`bulk_unit` is the *cheapest per-unit* tier available (usually but not always the largest quantity — verify, don't assume). `match_confidence` is `exact`, `fuzzy`, or `not_found`. Never fabricate a price — if a material can't be found or verified, leave the price fields empty and mark `not_found`, with a note on what was tried.
- **Verifying scraped data:** both Glazy and the IMCO supplier site are JS-rendered SPAs. Data collection and verification both require a tool that actually renders JavaScript (real browser automation), not a plain text-fetch tool — a text-fetch tool returning empty content proves nothing about whether a browser-collected claim is real.
- **New reports:** match the style of `frit3134_vs_gerstley_borate_cost_comparison.md` — a short framing paragraph explaining why the doc exists, tables over prose for numbers, and a "Source files referenced" list at the bottom.
- **Regenerating PDFs:** `scripts/md2pdf.sh path/to/report.md` — see `README.md`.
