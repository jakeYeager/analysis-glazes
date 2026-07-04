# Conventions

## Ingredient price tiers

`ingredients/ingredient_prices.csv` tracks per-quantity IMCO pricing in six
standard columns: `price_1lb, price_5lb, price_10lb, price_25lb, price_50lb,
price_100lb`. Two simplifying rules apply when scraped data doesn't line up
with these buckets exactly:

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

## Recipes

An accepted convention in writing glaze recipes is parts by weight normalized to 100-part. This 100-part is known as the "base glaze". 100-part is sometimes approximate (slight variations are not always calculation errors). Colorants & opacifiers are ingredients added (sometimes labled "add") on top of a 100-part base (base glaze ingredients).

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