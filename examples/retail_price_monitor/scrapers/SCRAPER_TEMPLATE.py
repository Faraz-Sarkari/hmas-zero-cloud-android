"""
SCRAPER TEMPLATE — Add a new site to the retail price monitor
=============================================================
Copy this file, rename it to your site (e.g. mynewsite.py),
and fill in the sections marked with TODO.

The Data Extraction Agent auto-loads every .py file in this folder
that exposes a `scrape(session, config) -> list` function.
No other changes needed anywhere.

Return format:
    Each result is a tuple: (name, price, source, url)
    - name:   product title string as shown on the site
    - price:  integer price in the local currency (no symbols)
    - source: short site label used in notifications, e.g. "MySite"
    - url:    direct link to the product listing
"""

from bs4 import BeautifulSoup
from shared.http import fetch_with_retry
from shared.validator import title_matches_expected

# TODO: Replace with the search/listing URL for your target product on this site
URL = "https://www.example.com/search?q=your+product"


def scrape(session, config):
    """
    Scrape one site and return a list of matching (name, price, source, url) tuples.
    Called automatically by the Data Extraction Agent on each check cycle.

    Args:
        session: requests.Session (proxy-configured if Tor is enabled)
        config:  dict loaded from plugin_config.yaml — use it for all thresholds
    """
    budget        = config.get("budget", float("inf"))
    keyword       = config.get("filter_keyword", "")
    secondary     = config.get("filter_keyword_2", "")
    brand_keywords = config.get("brand_keywords", [])
    results       = []

    response = fetch_with_retry(session, URL)
    if response is None:
        return results  # fetch failed after retries — skip this site silently

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # TODO: Replace ".product-item" with the CSS selector for product cards on your site
        for card in soup.select(".product-item"):

            # TODO: Replace selectors with the correct ones for name, price, and link on your site
            name_tag  = card.select_one(".product-title")
            price_tag = card.select_one(".product-price")
            link_tag  = card.select_one("a")

            if not name_tag or not price_tag:
                continue

            name = name_tag.text.strip()
            url  = link_tag["href"] if link_tag else URL

            # Keyword filter — skip listings that don't match the target product
            if keyword and keyword not in name:
                continue
            if secondary and secondary not in name:
                continue

            # Brand filter — skip listings from untrusted brands
            if brand_keywords and not title_matches_expected(name, brand_keywords):
                print(f"[mysite] Rejected listing — no trusted brand match: {name}")
                continue

            # TODO: Adjust price parsing for this site's currency format
            try:
                price = int(float(
                    price_tag.text
                    .replace("₹", "").replace("$", "")
                    .replace(",", "").strip()
                ))
            except ValueError:
                continue

            if price <= budget:
                # TODO: Replace "MySite" with your site's display name
                results.append((name, price, "MySite", url))

    except Exception as e:
        # TODO: Replace "mysite" with your site's name for log clarity
        print(f"[mysite] Error: {e}")

    return results
