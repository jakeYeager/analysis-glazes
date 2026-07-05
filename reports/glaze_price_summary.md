# Glaze Price Summary

| | |
|---|---|
| **Date** | 2026-07-04 |
| **Last Updated** | 2026-07-04 |
| **Document Version** | 1.0 |
| **Generation Model** | Claude Sonnet 5 |
| **Author** | Jake Yeager |

This is the current per-lb cost of every glaze recipe tracked in `db/glazes.db`, regenerated directly from it via `scripts/generate_price_summary.py` — a quick reference for pricing/rotation decisions, not a one-off analysis. Regenerate it (and re-run `scripts/price_batch.py` first if you want fresher prices) before sharing an updated copy with stakeholders. "Last Priced" is the oldest `last_verified` date among a recipe's ingredients — the number is only as fresh as its stalest ingredient. A recipe with unpriced ingredients shows its total computed from confirmed ingredients only; it is not a guess, but it is incomplete.

## Mid Fire glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Frogskin | $2.27 | 107.00 | $242.71 | 2026-07-04 |  |
| Giggin' for Salvation | $2.27 | 115.50 | $261.94 | 2026-07-04 |  |

## Raku glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Looks Expensive | $4.63 | 106.30 | $492.57 | 2026-07-04 |  |

## Source files referenced

- `db/glazes.db` — recipes, materials, and pricing (see `.claude/CLAUDE.md` for the full schema)  
- `reports/glaze_price_summary.csv` — this same data in spreadsheet form  
