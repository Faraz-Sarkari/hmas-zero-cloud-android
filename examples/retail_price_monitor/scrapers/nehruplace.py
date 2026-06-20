from bs4 import BeautifulSoup
from shared.validator import title_matches_expected
from shared.http import fetch_with_retry

URL = "https://www.nehruplacemarket.com/price-list/graphicscard-price-list.html"

def scrape(session, config):
    URL = config.get("scraper_urls", {}).get("nehruplace", globals()["URL"])
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    secondary = config.get("filter_keyword_2", "5060 Ti")
    brand_keywords = config.get("brand_keywords", [])
    results = []
    try:
        response = fetch_with_retry(session, URL)
        if response is None:
            return results
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("tr"):
            cells = row.select("td")
            if len(cells) >= 2:
                name = cells[0].text.strip()
                price_text = cells[1].text.strip()
                if secondary in name and keyword in name:
                    if brand_keywords and not title_matches_expected(name, brand_keywords):
                        print(f"[nehruplace] Rejected listing — no trusted brand match: {name}")
                        continue
                    try:
                        price = int(float(price_text.replace("₹", "").replace(",", "").strip()))
                        if price <= budget:
                            results.append((name, price, "NehruPlace", URL))
                    except ValueError:
                        pass
    except Exception as e:
        print(f"[nehruplace] Error: {e}")
    return results
