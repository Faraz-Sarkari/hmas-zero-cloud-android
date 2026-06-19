from bs4 import BeautifulSoup

URL = "https://www.amazon.in/s?k=rtx+5060+ti+16gb"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    secondary = config.get("filter_keyword_2", "5060 Ti")
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select(".s-result-item"):
            name_tag = p.select_one("h2 span")
            price_tag = p.select_one(".a-price-whole")
            unavailable = p.select_one(".s-item-unavailable")
            link_tag = p.select_one("a.a-link-normal")
            url = "https://www.amazon.in" + link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text and not unavailable:
                try:
                    price = int(float(price_tag.text.replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Amazon", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[amazon] Error: {e}")
    return results
