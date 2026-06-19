import requests
from bs4 import BeautifulSoup
import schedule
import time
import subprocess
import json
import os
from datetime import datetime

BUDGET = 60000
TARGET = 55000
CONTACT = os.environ.get("ALERT_PHONE_NUMBER", "")
PRICE_LOG = os.path.expanduser("~/rtx-agent/data/prices.json")

TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def notify(title, message):
    subprocess.Popen(['termux-notification', '--title', title, '--content', message, '--priority', 'high', '--vibrate', '500,200,500'])

def send_sms(message):
    subprocess.Popen(['termux-sms-send', '-n', CONTACT, message])

def emergency_alert(msg):
    for i in range(10):
        subprocess.Popen(['termux-notification', '--id', '999', '--title', 'RTX 55K ALERT!', '--content', msg, '--priority', 'high', '--vibrate', '1000,500,1000,500,1000', '--ongoing'])
        subprocess.Popen(['termux-sms-send', '-n', CONTACT, 'RTX UNDER 55K! CHECK NOW!\n' + msg])
        time.sleep(120)

def get(url):
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=TOR_PROXY, timeout=20)

def analyze_deal(price):
    if price <= TARGET:
        return "BUY NOW UNDER 55K!"
    elif price <= 57000:
        return "VERY CLOSE to 55K!"
    else:
        return str(price - TARGET) + " away from 55K target"

def log_price(price, site):
    os.makedirs(os.path.dirname(PRICE_LOG), exist_ok=True)
    data = []
    if os.path.exists(PRICE_LOG):
        with open(PRICE_LOG, 'r') as f:
            data = json.load(f)
    data.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "price": price, "site": site})
    with open(PRICE_LOG, 'w') as f:
        json.dump(data, f)

def predict_target_date():
    if not os.path.exists(PRICE_LOG):
        return "Need more data"
    with open(PRICE_LOG, 'r') as f:
        data = json.load(f)
    if len(data) < 2:
        return "Need more data points"
    prices = [d['price'] for d in data]
    avg_drop = (prices[0] - prices[-1]) / len(prices)
    if avg_drop <= 0:
        return "Price not dropping yet"
    days_needed = int((prices[-1] - TARGET) / avg_drop)
    return "Estimated days to 55K: " + str(days_needed)

def check_primeabgb():
    try:
        soup = BeautifulSoup(get("https://www.primeabgb.com/buy-online-price-india/geforce-rtx-5060-ti-graphic-card/").text, 'html.parser')
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
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'PrimeAbgb')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'PrimeAbgb', url))
                except: pass
        return results
    except Exception as e:
        print("PrimeAbgb error: " + str(e))
        return []

def check_mdcomputers():
    try:
        soup = BeautifulSoup(get("https://mdcomputers.in/index.php?route=product/search&search=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.product-layout'):
            name_tag = p.select_one('.name a')
            price_tag = p.select_one('.price-new')
            if not price_tag:
                price_tag = p.select_one('.price-normal')
            url = name_tag['href'] if name_tag and name_tag.get('href') else 'https://mdcomputers.in'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'MDComputers')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'MDComputers', url))
                except: pass
        return results
    except Exception as e:
        print("MDComputers error: " + str(e))
        return []

def check_vedant():
    try:
        soup = BeautifulSoup(get("https://www.vedantcomputers.com/index.php?route=product/search&search=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.product-layout'):
            name_tag = p.select_one('.name a')
            price_tag = p.select_one('.price-normal')
            url = name_tag['href'] if name_tag and name_tag.get('href') else 'https://www.vedantcomputers.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'Vedant')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'Vedant', url))
                except: pass
        return results
    except Exception as e:
        print("Vedant error: " + str(e))
        return []

def check_elitehubs():
    try:
        soup = BeautifulSoup(get("https://elitehubs.com/collections/nvidia-geforce-rtx-5060-ti-graphics-card").text, 'html.parser')
        results = []
        for p in soup.select('.product-item'):
            name_tag = p.select_one('.product-item__title')
            price_tag = p.select_one('.price__current')
            sold_out = p.select_one('.badge--sold-out')
            link_tag = p.select_one('a.product-item__image-link')
            url = 'https://elitehubs.com' + link_tag['href'] if link_tag else 'https://elitehubs.com'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text and not sold_out:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'EliteHubs')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'EliteHubs', url))
                except: pass
        return results
    except Exception as e:
        print("EliteHubs error: " + str(e))
        return []

def check_famberzbuilt():
    try:
        soup = BeautifulSoup(get("https://famberzbuilt.in/category/graphics-cards").text, 'html.parser')
        results = []
        for p in soup.select('.product-item'):
            name_tag = p.select_one('.product-title')
            price_tag = p.select_one('.product-price')
            link_tag = p.select_one('a')
            url = link_tag['href'] if link_tag else 'https://famberzbuilt.in'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'Famberzbuilt')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'Famberzbuilt', url))
                except: pass
        return results
    except Exception as e:
        print("Famberzbuilt error: " + str(e))
        return []

def check_smartprix():
    try:
        soup = BeautifulSoup(get("https://www.smartprix.com/goods/?q=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.sm-product'):
            name_tag = p.select_one('.name')
            price_tag = p.select_one('.price')
            link_tag = p.select_one('a')
            url = link_tag['href'] if link_tag else 'https://www.smartprix.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'Smartprix')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'Smartprix', url))
                except: pass
        return results
    except Exception as e:
        print("Smartprix error: " + str(e))
        return []

def check_amazon():
    try:
        soup = BeautifulSoup(get("https://www.amazon.in/s?k=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('.s-result-item'):
            name_tag = p.select_one('h2 span')
            price_tag = p.select_one('.a-price-whole')
            unavailable = p.select_one('.s-item-unavailable')
            link_tag = p.select_one('a.a-link-normal')
            url = 'https://www.amazon.in' + link_tag['href'] if link_tag else 'https://www.amazon.in'
            if name_tag and price_tag and '16GB' in name_tag.text and '5060 Ti' in name_tag.text and not unavailable:
                try:
                    price = int(float(price_tag.text.replace(',','').strip()))
                    log_price(price, 'Amazon')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'Amazon', url))
                except: pass
        return results
    except Exception as e:
        print("Amazon error: " + str(e))
        return []

def check_flipkart():
    try:
        soup = BeautifulSoup(get("https://www.flipkart.com/search?q=rtx+5060+ti+16gb").text, 'html.parser')
        results = []
        for p in soup.select('._1AtVbE'):
            name_tag = p.select_one('._4rR01T')
            price_tag = p.select_one('._30jeq3')
            link_tag = p.select_one('a')
            url = 'https://www.flipkart.com' + link_tag['href'] if link_tag else 'https://www.flipkart.com'
            if name_tag and price_tag and '16GB' in name_tag.text:
                try:
                    price = int(float(price_tag.text.replace('₹','').replace(',','').strip()))
                    log_price(price, 'Flipkart')
                    if price <= BUDGET:
                        results.append((name_tag.text.strip(), price, 'Flipkart', url))
                except: pass
        return results
    except Exception as e:
        print("Flipkart error: " + str(e))
        return []

def check_nehruplace():
    try:
        soup = BeautifulSoup(get("https://www.nehruplacemarket.com/price-list/graphicscard-price-list.html").text, 'html.parser')
        results = []
        for row in soup.select('tr'):
            cells = row.select('td')
            if len(cells) >= 2:
                name = cells[0].text.strip()
                price_text = cells[1].text.strip()
                if '5060 Ti' in name and '16GB' in name:
                    try:
                        price = int(float(price_text.replace('₹','').replace(',','').strip()))
                        log_price(price, 'NehruPlace')
                        if price <= BUDGET:
                            results.append((name, price, 'NehruPlace', 'https://www.nehruplacemarket.com/price-list/graphicscard-price-list.html'))
                    except: pass
        return results
    except Exception as e:
        print("NehruPlace error: " + str(e))
        return []

def run_check():
    now = datetime.now().strftime("%d %b %I:%M %p")
    print("Checking at " + now)
    results = (check_primeabgb() + check_mdcomputers() + check_vedant() +
               check_elitehubs() + check_famberzbuilt() + check_smartprix() +
               check_amazon() + check_flipkart() + check_nehruplace())
    prediction = predict_target_date()
    if results:
        msg = "RTX DEAL FOUND! [" + now + "]\n\n"
        for name, price, site, url in results:
            verdict = analyze_deal(price)
            msg += name + "\nPrice: " + str(price) + "\nSite: " + site + "\n" + verdict + "\nLink: " + url + "\n\n"
        msg += prediction
        if any(p <= TARGET for n, p, s, u in results):
            emergency_alert(msg)
        else:
            notify("RTX DEAL ALERT!", msg)
            send_sms(msg)
        print(msg)
    else:
        msg = "RTX Check [" + now + "]\nNo in-stock deal under 60K yet\nStill watching...\n" + prediction
        notify("RTX Check Done", msg)
        send_sms(msg)
        print(msg)

schedule.every().day.at("08:00").do(run_check)
schedule.every().day.at("13:00").do(run_check)
schedule.every().day.at("18:00").do(run_check)
schedule.every().day.at("21:00").do(run_check)

run_check()

while True:
    schedule.run_pending()
    time.sleep(30)
