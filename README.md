# analysis-glazes

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing. Started as a side-track inside a larger studio-operations analysis repo, then spun out on its own once it proved useful for a real decision: comparing the cost of two flux materials (Frit 3134 vs. Gerstley Borate) across two full glaze recipes, not just the one ingredient that changed.

## What's here

- `recipes/` — logged ingredient lists (material + amount by weight) for each glaze recipe tracked so far.
- `ingredients/` — verified per-lb bulk pricing for each raw material, pulled from the supplier's live site (not estimated).
- `docs/price_list_run_notes.md` — first-pass methodology log: what was verified, how, what went wrong along the way, and a running checklist for future price-collection passes.
- `reports/` (+ `/pdf/`) — report deliverables like full per-batch cost comparison between two recipes.
- `scripts/` — utilitiy scripts like regenerate a shareable PDF from any Markdown report here.

## Source systems

- **[Glazy](https://glazy.org)** — public community site for recording and sharing glaze recipes. Read-only, no login needed, no export/API found so far — recipes are transcribed by hand or read directly off the page.
- **IMCO** (a ceramics raw-materials supplier) — runs on **Square Online**. No public product/pricing API either way, so pricing comes from the on-site search + product pages.
