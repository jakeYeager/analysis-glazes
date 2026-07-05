#!/usr/bin/env python3
"""db_build.py — hydrate db/glazes.db from the checkpoint CSVs + db/schema.sql.

Usage:
    python3 scripts/db_build.py

Run this whenever db/glazes.db doesn't exist yet (fresh clone, new session)
or you want to discard local DB state and rebuild from the last committed
CSV checkpoint. Idempotent: drops and recreates every table each run, so
it's always safe to re-run — db/glazes.db is a disposable working copy, not
the source of truth. The source of truth is the three CSVs this reads:
recipes/compare_recipes.csv, ingredients/ingredient_prices.csv,
ingredients/name_candidates_log.csv. Run scripts/db_export.py to flush DB
state back to those CSVs before committing.

recipes/compare_recipes.csv doesn't yet track firing_type (mid-fire vs.
raku) — FIRING_TYPE_OVERRIDES below fills that in for recipes known when
this script was written. New recipes without an override default to
mid-fire with a warning; correct firing_type by hand in the DB (and flush it
back with db_export.py) until compare_recipes.csv tracks it directly.
"""

import csv
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQL = REPO_ROOT / "db" / "schema.sql"
DB_PATH = REPO_ROOT / "db" / "glazes.db"
RECIPES_CSV = REPO_ROOT / "recipes" / "compare_recipes.csv"
PRICES_CSV = REPO_ROOT / "ingredients" / "ingredient_prices.csv"
CANDIDATES_CSV = REPO_ROOT / "ingredients" / "name_candidates_log.csv"

# Cone 5-6 rules out raku (per docs/price_list_run_notes.md) -- both
# existing recipes are mid-fire. Add entries here for any recipe whose
# firing_type isn't obvious, until compare_recipes.csv tracks it directly.
FIRING_TYPE_OVERRIDES = {
    "Frogskin": "mid-fire",
    "Giggin' for Salvation": "mid-fire",
}

MATERIAL_COLUMNS = [
    "canonical_name",
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
    "imco_url",
    "match_confidence",
    "notes",
    "last_verified",
    "glazy_material_url",
]

TIER_FLOAT_FIELDS = ["price", "bulk_price", "price_1lb", "price_5lb", "price_10lb", "price_25lb", "price_50lb", "price_100lb"]


def to_float_or_none(value: str):
    value = value.strip()
    return float(value) if value else None


def build_materials(conn: sqlite3.Connection) -> None:
    with open(PRICES_CSV, newline="") as f:
        for row in csv.DictReader(f):
            values = {col: row.get(col, "") for col in MATERIAL_COLUMNS}
            values["canonical_name"] = row["material_name"]
            for field in TIER_FLOAT_FIELDS:
                values[field] = to_float_or_none(values[field])
            conn.execute(
                f"INSERT INTO materials ({', '.join(MATERIAL_COLUMNS)}) "
                f"VALUES ({', '.join('?' for _ in MATERIAL_COLUMNS)})",
                [values[col] for col in MATERIAL_COLUMNS],
            )


def build_recipes_and_ingredients(conn: sqlite3.Connection) -> None:
    with open(RECIPES_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    recipe_ids: dict[str, int] = {}
    for row in rows:
        name = row["recipe"]
        if name in recipe_ids:
            continue
        firing_type = FIRING_TYPE_OVERRIDES.get(name)
        if firing_type is None:
            print(f"warning: no firing_type override for '{name}', defaulting to mid-fire", file=sys.stderr)
            firing_type = "mid-fire"
        cursor = conn.execute(
            "INSERT INTO recipes (name, glazy_url, firing_type) VALUES (?, ?, ?)",
            (name, row["glazy_url"] or None, firing_type),
        )
        recipe_ids[name] = cursor.lastrowid

    material_ids = {
        row[0]: row[1]
        for row in conn.execute("SELECT canonical_name, id FROM materials")
    }

    for row in rows:
        material = row["material"]
        if material not in material_ids:
            print(f"warning: '{material}' not found in materials, skipping ingredient row", file=sys.stderr)
            continue
        conn.execute(
            "INSERT INTO recipe_ingredients (recipe_id, material_id, amount, is_addition, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                recipe_ids[row["recipe"]],
                material_ids[material],
                float(row["amount"]),
                1 if row["is_addition"].strip().lower() == "true" else 0,
                row["notes"] or None,
            ),
        )


def build_name_candidates_log(conn: sqlite3.Connection) -> None:
    with open(CANDIDATES_CSV, newline="") as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT INTO name_candidates_log "
                "(material_name, glazy_material_url, alt_names_tried, imco_search_term, "
                "imco_hits, suggested_sku, suggested_confidence, checked_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["material_name"],
                    row["glazy_material_url"] or None,
                    row["alt_names_tried"] or None,
                    row["imco_search_term"] or None,
                    int(row["imco_hits"]) if row["imco_hits"].strip() else None,
                    row["suggested_sku"] or None,
                    row["suggested_confidence"] or None,
                    row["checked_date"] or None,
                ),
            )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL.read_text())

    build_materials(conn)
    build_recipes_and_ingredients(conn)
    build_name_candidates_log(conn)

    conn.commit()

    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ["materials", "recipes", "recipe_ingredients", "name_candidates_log"]
    }
    conn.close()

    print(f"built {DB_PATH} from CSV checkpoints:")
    for table, count in counts.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    main()
