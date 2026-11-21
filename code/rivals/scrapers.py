"""
scrapers.py — Part 1, Step 2: one scraper per rival café.

Each scraper is handed a Playwright `page` (an open browser tab) and returns a
list of dicts, one per menu item *and size*, all with the same keys:

    {"cafe": ..., "category": ..., "item": ..., "size": ..., "price": ...}

Every café names its drink sizes S, M and L — Lakeshore pours only S and L — and
food has one price, "Each".

The three sites are built differently on purpose, so each scraper uses a
different technique from Unit 5. Before you write one, open the café in Chrome
(settings.cafe_url) and right-click → Inspect the parts you need.

The steps are described in words. You write the code.
"""

from io import StringIO
from urllib.parse import urljoin

import pandas as pd

from .cleaning import card_rows, clean_price
from .settings import CANAL_SHOP, cafe_url


def scrape_lakeshore(page) -> list[dict]:
    """Scrape Lakeshore Lattes menu cards."""
    list_of_rows = []
    page.goto(cafe_url("Lakeshore Lattes"))

    for heading in page.query_selector_all("h2.menu-section__title"):
        category = heading.inner_text()
        grid = heading.query_selector("~ div.menu-grid")
        for card in grid.query_selector_all("article.menu-card"):
            list_of_rows.extend(
                card_rows("Lakeshore Lattes", category, card.inner_text())
            )

    return list_of_rows


def scrape_hilltop(page) -> list[dict]:
    """Scrape Hilltop Grind category tables."""
    list_of_rows = []
    page.goto(cafe_url("Hilltop Grind"))

    categories = [h2.inner_text() for h2 in page.query_selector_all("#menu h2")]
    tables = pd.read_html(StringIO(page.content()))

    for category, table in zip(categories, tables):
        table = table.drop(columns="Description")
        table = table.melt(id_vars="Item", var_name="size", value_name="price")
        for _, row in table.iterrows():
            list_of_rows.append(
                {
                    "cafe": "Hilltop Grind",
                    "category": category,
                    "item": row["Item"],
                    "size": row["size"],
                    "price": clean_price(row["price"]),
                }
            )

    return list_of_rows


def scrape_canal(page, shop: str = CANAL_SHOP) -> list[dict]:
    """Scrape the dynamic Canal Street Coffee menu."""
    list_of_rows = []
    page.goto(cafe_url("Canal Street Coffee"))
    page.get_by_label("Choose your shop").select_option(shop)
    page.get_by_role("button", name="Show full menu").click()
    page.wait_for_selector("a.result-card")

    show_more = page.get_by_role("button", name="Show more")
    while show_more.is_visible():
        count = page.locator("a.result-card").count()
        show_more.click()
        page.wait_for_function(
            f"document.querySelectorAll('a.result-card').length > {count}"
        )

    hrefs = [
        card.get_attribute("href") for card in page.query_selector_all("a.result-card")
    ]

    for href in hrefs:
        page.goto(urljoin(cafe_url("Canal Street Coffee"), href))
        page.wait_for_selector("#sizes")
        item_name = page.query_selector("#item-name").inner_text()
        category = page.query_selector("#item-category").inner_text().split(" · ")[0]

        for row in page.query_selector_all("#sizes tbody tr"):
            size = row.query_selector("td:nth-child(1)").inner_text()
            price = clean_price(row.query_selector("td:nth-child(2)").inner_text())
            list_of_rows.append(
                {
                    "cafe": "Canal Street Coffee",
                    "category": category,
                    "item": item_name,
                    "size": size,
                    "price": price,
                }
            )

    return list_of_rows
