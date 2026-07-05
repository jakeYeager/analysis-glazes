#!/usr/bin/env python3
"""db_export.py — flush db/glazes.db state back to the checkpoint CSVs.

Usage:
    python3 scripts/db_export.py

Run this before committing any change made through the DB (price refreshes,
new recipes, candidate lookups) so the git-tracked CSVs stay the durable
record of the DB's state. Overwrites recipes/recipe_metadata.csv,
recipes/compare_recipes.csv, ingredients/ingredient_prices.csv, and
ingredients/name_candidates_log.csv in place, preserving their existing
column order/shape.
"""

import csv
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"
METADATA_CSV = REPO_ROOT / "recipes" / "recipe_metadata.csv"
RECIPES_CSV = REPO_ROOT / "recipes" / "compare_recipes.csv"
PRICES_CSV = REPO_ROOT / "ingredients" / "ingredient_prices.csv"
CANDIDATES_CSV = REPO_ROOT / "ingredients" / "name_candidates_log.csv"

METADATA_HEADER = ["name", "glazy_url", "firing_type", "cone", "atmosphere", "status", "imported_date", "notes"]

PRICES_HEADER = [
    "material_name",
    "price",
    "unit",
    "bulk_price",
    "bulk_unit",
    "price_1lb",
    "price_5lb",
    "price_10lb",
    "price_25lb",
    "price_50lb",
    "price_100lb",
    "purchase_tier",
    "imco_url",
    "match_confidence",
    "notes",
    "last_verified",
    "glazy_material_url",
]
RECIPES_HEADER = ["recipe", "glazy_url", "material", "amount", "is_addition", "notes"]
CANDIDATES_HEADER = [
    "material_name",
    "glazy_material_url",
    "alt_names_tried",
    "imco_search_term",
    "imco_hits",
    "suggested_sku",
    "suggested_confidence",
    "checked_date",
]


def fmt_float(value) -> str:
    return f"{value:.2f}" if value is not None else ""


def export_materials(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT canonical_name, price, unit, bulk_price, bulk_unit, price_1lb, price_5lb, "
        "price_10lb, price_25lb, price_50lb, price_100lb, purchase_tier, imco_url, match_confidence, notes, "
        "last_verified, glazy_material_url FROM materials ORDER BY id"
    ).fetchall()

    with open(PRICES_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRICES_HEADER)
        for row in rows:
            (
                name, price, unit, bulk_price, bulk_unit, p1, p5, p10, p25, p50, p100,
                purchase_tier, imco_url, match_confidence, notes, last_verified, glazy_material_url,
            ) = row
            writer.writerow(
                [
                    name,
                    fmt_float(price),
                    unit or "",
                    fmt_float(bulk_price),
                    bulk_unit or "",
                    fmt_float(p1),
                    fmt_float(p5),
                    fmt_float(p10),
                    fmt_float(p25),
                    fmt_float(p50),
                    fmt_float(p100),
                    purchase_tier or "bulk",
                    imco_url or "",
                    match_confidence or "",
                    notes or "",
                    last_verified or "",
                    glazy_material_url or "",
                ]
            )


def export_recipe_metadata(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT name, glazy_url, firing_type, cone, atmosphere, status, imported_date, notes "
        "FROM recipes ORDER BY id"
    ).fetchall()

    with open(METADATA_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(METADATA_HEADER)
        for name, glazy_url, firing_type, cone, atmosphere, status, imported_date, notes in rows:
            writer.writerow(
                [
                    name,
                    glazy_url or "",
                    firing_type or "",
                    cone or "",
                    atmosphere or "",
                    status or "",
                    imported_date or "",
                    notes or "",
                ]
            )


def export_recipes(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT r.name, r.glazy_url, m.canonical_name, ri.amount, ri.is_addition, ri.notes "
        "FROM recipe_ingredients ri "
        "JOIN recipes r ON r.id = ri.recipe_id "
        "JOIN materials m ON m.id = ri.material_id "
        "ORDER BY ri.id"
    ).fetchall()

    with open(RECIPES_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RECIPES_HEADER)
        for recipe_name, glazy_url, material, amount, is_addition, notes in rows:
            writer.writerow(
                [
                    recipe_name,
                    glazy_url or "",
                    material,
                    f"{amount:.2f}",
                    "true" if is_addition else "false",
                    notes or "",
                ]
            )


def export_name_candidates_log(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT material_name, glazy_material_url, alt_names_tried, imco_search_term, "
        "imco_hits, suggested_sku, suggested_confidence, checked_date "
        "FROM name_candidates_log ORDER BY id"
    ).fetchall()

    with open(CANDIDATES_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CANDIDATES_HEADER)
        for (
            material_name, glazy_material_url, alt_names_tried, imco_search_term,
            imco_hits, suggested_sku, suggested_confidence, checked_date,
        ) in rows:
            writer.writerow(
                [
                    material_name,
                    glazy_material_url or "",
                    alt_names_tried or "",
                    imco_search_term or "",
                    imco_hits if imco_hits is not None else "",
                    suggested_sku or "",
                    suggested_confidence or "",
                    checked_date or "",
                ]
            )


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    conn = sqlite3.connect(DB_PATH)
    export_materials(conn)
    export_recipe_metadata(conn)
    export_recipes(conn)
    export_name_candidates_log(conn)
    conn.close()

    print(f"exported {DB_PATH} to {PRICES_CSV}, {METADATA_CSV}, {RECIPES_CSV}, {CANDIDATES_CSV}")


if __name__ == "__main__":
    main()
