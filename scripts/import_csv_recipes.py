#!/usr/bin/env python3
"""import_csv_recipes.py — bulk-import recipes from a wide-format (pivoted) CSV.

Usage:
    python3 scripts/import_csv_recipes.py <csv_path> --firing-type mid-fire|raku

For recipes gathered somewhere other than Glazy (e.g. a personal spreadsheet)
that don't have a glazy_url yet. Expects the CSV shape exported by Google
Sheets for this studio's recipe tracker: first column is material name,
remaining columns are one per recipe (header cell = recipe name, possibly
wrapped across multiple lines within the cell — collapsed to single-line
whitespace here, and any trailing "*" stripped). Each material row lists
that material's amount in the recipe's column, blank if unused.

Skips a column entirely if a recipe with that name already exists — these
aren't meant to be repeatedly re-imported the way Glazy recipes are (no
--force). Skips a material row that's blank across every recipe (an unused
template row).

New materials get match_confidence='not_found', same as
import_glazy_recipe.py — price them via find_material_candidates.py /
price_batch.py afterward. KNOWN_MATERIAL_ALIASES maps a known synonym
straight to the existing material (e.g. "EPK" -> "EP Kaolin") instead of
creating a duplicate — same spirit as KNOWN_MANUFACTURER_PREFIXES in
import_glazy_recipe.py, just an exact-name synonym rather than a prefix.

is_addition is set to false for every ingredient here, since this CSV shape
has no base/addition marker (unlike a Glazy recipe page's "Total base
recipe" subtotal row — see import_glazy_recipe.py). Each imported recipe's
`notes` flags this explicitly: once you manually add it to Glazy, re-run
`import_glazy_recipe.py <url> --force` to pick up the real base/addition
split from the live page.
"""

import argparse
import csv
import sqlite3
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"

# Known exact-name synonyms for materials already in the database, checked
# before creating a new materials row. Keep in sync with the reasoning in
# .claude/rules/conventions.md "Material name variants".
KNOWN_MATERIAL_ALIASES = {
    "EPK": "EP Kaolin",  # Edgar Plastic Kaolin -- same product IMCO lists as EP Kaolin
}

PENDING_ADDITION_NOTE = (
    "Bulk-imported from a personal spreadsheet, not yet on Glazy -- is_addition "
    "defaulted to false for every ingredient since this source has no base/addition "
    "marker. Re-run import_glazy_recipe.py <url> --force once this recipe is added to "
    "Glazy to pick up the real base/addition split."
)


def get_or_create_material(conn: sqlite3.Connection, name: str) -> int:
    name = KNOWN_MATERIAL_ALIASES.get(name, name)
    row = conn.execute("SELECT id FROM materials WHERE canonical_name = ?", (name,)).fetchone()
    if row:
        return row[0]
    cursor = conn.execute(
        "INSERT INTO materials (canonical_name, match_confidence, notes) VALUES (?, 'not_found', ?)",
        (name, f"Auto-created by import_csv_recipes.py on {date.today().isoformat()}."),
    )
    print(f"  new material: {name} (not_found, needs pricing)")
    return cursor.lastrowid


def clean_header(cell: str) -> str:
    return " ".join(cell.split()).rstrip("*").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--firing-type", choices=["mid-fire", "raku"], required=True)
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    with open(args.csv_path, newline="") as f:
        rows = list(csv.reader(f))
    recipe_names = [clean_header(h) for h in rows[0][1:]]

    conn = sqlite3.connect(DB_PATH)
    today = date.today().isoformat()

    imported = 0
    skipped_existing = []
    for col_index, recipe_name in enumerate(recipe_names, start=1):
        if conn.execute("SELECT id FROM recipes WHERE name = ?", (recipe_name,)).fetchone():
            skipped_existing.append(recipe_name)
            continue

        ingredients = []
        for row in rows[1:]:
            material = row[0].strip()
            if not material or len(row) <= col_index or not row[col_index].strip():
                continue
            ingredients.append((material, float(row[col_index])))
        if not ingredients:
            print(f"  skipping '{recipe_name}': no ingredients found")
            continue

        cursor = conn.execute(
            "INSERT INTO recipes (name, firing_type, imported_date, notes) VALUES (?, ?, ?, ?)",
            (recipe_name, args.firing_type, today, PENDING_ADDITION_NOTE),
        )
        recipe_id = cursor.lastrowid
        for material, amount in ingredients:
            material_id = get_or_create_material(conn, material)
            conn.execute(
                "INSERT INTO recipe_ingredients (recipe_id, material_id, amount, is_addition) VALUES (?, ?, ?, 0)",
                (recipe_id, material_id, amount),
            )
        imported += 1
        print(f"imported '{recipe_name}' ({len(ingredients)} ingredients)")

    conn.commit()
    conn.close()

    print(f"\n{imported} recipe(s) imported.")
    if skipped_existing:
        print(f"{len(skipped_existing)} skipped (recipe name already exists): {', '.join(skipped_existing)}")


if __name__ == "__main__":
    main()
