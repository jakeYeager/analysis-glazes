# Frit 3134 vs. Gerstley Borate — Flux Cost Comparison

The studio's glaze tech traced Frogskin's glaze-fit problem ("running") to a flux substitution: the studio had been using Frit 3134 in place of the original recipe's Gerstley Borate, and a test batch mixed with real Gerstley Borate came out stable. Frogskin is a member favorite, and the glaze tech is getting pushback from members about it — this doc exists so the studio has real numbers to push back with (or concede to) rather than going on vibes, using real IMCO bulk pricing. It prices the Gerstley-Borate switch on its own, applies it to the glaze tech's new derivative recipe ("Giggin' for Salvation"), to Frogskin's own real-world bag economics, and — since a single-ingredient price swing can be a false positive if the rest of a recipe is cheap or expensive in the other direction — to the full per-batch cost of both recipes, ingredient by ingredient. Source recipes are logged in `recipes/compare_recipes.csv`; source prices in `ingredients/ingredient_prices.csv`.

**Naming note:** an internal chat thread (2026-07-04) refers to the substitute flux as "Gillespie Borate." No material by that name exists on Glazy or IMCO. "Giggin' for Salvation" (the glaze tech's recipe, same thread) lists "Ferro Frit 3134" in the role Frogskin's published formula gives to Gerstley Borate, and the glaze tech's own cost figures ("Frit 3134 is $135 for #50") match IMCO's Frit 3134 bulk price exactly. This doc treats "Gillespie Borate" as that thread's name for **Frit 3134** — flag if that's wrong.

## Verified bulk pricing (IMCO, 2026-07-04)

| Material | IMCO SKU | Bulk qty | Bulk price | Price per lb |
|---|---|---|---|---|
| Frit 3134 | 26802 | 50 lb | $135.00 | $2.70 |
| Gerstley Borate | 724 | 50 lb bag | $225.00 | $4.50 |

Both figures were pulled live from IMCO product pages (not just search-card ranges) and cross-checked against the glaze tech's own numbers — their $135/#50 and $225/bag match exactly. **Gerstley Borate costs $1.80/lb more than Frit 3134 at bulk (50 lb) pricing — a 67% premium.**

## Applied to "Giggin' for Salvation"

The glaze tech's recipe (no Glazy link given, logged from a chat message) calls for Frit 3134 at 25 parts per 100-part base, with total batch weight (including the four "+" colorant/additive lines) at 115.5 parts. Holding the flux quantity constant and swapping in Gerstley Borate 1:1 by weight (a cost-only substitution — whether the recipe needs re-balancing to hit the same chemistry at a different Gerstley amount is a reformulation question for the glaze tech, not addressed here):

| Scenario | Flux | Qty (parts = lb, at recipe ratio) | Flux cost | Δ vs. current |
|---|---|---|---|---|
| Current | Frit 3134 | 25 | $67.50 | — |
| Switched | Gerstley Borate | 25 | $112.50 | +$45.00 (+67%) |

Read "25 parts" as whatever unit the studio actually batches this recipe in (e.g. a 115.5 lb batch uses 25 lb of flux); scale linearly for the real batch size.

**Why a flux-only comparison isn't the whole story:** looking at just one ingredient can be misleading — a big swing on a cheap-by-volume material can look scary while contributing little to the total, and a small swing on a heavily-used material can hide a much bigger real cost. The full recipe breakdown below prices every ingredient in both recipes, not just the flux, so the totals reflect what each glaze actually costs to mix.

## Full recipe cost, every ingredient — Giggin' for Salvation vs. Frogskin

All prices are IMCO's best available bulk rate (the largest quantity tier for each material, which is not always 50 lb — see table). Amounts are read directly off each recipe as pounds, i.e. this prices a "107 lb batch" of Frogskin and a "115.5 lb batch" of Giggin' for Salvation; scale both figures by the same factor for the studio's actual batch size and the comparison holds.

### Frogskin (glazy.org/recipes/292795, with Gerstley Borate — the formula members know)

| Material | Amount (lb) | Bulk rate | $/lb | Cost |
|---|---|---|---|---|
| Silica | 26.00 | $25.00 / 50 lb | $0.50 | $13.00 |
| Gerstley Borate | 22.00 | $225.00 / 50 lb | $4.50 | $99.00 |
| Nepheline Syenite | 22.00 | $32.00 / 50 lb | $0.64 | $14.08 |
| Potash Feldspar | 22.00 | $56.00 / 55.14 lb | $1.02 | $22.34 |
| Copper Carbonate | 4.00 | $600.00 / 50 lb | $12.00 | $48.00 |
| EP Kaolin | 3.00 | $400.00 / 50 lb | $8.00 | $24.00 |
| Red Iron Oxide | 3.00 | $375.00 / 100 lb | $3.75 | $11.25 |
| Wollastonite | 3.00 | $30.00 / 50 lb | $0.60 | $1.80 |
| Titanium Dioxide | 2.00 | $231.00 / 50 lb | $4.62 | $9.24 |
| **Total** | **107.00 lb** | | | **$242.71** |

**= $2.27/lb of mixed glaze.**

### Giggin' for Salvation (the glaze tech's recipe, with Frit 3134)

| Material | Amount (lb) | Bulk rate | $/lb | Cost |
|---|---|---|---|---|
| Silica | 32.50 | $25.00 / 50 lb | $0.50 | $16.25 |
| Frit 3134 | 25.00 | $135.00 / 50 lb | $2.70 | $67.50 |
| Nepheline Syenite | 20.00 | $32.00 / 50 lb | $0.64 | $12.80 |
| EP Kaolin | 12.50 | $400.00 / 50 lb | $8.00 | $100.00 |
| Whiting | 10.00 | $15.00 / 50 lb | $0.30 | $3.00 |
| Red Iron Oxide | 10.00 | $375.00 / 100 lb | $3.75 | $37.50 |
| Titanium Dioxide | 2.50 | $231.00 / 50 lb | $4.62 | $11.55 |
| Bentonite | 2.00 | $33.50 / 50 lb | $0.67 | $1.34 |
| Copper Carbonate | 1.00 | $600.00 / 50 lb | $12.00 | $12.00 |
| **Total** | **115.50 lb** | | | **$261.94** |

**= $2.27/lb of mixed glaze.**

### The headline: they cost almost exactly the same per lb

| | Total (as-written batch) | $/lb |
|---|---|---|
| Frogskin (Gerstley Borate) | $242.71 / 107 lb | $2.27 |
| Giggin' for Salvation (Frit 3134) | $261.94 / 115.5 lb | $2.27 |
| Frogskin (Frit 3134, the recent substitute version) | $203.11 / 107 lb | $1.90 |

This is exactly the false-positive risk flagged going in: Frit 3134 is $1.80/lb cheaper than Gerstley Borate, so "Giggin' for Salvation uses the cheap flux" sounds like it should be the budget option — but Giggin' for Salvation also carries proportionally more EP Kaolin (12.5% vs. Frogskin's 3%) and Red Iron Oxide (10% vs. 3%), both expensive per lb ($8.00 and $3.75), which erases essentially all of the flux savings. **Reverting Frogskin to Gerstley Borate ($2.27/lb) costs about the same per lb as the glaze tech's new Giggin' for Salvation recipe ($2.27/lb) — cost alone doesn't favor either one over the other.** The real cost story is entirely about the Frit-3134-substitute version of Frogskin ($1.90/lb) being unusually cheap, not about Gerstley Borate being unusually expensive.

**Operational flag, not a cost issue:** EP Kaolin (used in both recipes) is currently **out of stock in every size** at IMCO. This affects both Frogskin and Giggin' for Salvation regardless of which flux is used, and is a bigger near-term problem than the Gerstley-vs-Frit cost question — worth raising with the glaze tech separately.

## Cross-check against Frogskin's real bag economics

This is the more grounded number, since it needs no assumption about batch size. The glaze tech: "one bag [of Gerstley] will yield 14 batches of Frogskin." Both Frit 3134 and Gerstley Borate are sold by IMCO in the same 50 lb bag size, so swapping a bag of one for a bag of the other, at the same weight, costs:

| | Per 50 lb bag | Per batch (÷14) |
|---|---|---|
| Frit 3134 | $135.00 | $9.64 |
| Gerstley Borate | $225.00 | $16.07 |
| **Difference** | **+$90.00** | **+$6.43** |

**Switching Frogskin's flux back to Gerstley Borate costs about $6.43 more per batch, or $90 more per 50 lb bag.**

## Decided / deprioritized items

- **Bentonite grade:** keeping the generic 325 Mesh Bentonite ($33.50/50 lb) as the priced material for "Giggin' for Salvation," per Jake, 2026-07-04. Not the premium Volclay API-grade.  
- **Commercial-glaze benchmark:** Jake's original ask to flag it "if we are way above a comparable commercial dry weight glaze" per-lb cost — deprioritized per Jake, 2026-07-04. Would need a quote from a commercial glaze supplier (e.g. Amaco, Spectrum) for a comparable cone 5–6 semi-glossy dry glaze; not sourced.  

## Source files referenced

- `recipes/compare_recipes.csv` — Frogskin and "Giggin' for Salvation" ingredient lists  
- `ingredients/ingredient_prices.csv` — verified IMCO pricing for all materials in both recipes  
- `docs/archive/price_list_run_notes.md` — pricing methodology and verification history (archived; current workflow is in `.claude/CLAUDE.md`)  
- Glazy recipe: <https://glazy.org/recipes/292795> (Frogskin)  
- Internal chat thread, 2026-07-04 (studio glaze tech / Jake), screenshot only — not machine-readable, transcribed into `recipes.csv`  
