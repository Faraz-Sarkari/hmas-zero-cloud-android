from bs4 import BeautifulSoup

URL = "https://mdcomputers.in/index.php?route=product/search&search=rtx+5060+ti+16gb"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".product-layout"):
            name_tag = p.select_one(".name a")
            price_tag = p.select_one(".price-new") or p.select_one(".price-normal")
            url = name_tag["href"] if name_tag and name_tag.get("href") else URL
            if name_tag and price_tag and keyword in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "MDComputers", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[mdcomputers] Error: {e}")
    return results
