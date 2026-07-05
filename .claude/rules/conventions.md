# Conventions

## Firing type

`recipes.firing_type` (in `db/glazes.db`, exported to
`recipes/recipe_metadata.csv`) is either `mid-fire` or `raku`. Glazy's
"Atmospheres" field states it directly (e.g. `"Raku, Reduction"`) — confirmed
live and auto-detected by `scripts/import_glazy_recipe.py`. Fall back to cone
only if Atmospheres doesn't mention it: cone 04-08 (low-fire) is raku
territory in this studio's practice, cone 04 and hotter (up to ~6) is
mid-fire. When in doubt, ask rather than guess — the two firing types aren't
cost-interchangeable (raku glazes are typically simpler, fewer/cheaper
materials) and mixing them in a report without the tag defeats the point of
tracking it.

## Material name variants

Different sources name the same material differently — this project has
hit it repeatedly (Potash/Potassium Feldspar, EP Kaolin/EPK, and now
manufacturer prefixes). One confirmed class: **manufacturer prefixes on
frits.** "Ferro Frit NNNN" and "Frit NNNN" are the same product — Ferro's
proprietary frit numbering (3124, 3134, etc.) became the de facto industry
reference number, and ceramic suppliers vary on whether they include the
manufacturer name. Confirmed via web search 2026-07-04 across multiple
independent ceramic-supply sources for Frit 3134 specifically. `Ferro` is
tracked in `KNOWN_MANUFACTURER_PREFIXES` in both `scripts/import_glazy_recipe.py`
(so a new recipe reuses the existing priced material instead of creating a
duplicate `not_found` row) and `scripts/find_material_candidates.py` (so the
stripped name gets tried as an IMCO search term too). Extend that list —
in both files — if another manufacturer prefix causes the same problem.

This is a *confirmed* class of name variant, not a guess — still mark the
resulting match `fuzzy` rather than `exact` (per the never-fabricate rule),
since it's inferred equivalence, not a literal string match.

Another confirmed case: **abbreviations for the same product.** `"EPK"` and
`"EP Kaolin"` are the same material (Edgar Plastic Kaolin) — confirmed when
a raku-glaze spreadsheet import used `"EPK"` for a material already tracked
as `"EP Kaolin"`. Tracked in `KNOWN_MATERIAL_ALIASES` in
`scripts/import_csv_recipes.py` (and worth adding to `import_glazy_recipe.py`
if a Glazy page ever uses the abbreviation directly). Unlike the
manufacturer-prefix case, this is a straight rename, not a fuzzy inference —
mark it `exact` once priced.

## Ingredient price tiers

`materials` (in `db/glazes.db`, exported to `ingredients/ingredient_prices.csv`)
tracks per-quantity IMCO pricing in six standard columns: `price_1lb,
price_5lb, price_10lb, price_25lb, price_50lb, price_100lb`. Two simplifying
rules apply when scraped data doesn't line up with these buckets exactly:

- **Sub-1 lb tiers are dropped.** Some materials (e.g. colorants like Copper
  Carbonate) also sell in 1/4 lb or 1/2 lb minimums below their 1 lb tier.
  These aren't tracked — recipes here are always priced in whole-lb-and-up
  quantities, so the smallest tracked tier is always 1 lb, and `price`/`unit`
  reflect that (not the true smallest pack size, if it's under 1 lb).
- **Non-standard pack sizes get bucketed into the closest standard column,**
  with the real size disclosed in that row's `notes`. E.g. a 25 kg bag
  (~55.14 lb, Potash Feldspar) has no matching column; its price is recorded
  under `price_50lb` (the nearest bucket), and `notes` says so explicitly,
  since that column value is an approximation, not a literal 50 lb price.

`bulk_price`/`bulk_unit` are the exception: they always reflect the true
cheapest-per-unit tier at its **real** quantity (e.g. `55.14 lb`, never
bucketed), since that's what drives actual batch-cost math in
`scripts/price_batch.py`. The wide tier columns are for at-a-glance
comparison across materials at standard sizes; `bulk_price`/`bulk_unit` are
for accurate costing — don't conflate the two.

`scripts/price_batch.py`'s `refresh_price_row()` implements this bucketing
automatically on every refresh; it prints a warning when a tier gets
approximated so you can decide whether the row's `notes` needs updating.

## Purchase tier

`materials.purchase_tier` (exported to `ingredients/ingredient_prices.csv`)
says which cached tier column actually drives that material's cost in
`scripts/price_batch.py` and `scripts/generate_price_summary.py` — it's an
enum matching the tier columns above (`'1lb'`, `'5lb'`, `'10lb'`, `'25lb'`,
`'50lb'`, `'100lb'`), plus a special value `'bulk'` meaning "use
`bulk_price`/`bulk_unit` as before" (the cheapest true per-unit tier,
regardless of size).

**Why this exists:** `bulk_price` reflects the cheapest way to buy a
material at *some* real quantity, but that quantity isn't always realistic.
Confirmed by Jake, 2026-07-05: colorants, opacifiers, suspension aids
(Copper Carbonate, the iron/copper/cobalt oxides and carbonates, Zircopax,
Bentonite, CMC Gum, Tin Oxide, etc.) and Lithium Carbonate are actually
bought in much smaller quantities — 5-10 lb at a time, not the 50lb+ bags
that make up most materials' `bulk_price` tier. Pricing them at the bulk
rate understated their real cost. A boolean "is this a small-batch
material" flag was considered and rejected in favor of this tier-mapped
enum, since some materials (not yet identified) may turn out to only be
bought in 1lb increments — the field should be able to say that precisely
rather than lump every non-bulk case into one rate.

**Current defaults:** every base-glaze material (frits, feldspars, clays,
silica) is `'bulk'` — unchanged from before this field existed. Every
colorant/opacifier/suspension-aid material, plus Lithium Carbonate
specifically (chemically a flux, but purchased like a colorant due to cost
and small usage), is `'10lb'`. No material is currently `'1lb'` — that
tier exists for a future case, not applied retroactively without evidence.

**Impact when this was introduced (2026-07-05):** repricing every recipe
against the new tiers raised every raku recipe containing a flagged
material (all except Clear Crackle, which has none) — non-trivially in
five cases where Lithium Carbonate or heavy colorant content dominates the
batch: Bill's Neon Blue 2025 (+32%), Looks Expensive (+31%), Kelly's
Lo-Fire Shino (+51%, driven by an unusually high 24%-by-weight Lithium
Carbonate content), Forbes Midnight Blue (+20%), and Hasselle Copper Matte
(+20%). Nothing decreased. See `.claude/CLAUDE.md`'s Open items for the
full before/after table generated at the time.

**How to apply going forward:** when adding a new material, default it to
`'bulk'` unless there's a specific reason to think it's bought in smaller
quantities (colorant, oxide, carbonate, or anything else added in small
amounts relative to a recipe's base) — in which case set `'10lb'` the same
way as the materials above, or ask if a different tier seems more
realistic for that specific material.

## Recipes

An accepted convention in writing glaze recipes is parts by weight normalized to 100-part. This 100-part is known as the "base glaze". 100-part is sometimes approximate (slight variations are not always calculation errors). Colorants & opacifiers are ingredients added (sometimes labled "add") on top of a 100-part base (base glaze ingredients).

**"To taste" application ingredients aren't chemistry — don't treat their amount as a data-quality signal.** CMC Gum (confirmed by Jake, 2026-07-04) is added purely to improve brushability/application, not for its fired chemistry, so its quantity is routinely adjusted batch to batch and isn't governed by the same precision as fluxes, colorants, or opacifiers. When a source disagrees with Glazy (or another source) on a CMC Gum amount, that's expected variance, not a transcription error worth flagging the way a flux or colorant discrepancy would be. Bentonite (a suspension aid, also often added "to taste") is plausibly similar, but that hasn't been explicitly confirmed the way CMC Gum has — don't assume it without asking.

**`$/lb` reflects mixing cost, not real per-piece cost — application thickness matters and isn't tracked here.** Confirmed by Jake, 2026-07-04, re: "Hasselle Copper Matte" ($11.43/lb, ~80% Black Copper Oxide): that recipe is deliberately applied as a very thin coat — just enough clay to make the copper stick — so its actual cost per piece is far below what the $/lb figure alone suggests. A thin-coat glaze and a thick-dipped glaze at the same $/lb do not cost the same per piece. Don't rank or compare recipes by `$/lb` alone as a proxy for "cost to use" without knowing application method; flag this caveat when a recipe's notes mention thin/thick application, and ask if it's unclear.

When a recipe has this kind of caveat, prefix its `recipes.notes` with `STAKEHOLDER NOTE` (see `scripts/generate_price_summary.py`'s `STAKEHOLDER_NOTE_PREFIX`) so the price summary surfaces a "see notes" flag in its table. Plain provenance notes (e.g. the bulk-import `is_addition` disclosure) should *not* use this prefix — they're not relevant to interpreting `$/lb` and would just be noise in the stakeholder report if flagged the same way.

**Not every tracked recipe is in active rotation.** Some are kept purely for reference/comparison (e.g. Kelly's Lo-Fire Shino — confirmed by Jake, 2026-07-04: a personal favorite nobody else at the studio mixes, kept in the file anyway). A `$/lb` ranking that includes these is misleading if read as "what we actually produce" — Kelly's Lo-Fire Shino currently ranks #2 by `$/lb`, ahead of things the studio actually mixes regularly. Mark these with `REFERENCE ONLY` at the start of `recipes.notes` (`REFERENCE_ONLY_PREFIX` in `scripts/generate_price_summary.py`) so the price summary flags them as "reference only — not in active rotation" rather than implying production relevance. (Blue Moon was originally tracked here too, but Jake dropped it entirely 2026-07-05 rather than keep it flagged reference-only — see `.claude/CLAUDE.md`'s Open items.)

## New reports

After the title, make a short framing paragraph explaining why the doc exists, tables over prose for numbers, and a "Source files referenced" list at the bottom.

### Header template

```markdown
# <Report Title>

| | |
|---|---|
| **Date** | YYYY-MM-DD (original date of record) |
| **Last Updated** | YYYY-MM-DD |
| **Document Version** | X.Y |
| **Generation Model** | <model name + context window> |
| **Author** | <author name> |
```

### Field notes

- **Date** — the original date of record for the document. Does not
  change on edits.
- **Last Updated** — updated whenever the document is substantively
  changed. If making multiple changes in a session, update once at the
  end to the current date.
- **Document Version** — see versioning guidance below.
- **Generation Model** — the model currently doing the work
  (e.g., "Claude Sonnet 4.6 (1M context)").
- **Author** — the human directing the work, not the model.

### Versioning Guidance

No hard rule. Suggested convention:

- **1.0** — initial version; minor edits, typo fixes, or formatting
  changes don't bump the version
- **1.1, 1.2, ...** — substantive new findings, new sections, or
  meaningful expansion of existing sections
- **2.0** — structural reorganization, significant revision, or a
  material shift in conclusion

When in doubt, err toward bumping — a reader seeing "1.4" knows the
document has evolved; a reader seeing "1.0" for months assumes it
hasn't been touched.

Always bump `Last Updated` on any substantive change, even ones too
small to bump the version.

## Regenerating PDFs

```
scripts/md2pdf.sh path/to/report.md
```

Renders the Markdown through an ephemeral `pandoc` (via `uv`, nothing installed permanently) into styled HTML, then prints it to PDF with headless Google Chrome. Requires Chrome to be installed locally; no other setup.