#!/usr/bin/env python3
"""generate_price_summary.py — regenerate the stakeholder-facing glaze price summary.

Usage:
    python3 scripts/generate_price_summary.py

Reads db/glazes.db (no scraping, no refresh — purely reports on whatever
prices are currently cached) and writes:
  - reports/glaze_price_summary.md  (stakeholder-facing report, grouped by
    firing type; PDF-exportable via scripts/md2pdf.sh)
  - reports/glaze_price_summary.csv (same data, spreadsheet-friendly)

Run scripts/price_batch.py for each recipe first if you want current prices
reflected here — this script never fetches anything itself, and never
fabricates a number for an unpriced ingredient: a recipe with any `not_found`
material gets flagged and its total is computed from confirmed ingredients
only (understated, not guessed).
"""

import csv
import re
import sqlite3
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "glazes.db"
REPORT_MD = REPO_ROOT / "reports" / "glaze_price_summary.md"
REPORT_CSV = REPO_ROOT / "reports" / "glaze_price_summary.csv"

CSV_HEADER = [
    "recipe",
    "firing_type",
    "batch_weight_lb",
    "total_cost",
    "price_per_lb",
    "oldest_last_verified",
    "unresolved_materials",
    "notes",
]

# Same quantity-parsing shape as scripts/price_batch.py's parse_quantity(),
# duplicated rather than imported so this script has no dependency on
# anything requiring Python 3.10+ syntax or playwright -- it should run
# under plain `python3` with no setup. Only the leading number matters here
# (bulk_unit values are already normalized to "lb" by price_batch.py).
QUANTITY_RE = re.compile(r"^([\d.]+(?:/[\d.]+)?)")


def parse_quantity(label: str):
    match = QUANTITY_RE.match(label.strip())
    if not match:
        raise ValueError(f"can't parse quantity from {label!r}")
    num_str = match.group(1)
    if "/" in num_str:
        numerator, denominator = num_str.split("/")
        return float(numerator) / float(denominator)
    return float(num_str)


TIER_LB_MAP = {"1lb": 1, "5lb": 5, "10lb": 10, "25lb": 25, "50lb": 50, "100lb": 100}


def select_rate(purchase_tier, bulk_price: float, bulk_unit: str, tier_prices: dict) -> float:
    """$/lb to cost this material at, honoring purchase_tier -- mirrors
    scripts/price_batch.py's select_rate() (duplicated rather than imported,
    see this file's module docstring on why: no playwright dependency here).
    'bulk' uses the cheapest true per-unit tier; a specific tier (e.g.
    '10lb') costs against that cached column instead. See "Purchase tier" in
    .claude/rules/conventions.md."""
    if not purchase_tier or purchase_tier == "bulk" or purchase_tier not in TIER_LB_MAP:
        qty = parse_quantity(bulk_unit)
        return bulk_price / qty
    tier_lb = TIER_LB_MAP[purchase_tier]
    tier_price = tier_prices.get(tier_lb)
    if tier_price is None:
        qty = parse_quantity(bulk_unit)
        return bulk_price / qty
    return tier_price / tier_lb


def summarize_recipe(conn: sqlite3.Connection, recipe_id: int, recipe_name: str, firing_type: str, recipe_notes) -> dict:
    rows = conn.execute(
        "SELECT m.canonical_name, ri.amount, m.match_confidence, m.bulk_price, m.bulk_unit, m.purchase_tier, "
        "m.price_1lb, m.price_5lb, m.price_10lb, m.price_25lb, m.price_50lb, m.price_100lb, m.last_verified "
        "FROM recipe_ingredients ri JOIN materials m ON m.id = ri.material_id "
        "WHERE ri.recipe_id = ? ORDER BY ri.id",
        (recipe_id,),
    ).fetchall()

    total_cost = 0.0
    total_weight = 0.0
    verified_dates = []
    unresolved = []

    for (
        name, amount, match_confidence, bulk_price, bulk_unit, purchase_tier,
        p1, p5, p10, p25, p50, p100, last_verified,
    ) in rows:
        total_weight += amount
        if match_confidence == "not_found" or bulk_price is None or not bulk_unit:
            unresolved.append(name)
            continue
        tier_prices = {1: p1, 5: p5, 10: p10, 25: p25, 50: p50, 100: p100}
        rate = select_rate(purchase_tier, bulk_price, bulk_unit, tier_prices)
        total_cost += amount * rate
        if last_verified:
            verified_dates.append(last_verified)

    return {
        "recipe": recipe_name,
        "firing_type": firing_type,
        "total_weight": total_weight,
        "total_cost": total_cost,
        "price_per_lb": (total_cost / total_weight) if total_weight else None,
        "oldest_priced": min(verified_dates) if verified_dates else None,
        "unresolved": unresolved,
        "recipe_notes": recipe_notes,
    }


STAKEHOLDER_NOTE_PREFIX = "STAKEHOLDER NOTE"
REFERENCE_ONLY_PREFIX = "REFERENCE ONLY"


def render_table(rows: list[dict]) -> str:
    lines = [
        "| Glaze | $/lb | Batch Weight (lb) | Total Cost | Last Priced | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        price = f"${r['price_per_lb']:.2f}" if r["price_per_lb"] is not None else "—"
        note_parts = []
        if r["unresolved"]:
            note_parts.append(f"{len(r['unresolved'])} ingredient(s) unpriced -- total may be understated")
        notes_text = r["recipe_notes"] or ""
        if notes_text.startswith(STAKEHOLDER_NOTE_PREFIX):
            note_parts.append("see Recipe Notes below -- affects how to read this $/lb figure")
        if notes_text.startswith(REFERENCE_ONLY_PREFIX):
            note_parts.append("reference only -- not in active rotation, see Recipe Notes below")
        notes = "; ".join(note_parts)
        lines.append(
            f"| {r['recipe']} | {price} | {r['total_weight']:.2f} | ${r['total_cost']:.2f} | "
            f"{r['oldest_priced'] or '—'} | {notes} |"
        )
    return "\n".join(lines)


def render_recipe_notes(rows: list[dict]) -> str:
    flagged = [
        r for r in rows
        if (r["recipe_notes"] or "").startswith(STAKEHOLDER_NOTE_PREFIX)
        or (r["recipe_notes"] or "").startswith(REFERENCE_ONLY_PREFIX)
    ]
    if not flagged:
        return ""
    entries = [f"**{r['recipe']}** — {r['recipe_notes']}" for r in sorted(flagged, key=lambda r: r["recipe"])]
    return "## Recipe Notes\n\nFull text of every note flagged \"see Recipe Notes below\" in the tables above.\n\n" + "\n\n".join(entries)


def write_report(summaries: list[dict]) -> None:
    today = date.today().isoformat()
    firing_types = sorted({s["firing_type"] or "unspecified" for s in summaries})

    sections = []
    for firing_type in firing_types:
        group = [s for s in summaries if (s["firing_type"] or "unspecified") == firing_type]
        heading = firing_type.replace("-", " ").title()
        sections.append(f"## {heading} glazes\n\n{render_table(group)}")

    recipe_notes_section = render_recipe_notes(summaries)
    if recipe_notes_section:
        sections.append(recipe_notes_section)

    body = f"""# Glaze Price Summary

| | |
|---|---|
| **Date** | {today} |
| **Last Updated** | {today} |
| **Document Version** | 2.1 |
| **Generation Model** | Claude Sonnet 5 |
| **Author** | Jake Yeager |

This is the current per-lb cost of every glaze recipe tracked in `db/glazes.db`, regenerated directly from it via `scripts/generate_price_summary.py` — a quick reference for pricing/rotation decisions, not a one-off analysis. Regenerate it (and re-run `scripts/price_batch.py` first if you want fresher prices) before sharing an updated copy with stakeholders. "Last Priced" is the oldest `last_verified` date among a recipe's ingredients — the number is only as fresh as its stalest ingredient. A recipe with unpriced ingredients shows its total computed from confirmed ingredients only; it is not a guess, but it is incomplete. Base-glaze materials (frits, feldspars, clays, silica) are costed at the cheapest bulk rate, since that's realistically how they're bought; colorants, opacifiers, and Lithium Carbonate are costed at a smaller 10lb rate instead, since those are typically bought in much smaller quantities than a full bag. **`$/lb` is mixing cost, not per-piece cost** — it says nothing about how thickly a glaze gets applied, so a thin-coat glaze and a thick-dipped one at the same `$/lb` do not cost the same to actually use. A recipe flagged "see Recipe Notes below" has a specific caveat about this worth reading before comparing it to others on `$/lb` alone — full text of each is in the "Recipe Notes" section below the price tables.

{(chr(10) * 2).join(sections)}

## Source files referenced

- `db/glazes.db` — recipes, materials, and pricing (see `.claude/CLAUDE.md` for the full schema)  
- `reports/glaze_price_summary.csv` — this same data in spreadsheet form  
"""
    REPORT_MD.write_text(body)


def write_csv(summaries: list[dict]) -> None:
    with open(REPORT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        for s in summaries:
            writer.writerow(
                [
                    s["recipe"],
                    s["firing_type"] or "",
                    f"{s['total_weight']:.2f}",
                    f"{s['total_cost']:.2f}",
                    f"{s['price_per_lb']:.2f}" if s["price_per_lb"] is not None else "",
                    s["oldest_priced"] or "",
                    "; ".join(s["unresolved"]),
                    s["recipe_notes"] or "",
                ]
            )


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} doesn't exist -- run scripts/db_build.py first")

    conn = sqlite3.connect(DB_PATH)
    recipes = conn.execute("SELECT id, name, firing_type, notes FROM recipes ORDER BY firing_type, name").fetchall()
    summaries = [summarize_recipe(conn, rid, name, firing_type, notes) for rid, name, firing_type, notes in recipes]
    conn.close()

    write_report(summaries)
    write_csv(summaries)
    print(f"wrote {REPORT_MD} and {REPORT_CSV} ({len(summaries)} recipes)")


if __name__ == "__main__":
    main()
