from bs4 import BeautifulSoup
from shared.validator import title_matches_expected
from shared.http import fetch_with_retry

URL = "https://www.amazon.in/s?k=rtx+5060+ti+16gb"

def scrape(session, config):
    URL = config.get("scraper_urls", {}).get("amazon", globals()["URL"])
    budget = config.get("budget", float("inf"))
    keyword = config.get("filter_keyword", "16GB")
    secondary = config.get("filter_keyword_2", "5060 Ti")
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
        for p in soup.select(".s-result-item"):
            name_tag = p.select_one("h2 span")
            price_tag = p.select_one(".a-price-whole")
            unavailable = p.select_one(".s-item-unavailable")
            link_tag = p.select_one("a.a-link-normal")
            url = "https://www.amazon.in" + link_tag["href"] if link_tag else URL
            if name_tag and price_tag and keyword in name_tag.text and secondary in name_tag.text and not unavailable:
                if brand_keywords and not title_matches_expected(name_tag.text, brand_keywords):
                    print(f"[amazon] Rejected listing — no trusted brand match: {name_tag.text.strip()}")
                    continue
                try:
                    price = int(float(price_tag.text.replace(",", "").strip()))
                    if price <= budget:
                        results.append((name_tag.text.strip(), price, "Amazon", url))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[amazon] Error: {e}")
    return results
