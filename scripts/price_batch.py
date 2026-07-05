#!/usr/bin/env python3
"""price_batch.py — price a full recipe batch, refreshing only stale/missing prices.

Usage:
    uv run --with playwright scripts/price_batch.py "<recipe name>"

Reads/writes db/glazes.db directly (run scripts/db_build.py first if it
doesn't exist yet). For each material in the named recipe:
  - if match_confidence == 'not_found': shells out to
    find_material_candidates.py to log IMCO candidates via Glazy's
    alternate-name list, flags it, and excludes it from the total (never
    fabricates a price).
  - if confirmed and last_verified is within STALENESS_DAYS: uses the cached
    price as-is.
  - if confirmed but stale: shells out to scrape_imco_price.py for a fresh
    tier table, updates that material's row in place, inserts a
    price_snapshots row, and marks it refreshed.

Prints an itemized cost table (mirroring
reports/frit3134_vs_gerstley_borate_cost_comparison.md) plus which materials
were cached vs. refreshed vs. unresolved. Run scripts/db_export.py afterward
to flush any changes back to the checkpoint CSVs before committing. This
script produces numbers only — turning them into a narrative report stays a
manual step, since that requires judgment a script can't apply.
"""

import json
import re
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

STALENESS_DAYS = 90

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"

QUANTITY_RE = re.compile(r"^([\d.]+(?:/[\d.]+)?)\s*(.*)$")
POUND_UNIT_RE = re.compile(r"^(lbs?|#|pounds?)$", re.IGNORECASE)


def normalize_unit(unit: str) -> str:
    """IMCO's option labels aren't consistent about how they spell "pounds"
    across products (seen live: "lb", "lbs", "LBS", "#") — collapse any of
    those to "lb" so the sheet doesn't reintroduce the inconsistency this
    refactor removed. Leaves anything else (e.g. a genuine non-lb unit)
    untouched."""
    return "lb" if POUND_UNIT_RE.match(unit.strip()) else unit


def parse_quantity(label: str) -> tuple[float, str]:
    match = QUANTITY_RE.match(label.strip())
    if not match:
        raise ValueError(f"can't parse quantity from {label!r}")
    num_str, unit = match.groups()
    unit = normalize_unit(re.sub(r"\(.*\)", "", unit).strip())
    if "/" in num_str:
        numerator, denominator = num_str.split("/")
        value = float(numerator) / float(denominator)
    else:
        value = float(num_str)
    return value, unit


def parse_price(price_str: str) -> float:
    return float(price_str.replace("$", "").replace(",", ""))


def is_stale(last_verified: str | None) -> bool:
    if not last_verified:
        return True
    return (date.today() - date.fromisoformat(last_verified)).days > STALENESS_DAYS


# Standard tier columns tracked on materials. Per .claude/rules/conventions.md:
# sub-1lb tiers aren't tracked (recipes here are always priced in
# whole-lb-and-up quantities), and a tier whose real quantity doesn't land on
# one of these exactly (e.g. a 25kg/55.14lb bag) gets bucketed into the
# closest standard column.
STANDARD_TIER_LBS = [1, 5, 10, 25, 50, 100]


def bucket_tiers(parsed: list[tuple[float, str, float]]) -> dict[int, tuple[float, float]]:
    """Map (qty, unit, price) tiers onto the closest standard column.

    Returns {bucket_lb: (price, actual_qty)}, keeping only the closest tier
    per bucket if more than one maps to it.
    """
    buckets: dict[int, tuple[float, float]] = {}
    for qty, _unit, price in parsed:
        bucket = min(STANDARD_TIER_LBS, key=lambda b: abs(b - qty))
        if bucket not in buckets or abs(qty - bucket) < abs(buckets[bucket][1] - bucket):
            buckets[bucket] = (price, qty)
    return buckets


def refresh_material(conn: sqlite3.Connection, material_id: int, material_name: str, imco_url: str) -> tuple[float, str] | None:
    """Rescrape imco_url, update the materials row + insert a price_snapshots
    row. Returns the new (bulk_price, bulk_unit), or None if the refresh failed."""
    result = subprocess.run(
        ["uv", "run", "--with", "playwright", "scripts/scrape_imco_price.py", imco_url],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  refresh failed for {material_name}: {result.stderr.strip()}", file=sys.stderr)
        return None

    tiers = json.loads(result.stdout)
    parsed = []
    for tier in tiers:
        if tier["price"] is None:
            continue
        qty, unit = parse_quantity(tier["label"])
        if qty < 1:
            continue  # sub-1lb tiers aren't tracked, see STANDARD_TIER_LBS comment
        parsed.append((qty, unit, parse_price(tier["price"])))
    if not parsed:
        print(f"  refresh returned no usable tiers for {material_name}", file=sys.stderr)
        return None

    smallest = min(parsed, key=lambda t: t[0])
    cheapest_per_unit = min(parsed, key=lambda t: t[2] / t[0])
    price = smallest[2]
    unit = f"{smallest[0]:g} {smallest[1]}"
    bulk_price = cheapest_per_unit[2]
    bulk_unit = f"{cheapest_per_unit[0]:g} {cheapest_per_unit[1]}"
    last_verified = date.today().isoformat()

    buckets = bucket_tiers(parsed)
    tier_values = {}
    for bucket in STANDARD_TIER_LBS:
        if bucket in buckets:
            bucket_price, actual_qty = buckets[bucket]
            tier_values[bucket] = bucket_price
            if abs(actual_qty - bucket) > 0.01:
                print(
                    f"  {material_name}: bucketed {actual_qty:g} lb tier into price_{bucket}lb "
                    "(approximation) -- update notes if this needs disclosing",
                    file=sys.stderr,
                )
        else:
            tier_values[bucket] = None

    conn.execute(
        "UPDATE materials SET price=?, unit=?, bulk_price=?, bulk_unit=?, "
        "price_1lb=?, price_5lb=?, price_10lb=?, price_25lb=?, price_50lb=?, price_100lb=?, "
        "last_verified=? WHERE id=?",
        (
            price, unit, bulk_price, bulk_unit,
            tier_values[1], tier_values[5], tier_values[10], tier_values[25], tier_values[50], tier_values[100],
            last_verified, material_id,
        ),
    )
    conn.execute(
        "INSERT INTO price_snapshots (material_id, snapshot_date, price, unit, bulk_price, bulk_unit, "
        "price_1lb, price_5lb, price_10lb, price_25lb, price_50lb, price_100lb) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            material_id, last_verified, price, unit, bulk_price, bulk_unit,
            tier_values[1], tier_values[5], tier_values[10], tier_values[25], tier_values[50], tier_values[100],
        ),
    )
    conn.commit()
    return bulk_price, bulk_unit


def log_candidates(recipe_glazy_url: str | None, material_name: str) -> None:
    if not recipe_glazy_url:
        print(f"  no glazy_url on this recipe — can't look up candidates for {material_name}", file=sys.stderr)
        return
    subprocess.run(
        ["uv", "run", "--with", "playwright", "scripts/find_material_candidates.py", recipe_glazy_url, material_name],
        cwd=REPO_ROOT,
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} \"<recipe name>\"", file=sys.stderr)
        sys.exit(1)

    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    recipe_name = sys.argv[1]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT m.id AS material_id, m.canonical_name AS material, m.imco_url, m.match_confidence, "
        "m.bulk_price, m.bulk_unit, m.last_verified, ri.amount, r.glazy_url "
        "FROM recipe_ingredients ri "
        "JOIN recipes r ON r.id = ri.recipe_id "
        "JOIN materials m ON m.id = ri.material_id "
        "WHERE r.name = ? ORDER BY ri.id",
        (recipe_name,),
    ).fetchall()
    if not rows:
        print(f"no rows found for recipe '{recipe_name}' in {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    line_items = []
    unresolved = []

    for row in rows:
        material = row["material"]
        amount = row["amount"]

        if row["match_confidence"] == "not_found":
            print(f"{material}: unresolved (no confirmed price) — logging candidates")
            log_candidates(row["glazy_url"], material)
            unresolved.append(material)
            continue

        bulk_price, bulk_unit = row["bulk_price"], row["bulk_unit"]
        if is_stale(row["last_verified"]):
            print(f"{material}: stale (last_verified={row['last_verified'] or 'never'}) — refreshing")
            refreshed = refresh_material(conn, row["material_id"], material, row["imco_url"])
            if refreshed is None:
                unresolved.append(material)
                continue
            bulk_price, bulk_unit = refreshed
            status = "refreshed"
        else:
            status = "cached"

        bulk_qty, _ = parse_quantity(bulk_unit)
        rate = bulk_price / bulk_qty
        cost = amount * rate
        line_items.append({"material": material, "amount": amount, "rate": rate, "cost": cost, "status": status})

    conn.close()

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
