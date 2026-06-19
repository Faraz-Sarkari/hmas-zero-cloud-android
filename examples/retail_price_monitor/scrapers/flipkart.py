from bs4 import BeautifulSoup

URL = "https://www.flipkart.com/search?q=rtx+5060+ti+16gb"

def scrape(session, config):
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    results = []
    try:
        soup = BeautifulSoup(session.get(URL, timeout=20).text, "html.parser")
        for p in soup.select("._1AtVbE"):
            name_tag = p.select_one("._4rR01T")
            price_tag = p.select_one("._30jeq3")
            link_tag = p.select_one("a")
            url = "https://www.flipkart.com" + link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Flipkart", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[flipkart] Error: {e}")
    return results
