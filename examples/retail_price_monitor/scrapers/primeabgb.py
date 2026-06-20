from bs4 import BeautifulSoup
from shared.validator import title_matches_expected

URL = "https://www.primeabgb.com/buy-online-price-india/geforce-rtx-5060-ti-graphic-card/"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    brand_keywords = config.get("brand_keywords", [])
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".product-inner"):
            name_tag = p.select_one(".woocommerce-loop-product__title")
            price_tag = p.select_one(".price .amount")
            stock_tag = p.select_one(".stock")
            link_tag = p.select_one("a.woocommerce-loop-product__link")
            out = stock_tag and "out-of-stock" in stock_tag.get("class", [])
            url = link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and not out:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[primeabgb] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "PrimeAbgb", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[primeabgb] Error: {e}")
    return results
