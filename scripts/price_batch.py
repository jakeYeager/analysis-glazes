#!/usr/bin/env python3
"""price_batch.py — price a full recipe batch, refreshing only stale/missing prices.

Usage:
    uv run --with playwright scripts/price_batch.py "<recipe name>"

For each material in the named recipe (from recipes/compare_recipes.csv):
  - if ingredient_prices.csv has no confirmed price (missing row, or
    match_confidence == not_found): shells out to find_material_candidates.py
    to log IMCO candidates via Glazy's alternate-name list, flags it, and
    excludes it from the total (never fabricates a price).
  - if confirmed and last_verified is within STALENESS_DAYS: uses the cached
    price as-is.
  - if confirmed but stale: shells out to scrape_imco_price.py for a fresh
    tier table, updates that row's price fields + last_verified, and marks
    it refreshed.

If anything was refreshed, ingredient_prices.csv is rewritten in place and a
dated copy is archived to ingredients/snapshots/. Prints an itemized cost
table (mirroring reports/frit3134_vs_gerstley_borate_cost_comparison.md)
plus which materials were cached vs. refreshed vs. unresolved. This script
produces numbers only — turning them into a narrative report stays a manual
step, since that requires judgment a script can't apply.
"""

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

STALENESS_DAYS = 90

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPES_CSV = REPO_ROOT / "recipes" / "compare_recipes.csv"
PRICES_CSV = REPO_ROOT / "ingredients" / "ingredient_prices.csv"
SNAPSHOTS_DIR = REPO_ROOT / "ingredients" / "snapshots"

QUANTITY_RE = re.compile(r"^([\d.]+(?:/[\d.]+)?)\s*(.*)$")


def parse_quantity(label: str) -> tuple[float, str]:
    match = QUANTITY_RE.match(label.strip())
    if not match:
        raise ValueError(f"can't parse quantity from {label!r}")
    num_str, unit = match.groups()
    unit = re.sub(r"\(.*\)", "", unit).strip()
    if "/" in num_str:
        numerator, denominator = num_str.split("/")
        value = float(numerator) / float(denominator)
    else:
        value = float(num_str)
    return value, unit


def parse_price(price_str: str) -> float:
    return float(price_str.replace("$", "").replace(",", ""))


def load_recipe(recipe_name: str) -> list[dict]:
    with open(RECIPES_CSV, newline="") as f:
        rows = [row for row in csv.DictReader(f) if row["recipe"] == recipe_name]
    if not rows:
        print(f"no rows found for recipe '{recipe_name}' in {RECIPES_CSV}", file=sys.stderr)
        sys.exit(1)
    return rows


def load_prices() -> tuple[list[str], dict[str, dict]]:
    with open(PRICES_CSV, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        prices = {row["material_name"]: row for row in reader}
    return fieldnames, prices


def write_prices(path: Path, fieldnames: list[str], prices: dict[str, dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prices.values())


def is_stale(price_row: dict) -> bool:
    last_verified = price_row.get("last_verified", "").strip()
    if not last_verified:
        return True
    return (date.today() - date.fromisoformat(last_verified)).days > STALENESS_DAYS


def refresh_price_row(price_row: dict) -> None:
    result = subprocess.run(
        ["uv", "run", "--with", "playwright", "scripts/scrape_imco_price.py", price_row["imco_url"]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  refresh failed for {price_row['material_name']}: {result.stderr.strip()}", file=sys.stderr)
        return

    tiers = json.loads(result.stdout)
    parsed = []
    for tier in tiers:
        if tier["price"] is None:
            continue
        qty, unit = parse_quantity(tier["label"])
        parsed.append((qty, unit, parse_price(tier["price"])))
    if not parsed:
        print(f"  refresh returned no usable tiers for {price_row['material_name']}", file=sys.stderr)
        return

    smallest = min(parsed, key=lambda t: t[0])
    cheapest_per_unit = min(parsed, key=lambda t: t[2] / t[0])

    price_row["price"] = f"{smallest[2]:.2f}"
    price_row["unit"] = f"{smallest[0]:g} {smallest[1]}"
    price_row["bulk_price"] = f"{cheapest_per_unit[2]:.2f}"
    price_row["bulk_unit"] = f"{cheapest_per_unit[0]:g} {cheapest_per_unit[1]}"
    price_row["last_verified"] = date.today().isoformat()


def log_candidates(recipe_glazy_url: str, material_name: str) -> None:
    if not recipe_glazy_url:
        print(f"  no glazy_url on this recipe row — can't look up candidates for {material_name}", file=sys.stderr)
        return
    subprocess.run(
        ["uv", "run", "--with", "playwright", "scripts/find_material_candidates.py", recipe_glazy_url, material_name],
        cwd=REPO_ROOT,
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} \"<recipe name>\"", file=sys.stderr)
        sys.exit(1)

    recipe_name = sys.argv[1]
    recipe_rows = load_recipe(recipe_name)
    fieldnames, prices = load_prices()

    line_items = []
    unresolved = []
    any_refreshed = False

    for row in recipe_rows:
        material = row["material"]
        amount = float(row["amount"])
        price_row = prices.get(material)

        if price_row is None or price_row.get("match_confidence") == "not_found":
            print(f"{material}: unresolved (no confirmed price) — logging candidates")
            log_candidates(row.get("glazy_url", ""), material)
            unresolved.append(material)
            continue

        if is_stale(price_row):
            print(f"{material}: stale (last_verified={price_row.get('last_verified') or 'never'}) — refreshing")
            refresh_price_row(price_row)
            any_refreshed = True
            status = "refreshed"
        else:
            status = "cached"

        bulk_qty, _ = parse_quantity(price_row["bulk_unit"])
        rate = parse_price(price_row["bulk_price"]) / bulk_qty
        cost = amount * rate
        line_items.append(
            {
                "material": material,
                "amount": amount,
                "rate": rate,
                "cost": cost,
                "status": status,
            }
        )

    if any_refreshed:
        write_prices(PRICES_CSV, fieldnames, prices)
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = SNAPSHOTS_DIR / f"{date.today().isoformat()}-ingredient_prices.csv"
        write_prices(snapshot_path, fieldnames, prices)
        print(f"\nwrote refreshed prices to {PRICES_CSV} and snapshot {snapshot_path}")

    print(f"\n{recipe_name} — itemized cost")
    print(f"{'Material':<20}{'Amount':>10}{'$/lb':>10}{'Cost':>12}  Status")
    total_cost = 0.0
    total_weight = 0.0
    for item in line_items:
        print(
            f"{item['material']:<20}{item['amount']:>10.2f}{item['rate']:>10.2f}{item['cost']:>12.2f}  {item['status']}"
        )
        total_cost += item["cost"]
        total_weight += item["amount"]
    print(f"{'Total':<20}{total_weight:>10.2f}{'':>10}{total_cost:>12.2f}")
    if total_weight:
        print(f"= ${total_cost / total_weight:.2f}/lb")

    if unresolved:
        print(f"\nunresolved (excluded from total, need manual price confirmation): {', '.join(unresolved)}")


if __name__ == "__main__":
    main()
