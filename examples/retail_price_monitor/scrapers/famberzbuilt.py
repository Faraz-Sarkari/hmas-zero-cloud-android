from bs4 import BeautifulSoup
from shared.validator import title_matches_expected
from shared.http import fetch_with_retry

URL = "https://famberzbuilt.in/category/graphics-cards"

def scrape(session, config):
    URL = config.get("scraper_urls", {}).get("famberzbuilt", globals()["URL"])
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
        for p in soup.select(".product-item"):
            name_tag = p.select_one(".product-title")
            price_tag = p.select_one(".product-price")
            link_tag = p.select_one("a")
            url = link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[famberzbuilt] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Famberzbuilt", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[famberzbuilt] Error: {e}")
    return results
