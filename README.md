# analysis-glazes

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing. Started as a side-track inside a larger studio-operations analysis repo, then spun out on its own once it proved useful for a real decision: comparing the cost of two flux materials (Frit 3134 vs. Gerstley Borate) across two full glaze recipes, not just the one ingredient that changed.

## What's here

Recipes, materials, and prices live in `db/glazes.db` (SQLite, gitignored — rebuild it with `python3 scripts/db_build.py`). See `.claude/CLAUDE.md` for the full workflow.

- `db/schema.sql` — the database schema (tracked; the `.db` file itself isn't).
- `recipes/` — `recipe_metadata.csv` (one row per recipe) and `compare_recipes.csv` (one row per ingredient): git-tracked checkpoints of the DB's recipe data, refreshed via `scripts/db_export.py`.
- `ingredients/` — `ingredient_prices.csv` (verified per-lb bulk pricing, pulled from the supplier's live site, not estimated) and `name_candidates_log.csv`: git-tracked checkpoints of the DB's material data.
- `docs/archive/price_list_run_notes.md` — historical methodology log from before the workflow was automated; kept for context, not required reading (see `.claude/CLAUDE.md`).
- `reports/` (+ `/pdfs/`) — report deliverables like full per-batch cost comparison between two recipes.
- `scripts/` — the automated workflow: fetching recipes, pricing materials, and syncing the DB with its checkpoint CSVs.

## Source systems

- **[Glazy](https://glazy.org)** — public community site for recording and sharing glaze recipes. Read-only, no login needed for published recipes, no export/API found so far — recipes are transcribed by hand or read directly off the page. Unpublished recipes are gated behind the owner's login session (`import_glazy_recipe.py`'s headless fetch returns "Recipe does not exist" for one) — those need a logged-in browser session to view/collect instead.
- **IMCO** (a ceramics raw-materials supplier) — runs on **Square Online**. No public product/pricing API either way, so pricing comes from the on-site search + product pages.

## Reference materials (not scraped/imported, background only)

- [**"15 Raku Glazes"** (Ceramic Arts Network)](https://ceramicartsnetwork.org/docs/default-source/uploadedfiles/wp-content/uploads/2015/08/15rakuglazes.pdf?sfvrsn=992b3959_0) — noted 2026-07-05. Published/popular versions of several raku glazes; useful as a comparison point when a studio recipe (e.g. a personal unpublished Glazy variant) deviates from the well-known published version and might warrant tracking as two separate recipes rather than one.
