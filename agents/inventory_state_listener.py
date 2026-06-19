"""
inventory_state_listener.py — Stock Watcher Agent
==================================================
Generic. Monitors a watchlist of URLs for stock status changes.
Fires alert the moment anything transitions out-of-stock → in-stock.
All domain values come from config.
"""

import json
import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("inventory_state_listener")


# ------------------------------------------------------------------ #
#  Watchlist persistence                                              #
# ------------------------------------------------------------------ #

def load_watchlist(path: str) -> list:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_watchlist(path: str, watchlist: list) -> None:
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(watchlist, f, indent=2)


def add_to_watchlist(path: str, name: str, url: str, price: float) -> None:
    watchlist = load_watchlist(path)
    if not any(item["url"] == url for item in watchlist):
        watchlist.append({
            "name": name,
            "url": url,
            "price": price,
            "added": datetime.now().isoformat(),
        })
        save_watchlist(path, watchlist)
        logger.info(f"Added to watchlist: {name}")


# ------------------------------------------------------------------ #
#  Stock detection — generic heuristic, overridable via config        #
# ------------------------------------------------------------------ #

DEFAULT_OOS_MARKERS = ["out of stock", "sold out", "unavailable", "notify me"]


def fetch_page(url: str, session: requests.Session) -> str:
    try:
        response = session.get(url, timeout=20)
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""


def is_in_stock(html: str, oos_markers: list) -> bool:
    if not html:
        return False
    lowered = html.lower()
    return not any(marker in lowered for marker in oos_markers)


# ------------------------------------------------------------------ #
#  Core watch cycle                                                   #
# ------------------------------------------------------------------ #

def run_watch_cycle(config: dict, session: requests.Session) -> None:
    watchlist_path = config.get("watchlist_path", "~/agent-data/watchlist.json")
    oos_markers = config.get("oos_markers", DEFAULT_OOS_MARKERS)

    watchlist = load_watchlist(watchlist_path)
    if not watchlist:
        logger.info("Watchlist empty. Nothing to check.")
        return

    still_out = []
    for item in watchlist:
        html = fetch_page(item["url"], session)
        in_stock = is_in_stock(html, oos_markers)
        logger.info(f"{item['name']}: in_stock={in_stock}")

        if in_stock:
            msg = (
                f"RESTOCKED: {item['name']} at ₹{item['price']:,} "
                f"is back in stock!\nLink: {item['url']}"
            )
            logger.warning(msg)
            send_notification("Restock Alert!", msg)
            send_sms(msg)
        else:
            still_out.append(item)

    save_watchlist(watchlist_path, still_out)


def main(config: dict) -> None:
    interval = config.get("watchlist_interval_seconds", 900)
    proxy_url = config.get("network", {}).get("tor_proxy", {}).get("http")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    if proxy_url:
        session.proxies = {"http": proxy_url, "https": proxy_url}

    logger.info("Inventory State Listener started. Interval: %ss.", interval)
    while True:
        run_watch_cycle(config, session)
        time.sleep(interval)


if __name__ == "__main__":
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../user_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    main(config)
