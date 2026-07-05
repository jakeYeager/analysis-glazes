#!/usr/bin/env python3
"""import_glazy_recipe.py — fetch a Glazy recipe once and add it to db/glazes.db.

Usage:
    uv run --with playwright scripts/import_glazy_recipe.py <glazy_recipe_url> [--firing-type mid-fire|raku] [--force]

Recipes don't drift like prices do, so unlike scrape_imco_price.py there's no
staleness window here — a recipe is fetched once and that's it. Re-running
against a glazy_url already in the recipes table is a no-op unless --force
is passed (which deletes the existing recipe + its recipe_ingredients rows
and re-imports fresh; materials/prices are untouched either way). The
existing-recipe check matches on *either* glazy_url or the scraped name, so
this also handles the "upgrade" case: a recipe bulk-imported from a personal
spreadsheet (scripts/import_csv_recipes.py, no glazy_url yet, is_addition
defaulted to false) that Jake has since added to Glazy by hand — re-running
this script with --force and the new URL replaces the placeholder row with
the real one, including the correct is_addition split. Any existing
recipes.notes (e.g. a manually-added STAKEHOLDER NOTE/REFERENCE ONLY flag,
see .claude/rules/conventions.md) is carried forward across a --force
re-import rather than wiped, since Glazy's page has no equivalent field.

New materials encountered here are inserted with match_confidence='not_found'
and no price data — run scripts/find_material_candidates.py /
scripts/price_batch.py afterward to resolve and price them, same as any
other unpriced material. Before creating a new row, get_or_create_material()
also checks whether stripping a known manufacturer prefix (see
KNOWN_MANUFACTURER_PREFIXES below) matches an existing material, so e.g.
"Ferro Frit 3134" reuses the already-priced "Frit 3134" row instead of
creating a duplicate — this is what caused the Run 7 "Ferro Frit 3134"
duplicate, resolved in Run 8. This is the actual fix for ingesting ~50
recipes without 50 agent browsing sessions: each recipe becomes one
idempotent script call.

Confirmed live against glazy.org/recipes/292795 (Frogskin, no additions) and
glazy.org/recipes/631749 (a raku recipe with additions): recipe
name/cone/atmosphere/status are each a "Label" line followed by a value line
in the page's rendered text; the ingredient table is the first <table> on
the page, one row per material (name links to /materials/<id>, captured
here as glazy_material_url). Additions (colorants/opacifiers layered on a
100-part base, see .claude/rules/conventions.md) are NOT "+"-prefixed
amounts as originally assumed — Glazy instead inserts a "Total base recipe"
subtotal row after the 100-part base, and every ingredient row after it
(before the final "Total" row) is an addition. A recipe with no additions
just goes straight to "Total" with no subtotal row at all (Frogskin's case).

firing_type is auto-detected from the "Atmospheres" field (e.g. "Raku,
Reduction" -> raku) unless --firing-type is passed explicitly to override.
"""

import argparse
import re
import sqlite3
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"

# Manufacturer prefixes suppliers/Glazy are inconsistent about including.
# Confirmed 2026-07-04 via web search: "Ferro Frit NNNN" and "Frit NNNN" are
# the same Ferro Corporation product -- Ferro's frit numbering (3124, 3134,
# etc.) is the de facto industry reference number, and most ceramic supply
# sites list it either with or without the manufacturer name. See
# .claude/rules/conventions.md "Material name variants". Extend this list
# if another manufacturer prefix causes the same duplicate-material problem.
KNOWN_MANUFACTURER_PREFIXES = ["Ferro"]


def strip_known_prefix(name: str) -> str | None:
    for prefix in KNOWN_MANUFACTURER_PREFIXES:
        if name.startswith(prefix + " "):
            return name[len(prefix) + 1 :]
    return None


def parse_metadata(lines: list[str]) -> dict:
    id_index = next(i for i, line in enumerate(lines) if re.fullmatch(r"\d+", line))
    metadata = {"name": lines[id_index - 1]}
    for label, key in [("Orton Cone", "cone"), ("Atmospheres", "atmosphere"), ("Status", "status")]:
        try:
            idx = lines.index(label)
            metadata[key] = lines[idx + 1]
        except ValueError:
            metadata[key] = None
    return metadata


def parse_ingredients(page) -> list[dict]:
    table = page.locator("table").first
    rows = table.evaluate(
        """table => Array.from(table.querySelectorAll('tr')).map(tr => {
            const cells = Array.from(tr.querySelectorAll('td, th'));
            const link = tr.querySelector('a');
            return {
                label: cells[0] ? cells[0].innerText.trim() : '',
                amount: cells[1] ? cells[1].innerText.trim() : '',
                href: link ? link.getAttribute('href') : null,
            };
        })"""
    )
    ingredients = []
    is_addition = False
    for row in rows:
        label = row["label"]
        if label in ("", "Material"):
            continue
        if label.lower().startswith("total base"):
            is_addition = True  # everything from here on is layered on top of the 100-part base
            continue
        if label.lower() == "total":
            break  # grand-total row marks the end of the ingredient table
        amount = float(row["amount"].strip())
        glazy_material_url = ("https://glazy.org" + row["href"]) if row["href"] else None
        ingredients.append(
            {
                "material": label,
                "amount": amount,
                "is_addition": is_addition,
                "glazy_material_url": glazy_material_url,
            }
        )
    return ingredients


def get_or_create_material(conn: sqlite3.Connection, name: str, glazy_material_url: str | None, source_url: str) -> int:
    row = conn.execute("SELECT id, glazy_material_url FROM materials WHERE canonical_name = ?", (name,)).fetchone()
    if row:
        material_id, existing_url = row
        if not existing_url and glazy_material_url:
            conn.execute("UPDATE materials SET glazy_material_url = ? WHERE id = ?", (glazy_material_url, material_id))
        return material_id

    stripped = strip_known_prefix(name)
    if stripped:
        alt_row = conn.execute("SELECT id, glazy_material_url FROM materials WHERE canonical_name = ?", (stripped,)).fetchone()
        if alt_row:
            material_id, existing_url = alt_row
            print(f"  '{name}' matched existing material '{stripped}' after stripping known manufacturer prefix")
            if not existing_url and glazy_material_url:
                conn.execute("UPDATE materials SET glazy_material_url = ? WHERE id = ?", (glazy_material_url, material_id))
            return material_id

    cursor = conn.execute(
        "INSERT INTO materials (canonical_name, match_confidence, glazy_material_url, notes) "
        "VALUES (?, 'not_found', ?, ?)",
        (name, glazy_material_url, f"Auto-created by import_glazy_recipe.py from {source_url} on {date.today().isoformat()}."),
    )
    print(f"  new material: {name} (not_found, needs pricing)")
    return cursor.lastrowid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("glazy_url")
    parser.add_argument(
        "--firing-type",
        choices=["mid-fire", "raku"],
        default=None,
        help="override auto-detection (default: 'raku' if the Atmospheres field mentions raku, else 'mid-fire')",
    )
    parser.add_argument("--force", action="store_true", help="re-import even if this glazy_url is already in recipes")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    conn = sqlite3.connect(DB_PATH)

    # Fast path: skip the browser entirely if this exact URL is already
    # imported and --force wasn't passed.
    by_url = conn.execute("SELECT id, name FROM recipes WHERE glazy_url = ?", (args.glazy_url,)).fetchone()
    if by_url and not args.force:
        print(f"'{by_url[1]}' already imported from {args.glazy_url} -- use --force to re-import")
        conn.close()
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(args.glazy_url, wait_until="load")
        page.wait_for_timeout(1500)
        body_text = page.inner_text("body")
        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        metadata = parse_metadata(lines)
        ingredients = parse_ingredients(page)
        browser.close()

    # Re-check by name too, now that we know it: catches a recipe imported
    # earlier via import_csv_recipes.py (no glazy_url yet) that shares this
    # Glazy page's name -- recipes.name is UNIQUE, so this would otherwise
    # crash on INSERT instead of upgrading the existing row.
    by_name = conn.execute(
        "SELECT id, name, glazy_url FROM recipes WHERE name = ?", (metadata["name"],)
    ).fetchone()
    existing = by_url or by_name
    if by_name and not by_url and not args.force:
        # Only reachable here when by_url was empty (the not-force/by_url
        # case already returned above), so this is always the name-only match.
        print(
            f"a recipe named '{metadata['name']}' already exists "
            f"(glazy_url={by_name[2]!r}) -- use --force to overwrite it"
        )
        conn.close()
        return
    existing_notes = None
    if existing:
        # Preserve any manually-curated notes (e.g. STAKEHOLDER NOTE /
        # REFERENCE ONLY flags) across a --force re-import -- these aren't
        # on the Glazy page itself, so a plain delete+reinsert would
        # silently wipe them. Confirmed missing 2026-07-05 on Post Pac Man's
        # thin-application note after a re-import; restored by hand there,
        # fixed here so it doesn't happen again.
        existing_notes = conn.execute(
            "SELECT notes FROM recipes WHERE id = ?", (existing[0],)
        ).fetchone()[0]
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (existing[0],))
        conn.execute("DELETE FROM recipes WHERE id = ?", (existing[0],))

    firing_type = args.firing_type
    if firing_type is None:
        atmosphere = metadata["atmosphere"] or ""
        firing_type = "raku" if "raku" in atmosphere.lower() else "mid-fire"

    cursor = conn.execute(
        "INSERT INTO recipes (name, glazy_url, firing_type, cone, atmosphere, status, imported_date, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            metadata["name"],
            args.glazy_url,
            firing_type,
            metadata["cone"],
            metadata["atmosphere"],
            metadata["status"],
            date.today().isoformat(),
            existing_notes,
        ),
    )
    recipe_id = cursor.lastrowid

    for ingredient in ingredients:
        material_id = get_or_create_material(conn, ingredient["material"], ingredient["glazy_material_url"], args.glazy_url)
        conn.execute(
            "INSERT INTO recipe_ingredients (recipe_id, material_id, amount, is_addition) VALUES (?, ?, ?, ?)",
            (recipe_id, material_id, ingredient["amount"], 1 if ingredient["is_addition"] else 0),
        )

    conn.commit()
    conn.close()

    print(f"imported '{metadata['name']}' ({len(ingredients)} ingredients) from {args.glazy_url}")


if __name__ == "__main__":
    main()
