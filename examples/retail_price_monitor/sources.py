"""
Reference source-checker plugin: RTX 5060 Ti 16GB price monitor across
9 Indian retail sites.

This is the ORIGINAL domain logic from the single-purpose version of this
project, kept here as a working example of how to write a `sources` plugin
for the generic agents/data_extraction_agent.py.

A plugin must expose get_checkers() -> list[Callable[[], list[tuple]]].
Each checker takes no arguments and returns a list of
(name, price, site, url) tuples for every matching item it finds —
including ones above budget. The core agent handles budget filtering,
logging, and alerting.

To build your own plugin for a different product/market: copy this file,
swap out the URLs/selectors, and point `sources_module` in
config/user_config.yaml at your new module's import path.
"""
import requests
from bs4 import BeautifulSoup

from config import settings


def fetch(url):
    return requests.get(
        url,
        headers={'User-Agent': 'Mozilla/5.0'},
        proxies=settings.TOR_PROXY,
        timeout=20,
    )


def _parse_price(text):
    return int(float(text.replace('₹', '').replace(',', '').strip()))


def check_primeabgb():
    try:
        soup = BeautifulSoup(
            fetch("https://www.primeabgb.com/buy-online-price-india/geforce-rtx-5060-ti-graphic-card/").text,
            'html.parser',
        )
        results = []
        for p in soup.select('.product-inner'):
            name_tag = p.select_one('.woocommerce-loop-product__title')
            price_tag = p.select_one('.price .amount')
            stock_tag = p.select_one('.stock')
            out = stock_tag and 'out-of-stock' in stock_tag.get('class', [])
            link_tag = p.select_one('a.woocommerce-loop-product__link')
            url = link_tag['href'] if link_tag else 'https://www.primeabgb.com'
            if name_tag and price_tag and '16GB' in name_tag.text and not out:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'PrimeAbgb', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("PrimeAbgb error: " + str(e))
        return []


def check_mdcomputers():
    try:
        soup = BeautifulSoup(
            fetch("https://mdcomputers.in/index.php?route=product/search&search=rtx+5060+ti+16gb").text,
            'html.parser',
        )
        results = []
        for p in soup.select('.product-layout'):
            name_tag = p.select_one('.name a')
            price_tag = p.select_one('.price-new') or p.select_one('.price-normal')
            url = name_tag['href'] if name_tag and name_tag.get('href') else 'https://mdcomputers.in'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'MDComputers', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("MDComputers error: " + str(e))
        return []


def check_vedant():
    try:
        soup = BeautifulSoup(
            fetch("https://www.vedantcomputers.com/index.php?route=product/search&search=rtx+5060+ti+16gb").text,
            'html.parser',
        )
        results = []
        for p in soup.select('.product-layout'):
            name_tag = p.select_one('.name a')
            price_tag = p.select_one('.price-normal')
            url = name_tag['href'] if name_tag and name_tag.get('href') else 'https://www.vedantcomputers.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'Vedant', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("Vedant error: " + str(e))
        return []


def check_elitehubs():
    try:
        soup = BeautifulSoup(
            fetch("https://elitehubs.com/collections/nvidia-geforce-rtx-5060-ti-graphics-card").text,
            'html.parser',
        )
        results = []
        for p in soup.select('.product-item'):
            name_tag = p.select_one('.product-item__title')
            price_tag = p.select_one('.price__current')
            sold_out = p.select_one('.badge--sold-out')
            link_tag = p.select_one('a.product-item__image-link')
            url = 'https://elitehubs.com' + link_tag['href'] if link_tag else 'https://elitehubs.com'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text and not sold_out:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'EliteHubs', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("EliteHubs error: " + str(e))
        return []


def check_famberzbuilt():
    try:
        soup = BeautifulSoup(fetch("https://famberzbuilt.in/category/graphics-cards").text, 'html.parser')
        results = []
        for p in soup.select('.product-item'):
            name_tag = p.select_one('.product-title')
            price_tag = p.select_one('.product-price')
            link_tag = p.select_one('a')
            url = link_tag['href'] if link_tag else 'https://famberzbuilt.in'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'Famberzbuilt', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("Famberzbuilt error: " + str(e))
        return []


def check_smartprix():
    try:
        soup = BeautifulSoup(fetch("https://www.smartprix.com/goods/?q=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.sm-product'):
            name_tag = p.select_one('.name')
            price_tag = p.select_one('.price')
            link_tag = p.select_one('a')
            url = link_tag['href'] if link_tag else 'https://www.smartprix.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'Smartprix', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("Smartprix error: " + str(e))
        return []


def check_amazon():
    try:
        soup = BeautifulSoup(fetch("https://www.amazon.in/s?k=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.s-result-item'):
            name_tag = p.select_one('h2 span')
            price_tag = p.select_one('.a-price-whole')
            unavailable = p.select_one('.s-item-unavailable')
            link_tag = p.select_one('a.a-link-normal')
            url = 'https://www.amazon.in' + link_tag['href'] if link_tag else 'https://www.amazon.in'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text and not unavailable:
                try:
                    price = int(float(price_tag.text.replace(',', '').strip()))
                    results.append((name_tag.text.strip(), price, 'Amazon', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("Amazon error: " + str(e))
        return []


def check_flipkart():
    try:
        soup = BeautifulSoup(fetch("https://www.flipkart.com/search?q=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('._1AtVbE'):
            name_tag = p.select_one('._4rR01T')
            price_tag = p.select_one('._30jeq3')
            link_tag = p.select_one('a')
            url = 'https://www.flipkart.com' + link_tag['href'] if link_tag else 'https://www.flipkart.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = _parse_price(price_tag.text)
                    results.append((name_tag.text.strip(), price, 'Flipkart', url))
                except Exception:
                    pass
        return results
    except Exception as e:
        print("Flipkart error: " + str(e))
        return []


def check_nehruplace():
    try:
        url = "https://www.nehruplacemarket.com/price-list/graphicscard-price-list.html"
        soup = BeautifulSoup(fetch(url).text, 'html.parser')
        results = []
        for row in soup.select('tr'):
            cells = row.select('td')
            if len(cells) >= 2:
                name = cells[0].text.strip()
                price_text = cells[1].text.strip()
                if '5060 Ti' in name and '16GB' in name:
                    try:
                        price = _parse_price(price_text)
                        results.append((name, price, 'NehruPlace', url))
                    except Exception:
                        pass
        return results
    except Exception as e:
        print("NehruPlace error: " + str(e))
        return []


def get_checkers():
    """Returns the list of checker functions this plugin provides."""
    return [
        check_primeabgb,
        check_mdcomputers,
        check_vedant,
        check_elitehubs,
        check_famberzbuilt,
        check_smartprix,
        check_amazon,
        check_flipkart,
        check_nehruplace,
    ]
