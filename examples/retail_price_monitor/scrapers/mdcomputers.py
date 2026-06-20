from bs4 import BeautifulSoup
from shared.validator import title_matches_expected
from shared.http import fetch_with_retry

URL = "https://mdcomputers.in/index.php?route=product/search&search=rtx+5060+ti+16gb"

def scrape(session, config):
    URL = config.get("scraper_urls", {}).get("mdcomputers", globals()["URL"])
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    brand_keywords = config.get("brand_keywords", [])
    results = []
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    })
    try:
        response = fetch_with_retry(session, URL)
        if response is None:
            return results
        soup = BeautifulSoup(response.text, "html.parser")
        for p in soup.select(".product-layout"):
            name_tag = p.select_one(".name a")
            price_tag = p.select_one(".price-new") or p.select_one(".price-normal")
            url = name_tag["href"] if name_tag and name_tag.get("href") else URL
            if name_tag and price_tag and keyword in name_tag.text:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[mdcomputers] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace("₹", "").replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "MDComputers", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[mdcomputers] Error: {e}")
    return results
