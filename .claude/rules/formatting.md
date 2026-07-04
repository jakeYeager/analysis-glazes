# Markdown Formatting Rules — `reports/`

These rules exist so the project's reports
render cleanly in Obsidian on a phone (the user reviews via AirDrop +
Obsidian.app on iPhone). Soft-wrapped lines collapse incorrectly on
small screens; this convention prevents that without sacrificing
readability in a desktop editor.

Apply these rules to every Markdown document in `reports/` and. 
Internal technical files at the repo root (`README.md`,
`PLAN.md`, etc.) are exempt — they are read on a desktop and follow
ordinary conventions.

## Rule 1 — Unwrap paragraphs

Within a paragraph, join consecutive non-empty lines into a single
long line. Markdown renderers reflow long lines automatically; the
join is what lets Obsidian on iPhone reflow them to the device width
instead of honoring the desktop wrap.

A "paragraph" for this rule is a block of consecutive non-empty lines
that is **not**:

- a heading (line starting with `#`)
- a table row (line containing `|`)
- a fenced code block (between ` ``` ` markers)
- a blockquote (line starting with `>`)
- a list item (see Rule 2)
- the metadata frontmatter table at the top of the document

Preserve the blank line that separates paragraphs from each other and
from headings, lists, tables, and code blocks.

## Rule 2 — Trailing double-space on every list item

Every list item — bulleted (`-`, `*`) or numbered (`1.`, `2.`, …),
including nested items — ends with two trailing spaces. In Markdown,
a line ending in two spaces is a hard line break, which keeps each
item visually separated when Obsidian on iPhone reflows.

If a list item was originally soft-wrapped onto multiple physical
lines, first unwrap it into a single line, **then** append the two
trailing spaces.

Preserve nested-list indentation exactly. Two trailing spaces apply
to nested items as well.

## Rule 3 — What NOT to touch

The following are preserved verbatim:

- Any metadata frontmatter table at the top of the document  
  (the `| | |` / `|---|---|` block with Date, Last Updated, Document
  Version, Generation Model, Author).
- All other Markdown tables (any block of consecutive lines
  containing `|`).
- Headings — no trailing spaces, no joining across heading and body.
- Fenced code blocks (between ` ``` ` markers) — content stays
  exactly as written.
- Inline code spans — unchanged.
- Blockquotes — unchanged.
- Blank lines that separate sections, paragraphs, or list groups —
  preserved.
