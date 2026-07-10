# Glaze Price Summary

| | |
|---|---|
| **Date** | 2026-07-10 |
| **Last Updated** | 2026-07-10 |
| **Document Version** | 2.1 |
| **Generation Model** | Claude Sonnet 5 |
| **Author** | Jake Yeager |

This is the current per-lb cost of every glaze recipe tracked in `db/glazes.db`, regenerated directly from it via `scripts/generate_price_summary.py` — a quick reference for pricing/rotation decisions, not a one-off analysis. Regenerate it (and re-run `scripts/price_batch.py` first if you want fresher prices) before sharing an updated copy with stakeholders. "Last Priced" is the oldest `last_verified` date among a recipe's ingredients — the number is only as fresh as its stalest ingredient. A recipe with unpriced ingredients shows its total computed from confirmed ingredients only; it is not a guess, but it is incomplete. Base-glaze materials (frits, feldspars, clays, silica) are costed at the cheapest bulk rate, since that's realistically how they're bought; colorants, opacifiers, and Lithium Carbonate are costed at a smaller 10lb rate instead, since those are typically bought in much smaller quantities than a full bag. **`$/lb` is mixing cost, not per-piece cost** — it says nothing about how thickly a glaze gets applied, so a thin-coat glaze and a thick-dipped one at the same `$/lb` do not cost the same to actually use. A recipe flagged "see Recipe Notes below" has a specific caveat about this worth reading before comparing it to others on `$/lb` alone — full text of each is in the "Recipe Notes" section below the price tables.

## Mid Fire glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Buttercup Yellow | $3.63 | 114.00 | $413.34 | 2026-07-04 |  |
| Falls Creek Shino | $5.89 | 106.70 | $628.42 | 2026-07-04 |  |
| Frogskin | $2.40 | 107.00 | $257.22 | 2026-07-04 |  |
| Giggin' for Salvation | $2.47 | 115.50 | $285.57 | 2026-07-04 |  |

## Raku glazes

| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |
|---|---|---|---|---|---|
| Ballingham Black Luster | $5.70 | 133.50 | $760.96 | 2026-07-04 |  |
| Bill's Neon Blue 2025 | $5.85 | 107.00 | $626.23 | 2026-07-04 |  |
| Clear Crackle | $3.73 | 100.00 | $372.80 | 2026-07-04 |  |
| Copper Sand | $6.03 | 113.75 | $686.25 | 2026-07-04 | see Recipe Notes below -- affects how to read this $/lb figure |
| Del Favero Luster | $3.92 | 102.00 | $399.80 | 2026-07-04 |  |
| Ferguson's White Crackle | $6.37 | 100.00 | $636.60 | 2026-07-04 |  |
| Fern Green Crackle | $3.79 | 100.50 | $380.80 | 2026-07-04 |  |
| Forbes Emerald Green Flash | $3.47 | 107.00 | $371.30 | 2026-07-04 |  |
| Forbes Midnight Blue | $5.13 | 107.00 | $548.43 | 2026-07-04 | see Recipe Notes below -- affects how to read this $/lb figure |
| Hasselle Copper Matte | $13.69 | 103.00 | $1409.65 | 2026-07-04 | see Recipe Notes below -- affects how to read this $/lb figure |
| Kelly's Lo-Fire Shino | $10.11 | 106.34 | $1075.10 | 2026-07-04 | reference only -- not in active rotation, see Recipe Notes below |
| Looks Expensive | $6.08 | 106.30 | $646.03 | 2026-07-04 |  |
| Marble White Crackle | $4.93 | 110.00 | $542.00 | 2026-07-04 |  |
| Post Pac Man | $5.21 | 114.70 | $597.74 | 2026-07-04 | see Recipe Notes below -- affects how to read this $/lb figure |
| Reynolds Wrap | $4.24 | 114.00 | $483.82 | 2026-07-04 |  |
| Sky Blue Crackle | $3.88 | 100.50 | $390.30 | 2026-07-04 |  |

## Recipe Notes

Full text of every note flagged "see Recipe Notes below" in the tables above.

**Copper Sand** — STAKEHOLDER NOTE (affects how to read $/lb): applied slightly thicker than Hasselle Copper Matte, but still just one coat needed. Per Jake, 2026-07-04: this $/lb figure overstates real per-piece cost relative to a glaze needing multiple coats/dips -- do not compare this recipe to others on $/lb alone without accounting for coat thickness.

**Forbes Midnight Blue** — STAKEHOLDER NOTE: this recipe calls for Custer Feldspar, which is discontinued (extinct as of 2024) and cannot be purchased new. Jake's Glazy recipe is locked and can't be edited to reflect the substitute. Cost here is computed using the G-200 (EU) Potassium Feldspar substitute -- see that material's notes in db/glazes.db. Chemistry isn't identical (lower iron, higher purity), so this recipe may need reformulation to hit its original fired result; this cost analysis doesn't address that.

**Hasselle Copper Matte** — STAKEHOLDER NOTE (affects how to read $/lb): applied as a very thin coat -- just enough Ball Clay to make the Black Copper Oxide stick. The high copper density/availability at the surface is what produces the dramatic flame-reduction effects; that same density is what makes it one of the most expensive recipes here per pound. Per Jake, 2026-07-04: this $/lb figure overstates real per-piece cost since so little material is used per application -- do not compare this recipe to others on $/lb alone without accounting for coat thickness.

**Kelly's Lo-Fire Shino** — REFERENCE ONLY (not actively mixed): Jake's personal preference -- nobody else in the studio likes this glaze. Confirmed 2026-07-04. Kept in the file for reference; not part of active rotation/production. is_addition confirmed 2026-07-05: this public recipe (by Irene Ives, glazy.org/recipes/64166, titled 'Raku - Kelly's Low-Fire Shino') has no 'Total base recipe' subtotal row, meaning every ingredient is base -- matches the false default already in place, so no is_addition change needed. Jake bookmarked this recipe on his own account rather than adding it to his profile as an authored recipe, since it isn't his.

**Post Pac Man** — STAKEHOLDER NOTE (affects how to read $/lb): applied slightly thicker than Hasselle Copper Matte, but still just one coat needed. Per Jake, 2026-07-04: this $/lb figure overstates real per-piece cost relative to a glaze needing multiple coats/dips -- do not compare this recipe to others on $/lb alone without accounting for coat thickness.

## Source files referenced

- `db/glazes.db` — recipes, materials, and pricing (see `.claude/CLAUDE.md` for the full schema)  
- `reports/glaze_price_summary.csv` — this same data in spreadsheet form  
