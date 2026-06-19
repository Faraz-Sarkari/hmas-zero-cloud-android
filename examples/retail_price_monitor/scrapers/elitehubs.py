from bs4 import BeautifulSoup

URL = "https://elitehubs.com/collections/nvidia-geforce-rtx-5060-ti-graphics-card"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    secondary = config.get("filter_keyword_2", "5060 Ti")
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".product-item"):
            name_tag = p.select_one(".product-item__title")
            price_tag = p.select_one(".price__current")
            sold_out = p.select_one(".badge--sold-out")
            link_tag = p.select_one("a.product-item__image-link")
            url = "https://elitehubs.com" + link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text and not sold_out:
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "EliteHubs", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[elitehubs] Error: {e}")
    return results
