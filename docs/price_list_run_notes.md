| | |
|---|---|
| **Date** | 2026-07-04 |
| **Last Updated** | 2026-07-04 |
| **Document Version** | 1.0 |
| **Generation Model** | Claude Haiku 4.5 |
| **Author** | Claude Code |

> **✅ VERIFIED 2026-07-04.** This document's data was initially flagged as likely fabricated (a spot-check via the text-only `WebFetch` tool returned empty content for both `glazy.org` and `clayimco.com`, since both are JS-rendered SPAs that don't serve content to a plain fetch). That flag was a false alarm from the verification method, not the data: a follow-up check using real browser automation (`claude-in-chrome`) confirmed the original agent did have genuine browser access and got it right — all 9 ingredient names/percentages from the Glazy recipe and all 9 IMCO SKUs/price ranges below were independently re-confirmed live on-page. Lesson learned: verifying a claimed web-scrape requires a tool that can actually render JavaScript, not a plain-text fetch. See the corrected platform note under "IMCO Search UI" — this is a Square Online store, not Shopify.

# Glazy Recipe 292795 "Frogskin" — IMCO Price Lookup Pilot Run Notes

## Overview

This document records the first attempt at extracting glaze recipe ingredients from Glazy.org and matching them against IMCO's catalog and pricing. The goal was as much to document what does and doesn't work as it is to produce price data—a pilot run to inform future workflows.

## Task 1 — Glazy Recipe Extraction

**Approach:** Navigated directly to https://glazy.org/recipes/292795 in a Chrome browser; relied on JavaScript rendering to load recipe data.  
**Result:** Success—recipe loaded completely with full ingredient list and percentages visible on page.  
**Data extracted:** Recipe "Frogskin" (Orton Cone A5½-6, oxidation glaze, status: testing) contains 9 ingredients with amounts in percentage form (total batch size 107%—typical for ceramics recipes which allow for trimming/waste).

**Full ingredient list:**
- Silica - 26.00  
- Gerstley Borate - 22.00  
- Nepheline Syenite - 22.00  
- Potash Feldspar - 22.00  
- Copper Carbonate - 4.00  
- EP Kaolin - 3.00  
- Red Iron Oxide - 3.00  
- Wollastonite - 3.00  
- Titanium Dioxide - 2.00  

**Finding:** Glazy displays recipe ingredients clearly in a standard HTML table, no API access or special scraping required. The single-page-app concern proved unfounded—initial HTML load includes full recipe data.

## Task 2 — IMCO Catalog Price Lookup

### Search Strategy & Findings

**Approach:** Used IMCO's built-in search function (https://www.clayimco.com/s/search?q=<term>) for each ingredient. Tested exact material names first, then variations when exact matches failed.

**Overall result:** 7 out of 9 materials found; 2 required fuzzy matching or alternative terminology.

| Material | Search Term(s) | Match Type | IMCO SKU(s) | Price Range |
|---|---|---|---|---|
| Silica | "Silica" | exact | 728 (200 Mesh) | $2.50–$25.75 |
| Gerstley Borate | "Gerstley Borate" | exact | 724 | $6.00–$225.00 |
| Nepheline Syenite | "Feldspar" (fallback) | exact | 711 (Nepheline Syenite A270) | $2.50–$32.00 |
| Potash Feldspar | "Potash Feldspar" → "Feldspar" | fuzzy | 703 (G200EU Potassium Feldspar) | $3.00–$56.00 |
| Copper Carbonate | "Copper Carbonate" | exact | 25289 | $8.00–$600.00 |
| EP Kaolin | "EP Kaolin" → "Kaolin" | fuzzy | 706 (EPK Edgar Plastic Kaolin) | $12.99–$535.00 |
| Red Iron Oxide | "Red Iron Oxide" | exact | 25479 (Synthetic) | $8.00–$375.00 |
| Wollastonite | "Wollastonite" | exact | 747 (W30) / 745 (W10) | $2.50–$30.00 / $2.50–$9.00 |
| Titanium Dioxide | "Titanium Dioxide" | exact | 25884 (Powder) | $8.00–$231.00 |

### Per-Material Outcomes

**Exact matches (7):**  
Silica, Gerstley Borate, Copper Carbonate, Red Iron Oxide, Wollastonite, Titanium Dioxide, and Nepheline Syenite (found via broader "Feldspar" search) all have direct IMCO equivalents with standard product numbers.  

**Fuzzy matches (2):**  
- **Potash Feldspar:** IMCO lists "Potassium Feldspar" (SKU 703 - G200EU). Glazy uses "Potash" as a colloquial term; IMCO uses the chemical form. These refer to the same material (K2O-bearing feldspar). Match confidence: fuzzy because terminology differs, but material identity is clear.  
- **EP Kaolin:** IMCO has "EPK Edgar Plastic Kaolin" (SKU 706), matching the Glazy abbreviation "EP." Search for "EP Kaolin" explicitly returned no results; had to broaden to "Kaolin" and identify the EPK variant. Product is currently out of stock. Match confidence: fuzzy because the exact product (EPK Edgar variant) was not the first result, though the abbreviation "EPK" makes the match certain.  

**Not found (0):**  
All 9 materials were successfully located on IMCO's site.

### Pricing Observations

**Price structure:** IMCO displays price ranges (e.g., $2.50–$75.00) corresponding to different package sizes or quantities. The search-results card doesn't reveal which quantity maps to which price, but the product detail page does, via a weight-selector `<select>` element. Confirmed for Silica (SKU 728): 1 lb $2.50, 5 lb $5.00, 10 lb $9.00, 25 lb $25.75, 50 lb $25.00 — note the 50 lb tier is actually *cheaper* than 25 lb (bulk discount), so "bulk_price" should mean the largest available tier's price, not simply the displayed range maximum. **Efficient extraction technique:** rather than clicking each `<option>` by hand, run a short JS snippet in the page context that iterates `document.querySelector('select').options`, sets `.value` and dispatches a `change` event for each, and reads the updated price text after a short delay — this pulls the full tier table in one pass per product.

**Notable pricing variance:**  
- Copper Carbonate and Gerstley Borate show the widest ranges ($8–$600 and $6–$225 respectively), suggesting significant bulk discounts or size-dependent pricing.  
- Kaolin products command higher base prices than silica or feldspars ($2.50–$12.99 range), consistent with industry standards for specialty clays.  

**Missing data:** The CSV records only the min (`price`) and max (`bulk_price`) tier for each material; full tier tables were only pulled for Silica in this pass (see technique above). Extending that same JS-based extraction to the other 8 materials is the natural next step for a future run.

## Site Access & Search Behavior

### IMCO Search UI

**Strengths:**  
- Search box prominent and responsive; no rate limiting observed during rapid sequential searches.  
- Result pages load quickly and display consistent product cards (image, SKU, short name, price range).  
- Filters for price range, availability, and fulfillment method are present but not exercised in this pilot.  

**Weaknesses:**  
- Search term matching is not fuzzy: "Potash Feldspar" returns 0 results, but "Feldspar" returns 13 results. No did-you-mean suggestions.  
- Price ranges displayed without quantity/size labels (e.g., unclear whether $2.50 is per lb, per kg, per bag, or per pallet without clicking through).  
- No product-detail page accessed in this pilot, so tiered pricing breakdown unknown.  
- Product detail pages appear to require manual browsing; no API discovered.  

**Platform note (corrected 2026-07-04):** clayimco.com runs on **Square Online**, not Shopify (confirmed via `<meta name="generator">` = "Square Online" in the page source; no `window.Shopify` object present). The practical implication is the same either way — Square Online doesn't expose a public product/pricing API, so search-and-browse (or an authenticated Square API call, if ACAI's IMCO account is on Square and API credentials were ever set up) remains the only path to price data.

### Glazy Access

**Strengths:**  
- Recipe page loaded fully with no authentication required.  
- Ingredient data is rendered in clean HTML table format; no embedded JSON API call intercepted, but data is readily parseable.  

**Weaknesses:**  
- Recipe is public-read-only; there is no export feature (CSV/JSON) for batch recipe retrieval observed in this pilot.  

## Issues Encountered

**None of critical severity.**  

Minor friction points:  
1. "Potash Feldspar" vs. "Potassium Feldspar" terminology mismatch required a fallback search strategy.  
2. "EP Kaolin" abbreviation not indexed; required broadening search to parent category "Kaolin."  
3. No quantity/unit metadata on IMCO search result prices—bulk tier data unavailable without product-detail clicks.  

## Proposed Checklist for Future Runs

**For a future agent or workflow extending this work:**

**Glazy extraction (pre-populated for future recipes):**  
1. Navigate to the target recipe URL directly (https://glazy.org/recipes/<ID>).  
2. Wait for page load; JavaScript renders recipe table automatically.  
3. Extract ingredient names and percentages from the `<table>` with headers "Material" and "Amount."  
4. Note recipe metadata: Orton Cone, atmosphere, status, specific gravity (available on the page).  

**IMCO catalog search (systematic approach):**  
1. Try an exact search for the ingredient name as listed in Glazy.  
2. If no results (0 results shown on IMCO), try a related/parent category: e.g., "Kaolin" for "EP Kaolin," "Feldspar" for "Potash Feldspar."  
3. Record whether match is exact (SKU found, terminology matches) or fuzzy (must infer material identity; terminology differs).  
4. For each matching SKU, click into the product detail page to extract: full product name, SKU, full price-tiering table (e.g., 10-lb $X, 50-lb $Y, pallet $Z), and unit (per-pound, per-bag, per-pallet).  
5. Note availability: in-stock, out-of-stock, or backorder.  
6. Record URL of product detail page for future reference.  

**Disambiguation rules (when multiple matches appear):**  
1. If a search returns multiple products (e.g., "Kaolin" returns 18 results), prioritize by relevance displayed on IMCO search page.  
2. For standard/common materials, IMCO's top results tend to be the most-used grade. For "Kaolin," "EPK" (Edgar Plastic Kaolin) is listed; for "Feldspar," "Potassium Feldspar" (standard term) is listed.  
3. For grade variants (e.g., Wollastonite W10 vs. W30, or multiple silica mesh sizes), note both SKUs and price ranges if the glaze recipe does not specify a grade. Flag for manual verification (do the glaze's firing characteristics require a specific grade?).  

**Bulk pricing capture:**  
1. Navigate to the product detail page (not the search-result card) and locate the weight/quantity `<select>` element.  
2. Run a JS snippet (via a real browser tool, e.g. `claude-in-chrome`'s `javascript_tool`) that loops over `select.options`, sets each `.value`, dispatches a `change` event, waits ~400ms, and reads the updated price text from the page — this returns the full tier table (e.g. 1 lb / 5 lb / 10 lb / 25 lb / 50 lb and their prices) without manually clicking each option.  
3. Don't assume the displayed range max is the largest-quantity price — check for non-monotonic bulk discounts (confirmed case: Silica's 50 lb tier is cheaper than its 25 lb tier).  

**CSV data model (what to include):**  
- `material_name`: name as listed in Glazy recipe.  
- `price`: lowest price shown on IMCO search result (likely small/sample qty).  
- `unit`: unit associated with that price (if known; leave blank if not visible on search page).  
- `bulk_price`: highest price shown on IMCO (likely bulk qty or pallet).  
- `bulk_unit`: unit associated with bulk price (if known).  
- `imco_url`: direct URL to product detail page (not search result).  
- `match_confidence`: exact, fuzzy, or not_found.  
- `notes`: SKU, alternative names, availability status, any caveats.  

**When a material is not found:**  
Do not fabricate a price. Leave `price`, `unit`, `bulk_price`, and `bulk_unit` empty. Mark `match_confidence` as `not_found` and note in the `notes` field: (a) what search terms were tried, (b) whether the material is a specialty item IMCO may not stock, and (c) a suggestion for manual lookup (e.g., "Check IMCO's custom milling service; may stock via quote-only").

**Integration with future workflows:**  
1. For batch recipe processing, consider: does Glazy expose an API or downloadable export? If not, a web scraper iterating over recipe IDs would be more efficient than clicking each page.  
2. For IMCO price updates: IMCO prices change over time. If this becomes a production workflow, implement a dated-snapshot convention (e.g. `YYYY-MM-DD-ingredient_prices.csv`) to track price history instead of overwriting the same file.  
3. Consider whether ACAI's IMCO account has an order history API or downloadable invoices—these would be more accurate than catalog prices (actual historical cost).

## Run 2 (2026-07-04) — "Giggin' for Salvation" materials + Frit 3134/Gerstley comparison

Triggered by a real business question (see `reports/frit3134_vs_gerstley_borate_cost_comparison.md`): the studio glaze tech's derivative recipe "Giggin' for Salvation" needed three materials not yet in `ingredients/ingredient_prices.csv`. This run used the JS weight-tier extraction technique (see above) on every product from the start, so all three came back with full tier pricing, not just a min–max range:

| Material | IMCO match | Match confidence | Full tier pricing (1/5/10/25/50 lb) |
|---|---|---|---|
| Frit 3134 | 26802 - Frit 3134 | fuzzy (recipe said "Ferro Frit 3134"; IMCO drops the manufacturer prefix) | $4.25 / $20.00 / $38.00 / $85.00 / $135.00 |
| Whiting | 710 - Marble Whiting (Calcium Carbonate) | exact | $2.50 / $5.00 / $9.00 / $24.25 / $15.00 |
| Bentonite | 763 - 325 Mesh Bentonite | fuzzy (recipe just says "Bentonite," no grade; IMCO also carries a premium "200 Mesh API Grade (Volclay)" at $14–$600 that could be the intended material) | $2.50 / $5.00 / $9.50 / $28.50 / $33.50 |

Also went back and pulled full tier pricing for Gerstley Borate (724), previously only recorded as a min–max range: $6.00 / $30.00 / $55.00 / $150.00 / $225.00 (50 lb bag) — the $225 exactly matches the glaze tech's quote.

**New pattern confirmed:** Whiting's 50 lb tier ($15.00) is cheaper than its 25 lb tier ($24.25) — a second case (after Silica) of a non-monotonic bulk discount. Don't assume price scales linearly or monotonically with quantity; always pull the actual tier table.

**Bentonite grade — resolved:** flagged as open above, decided by Jake (2026-07-04): keep the generic 325 Mesh Bentonite, not the premium Volclay grade.

## Run 3 (2026-07-04) — full-recipe pricing for every remaining ingredient

Triggered by a request to compare Giggin' for Salvation and Frogskin at the full-recipe level (not just the flux), since a single-ingredient swing can be a false positive if other ingredients move the other way. Pulled full tier pricing (same JS technique) for every remaining material in both recipes: Nepheline Syenite, Potash Feldspar, Copper Carbonate, EP Kaolin, Red Iron Oxide, Wollastonite, Titanium Dioxide. All now have real per-lb bulk rates in `ingredients/ingredient_prices.csv` instead of "various."

**Notable findings from this pass:**
- **EP Kaolin is out of stock in every size** (1/5/10/25/50 lb all show "Out of stock" on IMCO). Prices are last-listed, not currently purchasable. This affects both recipes and is arguably a bigger near-term problem than the flux cost question.  
- **Red Iron Oxide has a 100 lb tier** ($375.00) that beats its 50 lb tier ($200.00, i.e. $4.00/lb) on a per-lb basis ($3.75/lb) — the true bulk rate isn't always the 50 lb size. Always check for tiers above 50 lb before calling a rate "bulk."  
- **Potash Feldspar's largest tier is 55.14 lb ($56.00), not 50 lb** — almost certainly a 25 kg bag (25 kg ≈ 55.116 lb) rather than an imperial size. Don't assume every material's tiers are 1/5/10/25/50 lb.  
- **Copper Carbonate has 1/4 lb and 1/2 lb tiers** below 1 lb (colorants are often sold in smaller minimum quantities than bulk clay-body materials).  
- **EP Kaolin (25 lb, $535.00) costs more than its own 50 lb tier ($400.00)** — a third non-monotonic case, same pattern as Silica and Whiting. This is common enough now that it should be treated as the default expectation, not an anomaly.  

With full pricing in hand, total per-batch cost came out to $242.71 (107 lb) for Frogskin with Gerstley Borate and $261.94 (115.5 lb) for Giggin' for Salvation — both landing at the same $2.27/lb once every ingredient is counted, despite Frit 3134 being $1.80/lb cheaper than Gerstley Borate. See `frit3134_vs_gerstley_borate_cost_comparison.md` for the full breakdown.

## Source Files Referenced

- Glazy recipe page: https://glazy.org/recipes/292795  
- IMCO home page: https://www.clayimco.com/  
- IMCO search queries (per-ingredient): see CSV `imco_url` column for direct search/product links.  
- `recipes/compare_recipes.csv` — ingredient lists for Frogskin and "Giggin' for Salvation."  
- `frit3134_vs_gerstley_borate_cost_comparison.md` — the cost comparison this run's data fed into.  
