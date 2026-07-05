# Glaze Price Summary

| | |
|---|---|
| **Date** | 2026-07-04 |
| **Last Updated** | 2026-07-04 |
| **Document Version** | 1.0 |
| **Generation Model** | Claude Sonnet 5 |
| **Author** | Jake Yeager |

This is the current per-lb cost of every glaze recipe tracked in `db/glazes.db`, regenerated directly from it via `scripts/generate_price_summary.py` — a quick reference for pricing/rotation decisions, not a one-off analysis. Regenerate it (and re-run `scripts/price_batch.py` first if you want fresher prices) before sharing an updated copy with stakeholders. "Last Priced" is the oldest `last_verified` date among a recipe's ingredients — the number is only as fresh as its stalest ingredient. A recipe with unpriced ingredients shows its total computed from confirmed ingredients only; it is not a guess, but it is incomplete. **`$/lb` is mixing cost, not per-piece cost** — it says nothing about how thickly a glaze gets applied, so a thin-coat glaze and a thick-dipped one at the same `$/lb` do not cost the same to actually use. A recipe flagged "see notes" below has a specific caveat about this worth reading before comparing it to others on `$/lb` alone.

## Mid Fire glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Frogskin | $2.27 | 107.00 | $242.71 | 2026-07-04 |  |
| Giggin' for Salvation | $2.27 | 115.50 | $261.94 | 2026-07-04 |  |

## Raku glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Ballingham Black Luster | $5.24 | 133.50 | $700.07 | 2026-07-04 |  |
| Bill's Neon Blue 2024 | $4.53 | 109.00 | $493.97 | 2026-07-04 |  |
| Blue Moon | $7.03 | 102.00 | $717.27 | 2026-07-04 |  |
| Clear Crackle | $3.73 | 100.00 | $372.80 | 2026-07-04 |  |
| Copper Sand | $5.77 | 113.75 | $656.00 | 2026-07-04 |  |
| Del Favero Luster | $3.89 | 102.00 | $396.80 | 2026-07-04 |  |
| Emerald Green Copper Flash | $3.43 | 109.00 | $373.80 | 2026-07-04 |  |
| Ferguson White Crackle | $6.06 | 100.00 | $606.30 | 2026-07-04 |  |
| Fern Green Crackle | $3.78 | 100.50 | $379.70 | 2026-07-04 |  |
| Forbes Midnight Blue | $4.39 | 109.00 | $478.15 | 2026-07-04 |  |
| Hasselle Copper Matte | $11.43 | 103.00 | $1176.81 | 2026-07-04 | see notes (db/glazes.db) -- affects how to read this $/lb figure |
| Kelly's Lo-Fire Shino | $6.69 | 106.34 | $710.90 | 2026-07-04 |  |
| Looks Expensive | $4.63 | 106.30 | $492.57 | 2026-07-04 |  |
| Marble White Crackle | $4.72 | 110.00 | $519.20 | 2026-07-04 |  |
| Metallic Turquoise | $4.34 | 108.00 | $468.80 | 2026-07-04 |  |
| Post Pac Man | $5.02 | 114.70 | $575.75 | 2026-07-04 |  |
| Reynolds Wrap | $4.08 | 114.00 | $465.26 | 2026-07-04 |  |
| Sky Blue Crackle | $3.85 | 100.50 | $386.80 | 2026-07-04 |  |

## Source files referenced

- `db/glazes.db` — recipes, materials, and pricing (see `.claude/CLAUDE.md` for the full schema)  
- `reports/glaze_price_summary.csv` — this same data in spreadsheet form  
