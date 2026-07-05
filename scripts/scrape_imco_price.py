#!/usr/bin/env python3
"""scrape_imco_price.py — pull the full weight-tier price table off one IMCO product page.

Usage:
    uv run --with playwright scripts/scrape_imco_price.py <imco_product_url>

One-time setup (real browser binary, not ephemeral like the rest of this
project's tooling):
    uv run --with playwright playwright install chromium

Automates the technique originally documented by hand in
docs/archive/price_list_run_notes.md: IMCO (Square Online) product pages
expose a weight/quantity <select>; picking
each option updates the displayed price without a page reload. This script
loops every option, dispatches a `change` event, and reads back whichever
"$X.XX" text on the page changed as a result — rather than hardcoding a CSS
selector for the price element, since that wasn't confirmed against a live
page in the session that wrote this script. Spot-check output against a
product page in a real browser before trusting it for a price you haven't
seen before; the run notes call out confirmed non-monotonic bulk tiers
(a larger quantity costing more per unit than a smaller one), so sanity-check
new results the same way.

Prints a JSON list of {"label": <option text>, "price": <matched $ amount or
null>} to stdout, one entry per <select> option, in DOM order.
"""

import json
import re
import sys

from playwright.sync_api import sync_playwright

PRICE_RE = re.compile(r"\$[\d,]+\.\d{2}")


def scrape(url: str, select_index: int = 0) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="load")
        page.wait_for_timeout(1000)

        selects = page.locator("select")
        count = selects.count()
        if count == 0:
            browser.close()
            raise RuntimeError(f"no <select> element found on page: {url}")
        select = selects.nth(select_index)

        options = select.evaluate(
            "el => Array.from(el.options)"
            ".map(o => ({value: o.value, label: o.textContent.trim(), disabled: o.disabled}))"
        )
        options = [o for o in options if not o["disabled"] and o["value"]]

        results = []
        for option in options:
            select.select_option(value=option["value"])
            page.wait_for_timeout(400)
            body_text = page.inner_text("body")
            match = PRICE_RE.search(body_text)
            results.append({"label": option["label"], "price": match.group(0) if match else None})

        browser.close()
        return results


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <imco_product_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    try:
        tiers = scrape(url)
    except Exception as exc:
        print(f"error scraping {url}: {exc}", file=sys.stderr)
        print(
            "if this is a missing-browser error, run: "
            "uv run --with playwright playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(tiers, indent=2))


if __name__ == "__main__":
    main()
