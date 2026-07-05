#!/usr/bin/env bash
# md2pdf.sh — convert Markdown report(s) to .pdf for sharing.
#
# Usage:
#   scripts/md2pdf.sh path/to/report.md [more.md ...]
#
# Each .pdf is written into a pdfs/ subfolder next to its source .md (same
# name, .pdf extension), overwriting any existing one. Pipeline: pandoc (via `uv`, ephemeral, same
# approach as md2docx.sh — nothing installed permanently) renders Markdown
# to a styled standalone HTML file, then headless Google Chrome prints that
# HTML to PDF. Requires Google Chrome.app to already be installed locally;
# no brew, no project env.
#
# Styling mirrors ../analysis-governance/generate_pdfs.py: page numbers,
# H2-starts-a-new-page pagination (except the first section, which stays on
# page 1 with the title/metadata table), and the same type/table/blockquote
# treatment. That script targets a different toolchain (Python `markdown`
# lib instead of pandoc), so the "first H2" exception is done here with a
# pure CSS `:first-of-type` selector instead of injecting an HTML class —
# same visual result, no extra processing step needed for this pandoc-based
# pipeline.

set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <file.md> [file2.md ...]" >&2
  exit 1
fi

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  echo "Google Chrome not found at: $CHROME" >&2
  exit 1
fi

WORKDIR="$(mktemp -d -t md2pdf)"
trap 'rm -rf "$WORKDIR"' EXIT

CSS="$WORKDIR/style.css"
cat > "$CSS" <<'CSS'
@page {
    size: letter;
    margin: 0.85in 0.85in 1in 0.85in;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 9pt;
        color: #777;
    }
}

:root {
    --text: #1a1a1a;
    --muted: #5a5a5a;
    --rule: #d0d0d0;
    --rule-strong: #3a3a3a;
    --bg-soft: #f5f5f5;
    --bg-soft-2: #fafafa;
}

html, body {
    margin: 0;
    padding: 0;
}

body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

h1 {
    font-size: 22pt;
    font-weight: 600;
    margin: 0 0 16pt 0;
    padding-bottom: 8pt;
    border-bottom: 2px solid var(--rule-strong);
    letter-spacing: -0.01em;
    page-break-after: avoid;
    break-after: avoid;
}

h2 {
    font-size: 16pt;
    font-weight: 600;
    margin: 0 0 12pt 0;
    padding-bottom: 4pt;
    border-bottom: 1px solid var(--rule);
    letter-spacing: -0.005em;
    page-break-before: always;
    break-before: page;
    page-break-after: avoid;
    break-after: avoid;
}

/* Keep the first section on page 1 with the title/metadata table */
h2:first-of-type {
    page-break-before: auto;
    break-before: auto;
}

h3 {
    font-size: 13pt;
    font-weight: 600;
    margin: 20pt 0 6pt 0;
    color: var(--text);
    page-break-after: avoid;
    break-after: avoid;
}

h4 {
    font-size: 11.5pt;
    font-weight: 600;
    margin: 14pt 0 5pt 0;
    color: var(--text);
    page-break-after: avoid;
    break-after: avoid;
}

h5, h6 {
    font-size: 10.5pt;
    font-weight: 600;
    margin: 12pt 0 4pt 0;
    color: var(--muted);
}

p {
    margin: 6pt 0;
    orphans: 3;
    widows: 3;
}

blockquote {
    border-left: 3px solid var(--muted);
    margin: 10pt 4pt;
    padding: 4pt 14pt;
    color: #333;
    font-style: italic;
    background: var(--bg-soft-2);
    page-break-inside: avoid;
    break-inside: avoid;
}

blockquote p {
    margin: 4pt 0;
}

code {
    font-family: "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 9.5pt;
    background: var(--bg-soft);
    padding: 1px 5px;
    border-radius: 3px;
    color: #222;
}

pre {
    background: var(--bg-soft);
    padding: 10pt 12pt;
    border-radius: 4px;
    font-family: "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 9pt;
    line-height: 1.4;
    overflow-x: auto;
    page-break-inside: avoid;
    break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
    font-size: 9pt;
    border-radius: 0;
}

table {
    border-collapse: collapse;
    margin: 12pt 0;
    width: 100%;
    font-size: 9.5pt;
    page-break-inside: avoid;
    break-inside: avoid;
}

table th,
table td {
    border: 1px solid var(--rule);
    padding: 5pt 9pt;
    text-align: left;
    vertical-align: top;
}

table th {
    background: #ededed;
    font-weight: 600;
    color: var(--text);
}

table tr:nth-child(even) td {
    background: var(--bg-soft-2);
}

/* Metadata table at the top of each report */
h1 + table {
    width: 70%;
    margin: 0 0 16pt 0;
    font-size: 10pt;
}

h1 + table td:first-child {
    width: 30%;
    background: #f0f0f0;
}

h1 + table tr:nth-child(even) td {
    background: inherit;
}

hr {
    border: none;
    border-top: 1px solid var(--rule);
    margin: 18pt 0;
}

ul, ol {
    padding-left: 24pt;
    margin: 8pt 0;
}

li {
    margin: 4pt 0;
}

li p {
    margin: 3pt 0;
}

strong {
    font-weight: 600;
}

em {
    font-style: italic;
}

a {
    color: var(--text);
    text-decoration: none;
    border-bottom: 1px dotted var(--muted);
}

/* Keep short sections together */
h3 + p,
h4 + p,
h3 + ul,
h4 + ul {
    page-break-before: avoid;
    break-before: avoid;
}
CSS

failed=0
for src in "$@"; do
  if [ ! -f "$src" ]; then
    echo "skip (not found): $src" >&2
    failed=1
    continue
  fi
  html="$WORKDIR/$(basename "${src%.md}").html"
  pdfdir="$(dirname "$src")/pdfs"
  mkdir -p "$pdfdir"
  pdf="$pdfdir/$(basename "${src%.md}").pdf"

  uv run --with pypandoc-binary python - "$src" "$html" "$CSS" <<'PY'
import sys
import pypandoc

src, html, css = sys.argv[1:4]
pypandoc.convert_file(src, "html", outputfile=html, extra_args=["--standalone", "--embed-resources", f"--css={css}"])
PY

  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --hide-scrollbars \
    --run-all-compositor-stages-before-draw --virtual-time-budget=5000 \
    --print-to-pdf="$pdf" "file://$html" >/dev/null 2>&1
  echo "$src -> $pdf"
done

exit "$failed"
