# Conventions

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