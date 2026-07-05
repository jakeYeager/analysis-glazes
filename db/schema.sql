-- Schema for db/glazes.db. This file is git-tracked; the .db file itself is
-- gitignored and rebuilt on demand via scripts/db_build.py from the
-- checkpoint CSVs (recipes/compare_recipes.csv, ingredients/ingredient_prices.csv,
-- ingredients/name_candidates_log.csv). See CLAUDE.md "Database-backed workflow".

PRAGMA foreign_keys = ON;

CREATE TABLE materials (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    price REAL,
    unit TEXT,
    bulk_price REAL,
    bulk_unit TEXT,
    price_1lb REAL,
    price_5lb REAL,
    price_10lb REAL,
    price_25lb REAL,
    price_50lb REAL,
    price_100lb REAL,
    imco_url TEXT,
    match_confidence TEXT CHECK (match_confidence IN ('exact', 'fuzzy', 'not_found')),
    notes TEXT,
    last_verified TEXT,
    glazy_material_url TEXT
);

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    glazy_url TEXT,
    firing_type TEXT CHECK (firing_type IN ('mid-fire', 'raku')),
    cone TEXT,
    atmosphere TEXT,
    status TEXT,
    imported_date TEXT,
    notes TEXT
);

CREATE TABLE recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes (id),
    material_id INTEGER NOT NULL REFERENCES materials (id),
    amount REAL NOT NULL,
    is_addition INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE price_snapshots (
    id INTEGER PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES materials (id),
    snapshot_date TEXT NOT NULL,
    price REAL,
    unit TEXT,
    bulk_price REAL,
    bulk_unit TEXT,
    price_1lb REAL,
    price_5lb REAL,
    price_10lb REAL,
    price_25lb REAL,
    price_50lb REAL,
    price_100lb REAL
);

CREATE TABLE name_candidates_log (
    id INTEGER PRIMARY KEY,
    material_name TEXT NOT NULL,
    glazy_material_url TEXT,
    alt_names_tried TEXT,
    imco_search_term TEXT,
    imco_hits INTEGER,
    suggested_sku TEXT,
    suggested_confidence TEXT,
    checked_date TEXT
);
