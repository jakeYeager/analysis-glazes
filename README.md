# analysis-glazes

Cost analysis for a ceramics studio's glaze recipes and raw-material pricing. Started as a side-track inside a larger studio-operations analysis repo, then spun out on its own once it proved useful for a real decision: comparing the cost of two flux materials (Frit 3134 vs. Gerstley Borate) across two full glaze recipes, not just the one ingredient that changed.

## What's here

- `recipes.csv` — logged ingredient lists (material + amount by weight) for each glaze recipe tracked so far.
- `ingredient_prices.csv` — verified per-lb bulk pricing for each raw material, pulled from the supplier's live site (not estimated).
- `price_list_run_notes.md` — the methodology log: what was verified, how, what went wrong along the way, and a running checklist for future price-collection passes.
- `frit3134_vs_gerstley_borate_cost_comparison.md` (+ `.pdf`) — the first real deliverable: a full per-batch cost comparison between two recipes, showing why comparing a single ingredient's price in isolation can be misleading.
- `scripts/md2pdf.sh` — regenerates a shareable PDF from any Markdown report here (see below).

## Source systems

- **[Glazy](https://glazy.org)** — public community site for recording and sharing glaze recipes. Read-only, no login needed, no export/API found so far — recipes are transcribed by hand or read directly off the page.
- **IMCO** (a ceramics raw-materials supplier) — runs on **Square Online** (confirmed via page source), not Shopify. No public product/pricing API either way, so pricing comes from the on-site search + product pages.

## Key lessons learned (read before extending this)

- **Both source sites are JS-rendered SPAs.** A plain text-fetch tool (e.g. an LLM agent's basic web-fetch tool) cannot see their content at all — it returns an empty shell. This matters for two reasons: (1) collecting data requires real browser automation, not a text fetch, and (2) *verifying* someone else's claimed scrape also requires a tool that can render JS — a text-fetch tool coming back empty is not proof the original data was fabricated, only that the fetch tool couldn't see the page. Confirm with a real browser before concluding either way.
- **Bulk pricing is not linear or monotonic.** More than one material on this supplier's site has a smaller-quantity tier priced *higher per unit* than a larger one (e.g. a 25 lb tier costing more per lb than the 50 lb tier). Always pull every quantity tier for a product rather than assuming price scales predictably with size, and always use the cheapest available tier as "bulk," not just the largest.
- **Bag sizes aren't always round numbers.** One material's largest tier was 55.14 lb — a 25 kg bag converted to pounds, not a 50 lb bag. Don't assume every product follows the same 1/5/10/25/50 lb pattern.
- **A useful technique for full tier pricing:** a product page's weight/quantity `<select>` element can be enumerated with a short JavaScript snippet (via real browser automation) that sets each option, dispatches a `change` event, and reads back the updated price — this pulls the full tier table in one pass instead of clicking each option by hand.
- **Ingredient names don't always match between systems.** A recipe may name a material generically (e.g. "Bentonite," "Kaolin") while the supplier carries several grades at very different price points. Flag ambiguous matches rather than silently picking one.

## Regenerating a PDF

```
scripts/md2pdf.sh path/to/report.md
```

Renders the Markdown through an ephemeral `pandoc` (via `uv`, nothing installed permanently) into styled HTML, then prints it to PDF with headless Google Chrome. Requires Chrome to be installed locally; no other setup.

## Open items / natural next steps

- The Glazy/IMCO data collection so far has been done by driving a browser interactively (via an AI coding agent with browser automation). A real scraping script (e.g. Playwright/Puppeteer) would make future price-refresh runs cheaper and repeatable without a full agent session.
- No dated-snapshot convention exists yet for `ingredient_prices.csv` — prices will drift over time, and right now a re-run overwrites the previous numbers. Consider a `YYYY-MM-DD-ingredient_prices.csv` pattern once this becomes a recurring workflow.
- One material used in multiple recipes here (EP Kaolin) was found completely out of stock at the supplier as of the last price-collection run — worth rechecking before relying on any cost estimate that includes it.
