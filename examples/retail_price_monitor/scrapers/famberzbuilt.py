from bs4 import BeautifulSoup

URL = "https://famberzbuilt.in/category/graphics-cards"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    secondary = config.get("filter_keyword_2", "5060 Ti")
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".product-item"):
            name_tag = p.select_one(".product-title")
            price_tag = p.select_one(".product-price")
            link_tag = p.select_one("a")
            url = link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Famberzbuilt", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[famberzbuilt] Error: {e}")
    return results
