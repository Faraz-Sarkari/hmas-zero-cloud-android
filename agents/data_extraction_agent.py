"""
Generic Data Extraction Agent — HMAS Framework

This agent contains NO domain-specific logic. It periodically runs a set of
"source checkers" supplied by a pluggable module (configured via
`sources_module` in config/user_config.yaml), logs every price point it
sees, and fires notifications/SMS/emergency-alerts when a result is at or
below your configured budget/target.

Each checker is a zero-argument callable that returns a list of
(name, price, site, url) tuples for every matching item it found —
regardless of price. Filtering against budget/target happens here, once,
so every checker can stay dumb and simple.

See examples/retail_price_monitor/sources.py for a reference plugin.
"""
import importlib
import subprocess
import time
from datetime import datetime

import schedule

from config import settings
from shared.price_history import load_price_history, log_price

# ---------------------------------------------------------------------------
# Load the pluggable source-checker module named in user_config.yaml
# ---------------------------------------------------------------------------
_sources_module = importlib.import_module(settings.SOURCES_MODULE)
CHECKERS = _sources_module.get_checkers()


def notify(title, message):
    subprocess.Popen([
        'termux-notification', '--title', title, '--content', message,
        '--priority', 'high', '--vibrate', '500,200,500'
    ])


def send_sms(message):
    if not settings.CONTACT_NUMBER:
        return
    subprocess.Popen(['termux-sms-send', '-n', settings.CONTACT_NUMBER, message])


def emergency_alert(msg):
    for _ in range(10):
        subprocess.Popen([
            'termux-notification', '--id', '999',
            '--title', f'{settings.PRODUCT_NAME} TARGET ALERT!',
            '--content', msg, '--priority', 'high',
            '--vibrate', '1000,500,1000,500,1000', '--ongoing'
        ])
        if settings.CONTACT_NUMBER:
            subprocess.Popen([
                'termux-sms-send', '-n', settings.CONTACT_NUMBER,
                f'{settings.PRODUCT_NAME} UNDER TARGET! CHECK NOW!\n' + msg
            ])
        time.sleep(120)


def analyze_deal(price):
    if price <= settings.TARGET_PRICE:
        return f"BUY NOW — at or under target ({settings.TARGET_PRICE})!"
    elif price <= settings.WARNING_THRESHOLD:
        return "VERY CLOSE to target!"
    else:
        return f"{price - settings.TARGET_PRICE} away from target"


def predict_target_date():
    data = load_price_history()
    if len(data) < 2:
        return "Need more data points"
    prices = [d['price'] for d in data]
    avg_drop = (prices[0] - prices[-1]) / len(prices)
    if avg_drop <= 0:
        return "Price not dropping yet"
    days_needed = int((prices[-1] - settings.TARGET_PRICE) / avg_drop)
    return f"Estimated days to target: {days_needed}"


def run_check():
    now = datetime.now().strftime("%d %b %I:%M %p")
    print(f"Checking at {now}")

    all_items = []
    for checker in CHECKERS:
        try:
            all_items.extend(checker())
        except Exception as e:
            print(f"{checker.__name__} error: {e}")

    for name, price, site, url in all_items:
        log_price(price, site)

    deals = [item for item in all_items if item[1] <= settings.BUDGET_CEILING]
    prediction = predict_target_date()

    if deals:
        msg = f"{settings.PRODUCT_NAME} DEAL FOUND! [{now}]\n\n"
        for name, price, site, url in deals:
            msg += f"{name}\nPrice: {price}\nSite: {site}\n{analyze_deal(price)}\nLink: {url}\n\n"
        msg += prediction

        if any(price <= settings.TARGET_PRICE for _, price, _, _ in deals):
            emergency_alert(msg)
        else:
            notify(f"{settings.PRODUCT_NAME} DEAL ALERT!", msg)
            send_sms(msg)
        print(msg)
    else:
        msg = (
            f"{settings.PRODUCT_NAME} Check [{now}]\n"
            f"No in-stock deal under {settings.BUDGET_CEILING} yet\n"
            f"Still watching...\n{prediction}"
        )
        notify(f"{settings.PRODUCT_NAME} Check Done", msg)
        send_sms(msg)
        print(msg)


def main():
    for check_time in settings.CHECK_TIMES:
        schedule.every().day.at(check_time).do(run_check)

    run_check()
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
