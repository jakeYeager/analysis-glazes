#!/usr/bin/env python3
"""find_material_candidates.py — log candidate IMCO matches for a material via Glazy's
alternate-name list.

Usage:
    uv run --with playwright scripts/find_material_candidates.py <recipe_glazy_url> "<material name>"

For a material whose materials row is `fuzzy` or `not_found`, this finds that
material's Glazy detail page (by following the link matching <material name>
on the recipe page), scrapes its listed alternate/synonym names, and tries
each one against IMCO's search. Results are *candidates only* — inserted
into db/glazes.db's name_candidates_log table for manual review. This
script never writes to the materials table itself: per this project's
"never fabricate a price" rule, a human confirms any fuzzy match before it
becomes real data.

Confirmed live against glazy.org/materials/15458 (Wollastonite) and IMCO
search: Glazy has no literal "alternate names" section — the closest
equivalent is "Child materials," a list of manufacturer-specific product
names for that generic material, rendered as one comma-separated line.
IMCO's search also doesn't return zero results for a bad query; it falls
back to unrelated "trending" products, so raw hit count alone isn't a
relevance signal — see the token-overlap filter in search_imco().

Also tries the material name with a known manufacturer prefix stripped
(e.g. "Ferro Frit 3134" -> "Frit 3134") as an extra search term, since
IMCO's own catalog often drops it — see KNOWN_MANUFACTURER_PREFIXES.
"""

import re
import sqlite3
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"

# Manufacturer prefixes suppliers/Glazy are inconsistent about including —
# keep in sync with the same list in import_glazy_recipe.py and
# .claude/rules/conventions.md "Material name variants" (the source of
# truth for why this list exists and what's confirmed so far).
KNOWN_MANUFACTURER_PREFIXES = ["Ferro"]


def strip_known_prefix(name: str) -> str | None:
    for prefix in KNOWN_MANUFACTURER_PREFIXES:
        if name.startswith(prefix + " "):
            return name[len(prefix) + 1 :]
    return None


ALT_NAME_HEADING_RE = re.compile(
    r"alternate names?|also known as|synonyms?|child materials?", re.IGNORECASE
)


def find_material_glazy_url(page, recipe_url: str, material_name: str) -> str:
    page.goto(recipe_url, wait_until="load")
    page.wait_for_timeout(1000)
    link = page.locator(f"a:text-is('{material_name}')").first
    if link.count() == 0:
        # fall back to a substring/case-insensitive match
        link = page.get_by_role("link", name=re.compile(re.escape(material_name), re.IGNORECASE)).first
    if link.count() == 0:
        raise RuntimeError(f"no link for '{material_name}' found on {recipe_url}")
    href = link.get_attribute("href")
    if href is None:
        raise RuntimeError(f"link for '{material_name}' has no href on {recipe_url}")
    if href.startswith("http"):
        return href
    return "https://glazy.org" + href


def scrape_alt_names(page, material_url: str) -> list[str]:
    page.goto(material_url, wait_until="load")
    page.wait_for_timeout(1000)
    body_text = page.inner_text("body")
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        match = ALT_NAME_HEADING_RE.search(line)
        if not match:
            continue
        # Glazy renders the heading and its comma-separated list on one line
        # (e.g. "Child materials Vansil W-30 Wollastonite, Imerys ..."), so
        # strip the heading text itself and split the remainder on commas.
        # (Confirmed against a live page: everything lives on this one line —
        # don't pull in following lines, they're unrelated page chrome.)
        text = line[: match.start()] + line[match.end() :]
        return [name.strip() for name in text.split(",") if name.strip()]
    return []


WORD_RE = re.compile(r"[a-z0-9]+")


def relevant_tokens(term: str) -> set[str]:
    return {w for w in WORD_RE.findall(term.lower()) if len(w) >= 4}


def search_imco(page, term: str) -> list[str]:
    """Return IMCO product URLs that look genuinely relevant to `term`.

    IMCO's search doesn't return zero results for a bad query — it falls
    back to unrelated "trending" products (confirmed live: nonsense terms
    return the same 9 hrefs pointing at an unrelated clay-body bag). So a
    raw hit count isn't a relevance signal; only keep hrefs that share a
    significant (4+ char) word with the search term.
    """
    page.goto(f"https://www.clayimco.com/s/search?q={quote(term)}", wait_until="load")
    page.wait_for_timeout(1000)
    hrefs = page.eval_on_selector_all("a[href*='/product/']", "els => els.map(e => e.href)")
    unique = list(dict.fromkeys(hrefs))
    tokens = relevant_tokens(term)
    if not tokens:
        return unique
    return [href for href in unique if any(tok in href.lower() for tok in tokens)]


def suggest_confidence(term: str, material_name: str, hits: int) -> str:
    if hits == 0:
        return "not_found"
    if term.strip().lower() == material_name.strip().lower() and hits == 1:
        return "exact"
    return "fuzzy"


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <recipe_glazy_url> \"<material name>\"", file=sys.stderr)
        sys.exit(1)
    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    recipe_url, material_name = sys.argv[1], sys.argv[2]
    today = date.today().isoformat()

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            material_url = find_material_glazy_url(page, recipe_url, material_name)
            alt_names = scrape_alt_names(page, material_url)
        except Exception as exc:
            print(f"error finding alt names for '{material_name}': {exc}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        stripped = strip_known_prefix(material_name)
        terms_to_try = [material_name] + ([stripped] if stripped else []) + alt_names
        for term in terms_to_try:
            matches = search_imco(page, term)
            rows.append(
                {
                    "material_name": material_name,
                    "glazy_material_url": material_url,
                    "alt_names_tried": "; ".join(alt_names),
                    "imco_search_term": term,
                    "imco_hits": len(matches),
                    "suggested_sku": matches[0] if matches else "",
                    "suggested_confidence": suggest_confidence(term, material_name, len(matches)),
                    "checked_date": today,
                }
            )

        browser.close()

    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT INTO name_candidates_log "
        "(material_name, glazy_material_url, alt_names_tried, imco_search_term, "
        "imco_hits, suggested_sku, suggested_confidence, checked_date) "
        "VALUES (:material_name, :glazy_material_url, :alt_names_tried, :imco_search_term, "
        ":imco_hits, :suggested_sku, :suggested_confidence, :checked_date)",
        rows,
    )
    conn.commit()
    conn.close()

    for row in rows:
        print(
            f"{row['imco_search_term']!r}: {row['imco_hits']} hit(s), "
            f"suggested {row['suggested_confidence']} -> {row['suggested_sku'] or '(none)'}"
        )
    print(f"logged {len(rows)} candidate row(s) to {DB_PATH}")


if __name__ == "__main__":
    main()
