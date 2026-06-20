from bs4 import BeautifulSoup
from shared.validator import title_matches_expected

URL = "https://www.smartprix.com/goods/?q=rtx+5060+ti+16gb"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    brand_keywords = config.get("brand_keywords", [])
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".sm-product"):
            name_tag = p.select_one(".name")
            price_tag = p.select_one(".price")
            link_tag = p.select_one("a")
            url = link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[smartprix] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Smartprix", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[smartprix] Error: {e}")
    return results
