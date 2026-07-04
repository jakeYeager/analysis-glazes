#!/usr/bin/env bash
# md2pdf.sh — convert Markdown report(s) to .pdf for sharing.
#
# Usage:
#   scripts/md2pdf.sh path/to/report.md [more.md ...]
#
# Each .pdf is written alongside its source .md (same name, .pdf extension),
# overwriting any existing one. Pipeline: pandoc (via `uv`, ephemeral, same
# approach as md2docx.sh — nothing installed permanently) renders Markdown
# to a styled standalone HTML file, then headless Google Chrome prints that
# HTML to PDF. Requires Google Chrome.app to already be installed locally;
# no brew, no project env.

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
body { font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 780px; margin: 2rem auto; line-height: 1.5; color: #1a1a1a; }
h1, h2, h3 { line-height: 1.25; }
h1 { border-bottom: 2px solid #ddd; padding-bottom: .3rem; }
h2 { border-bottom: 1px solid #eee; padding-bottom: .2rem; margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.92em; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f2f2f2; }
code { background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1rem; color: #444; }
a { color: #2563eb; }
CSS

failed=0
for src in "$@"; do
  if [ ! -f "$src" ]; then
    echo "skip (not found): $src" >&2
    failed=1
    continue
  fi
  html="$WORKDIR/$(basename "${src%.md}").html"
  pdf="${src%.md}.pdf"

  uv run --with pypandoc-binary python - "$src" "$html" "$CSS" <<'PY'
import sys
import pypandoc

src, html, css = sys.argv[1:4]
pypandoc.convert_file(src, "html", outputfile=html, extra_args=["--standalone", "--embed-resources", f"--css={css}"])
PY

  "$CHROME" --headless --disable-gpu --no-margins --print-to-pdf="$pdf" --print-to-pdf-no-header "file://$html" >/dev/null 2>&1
  echo "$src -> $pdf"
done

exit "$failed"
