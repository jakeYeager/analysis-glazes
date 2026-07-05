#!/usr/bin/env python3
"""import_glazy_recipe.py — fetch a Glazy recipe once and add it to db/glazes.db.

Usage:
    uv run --with playwright scripts/import_glazy_recipe.py <glazy_recipe_url> [--firing-type mid-fire|raku] [--force]

Recipes don't drift like prices do, so unlike scrape_imco_price.py there's no
staleness window here — a recipe is fetched once and that's it. Re-running
against a glazy_url already in the recipes table is a no-op unless --force
is passed (which deletes the existing recipe + its recipe_ingredients rows
and re-imports fresh; materials/prices are untouched either way).

New materials encountered here are inserted with match_confidence='not_found'
and no price data — run scripts/find_material_candidates.py /
scripts/price_batch.py afterward to resolve and price them, same as any
other unpriced material. This is the actual fix for ingesting ~50 recipes
without 50 agent browsing sessions: each recipe becomes one idempotent
script call.

Confirmed live against glazy.org/recipes/292795 (Frogskin): recipe
name/cone/atmosphere/status are each a "Label" line followed by a value line
in the page's rendered text; the ingredient table is the first <table> on
the page, one row per material (name links to /materials/<id>, captured
here as glazy_material_url), with a trailing "Total" row skipped. Additions
(colorants/opacifiers layered on a 100-part base, see
.claude/rules/conventions.md) are assumed to render as a "+"-prefixed
amount when present — not confirmed live, since Frogskin's own recipe is
base-only and doesn't have any. Spot-check is_addition against a recipe
that actually has additions before trusting a bulk import.
"""

import argparse
import re
import sqlite3
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"


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
    for row in rows:
        label = row["label"]
        if label in ("", "Material", "Total"):
            continue
        amount_text = row["amount"]
        is_addition = amount_text.startswith("+")
        amount = float(amount_text.lstrip("+").strip())
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
    parser.add_argument("--firing-type", choices=["mid-fire", "raku"], default="mid-fire")
    parser.add_argument("--force", action="store_true", help="re-import even if this glazy_url is already in recipes")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT id, name FROM recipes WHERE glazy_url = ?", (args.glazy_url,)).fetchone()
    if existing and not args.force:
        print(f"'{existing[1]}' already imported from {args.glazy_url} -- use --force to re-import")
        conn.close()
        return
    if existing and args.force:
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (existing[0],))
        conn.execute("DELETE FROM recipes WHERE id = ?", (existing[0],))

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

    cursor = conn.execute(
        "INSERT INTO recipes (name, glazy_url, firing_type, cone, atmosphere, status, imported_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            metadata["name"],
            args.glazy_url,
            args.firing_type,
            metadata["cone"],
            metadata["atmosphere"],
            metadata["status"],
            date.today().isoformat(),
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
