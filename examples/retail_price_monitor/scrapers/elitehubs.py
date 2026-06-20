from bs4 import BeautifulSoup
from shared.validator import title_matches_expected
from shared.http import fetch_with_retry

URL = "https://elitehubs.com/collections/nvidia-geforce-rtx-5060-ti-graphics-card"

def scrape(session, config):
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
            name_tag = p.select_one(".product-item__title")
            price_tag = p.select_one(".price__current")
            sold_out = p.select_one(".badge--sold-out")
            link_tag = p.select_one("a.product-item__image-link")
            url = "https://elitehubs.com" + link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text and not sold_out:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[elitehubs] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "EliteHubs", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[elitehubs] Error: {e}")
    return results
