"""
Stock Watcher Agent: Heterogeneous Multi-Agent System (HMAS)
================================================================
Responsibility: Tracks a watchlist of specific product pages that
were previously found "out of stock" by the primary hunter agent.
Re-checks them on a tighter interval than the main 4x-daily cron,
and fires an immediate alert the moment any watched product
transitions from out-of-stock to in-stock.

This agent embodies the "targeted re-acquisition" layer — turning a
missed opportunity into a recoverable one.
"""
import json
import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("stock_watcher")

WATCHLIST_PATH = os.path.expanduser("~/multi-agent-system/shared/watchlist.json")
CHECK_INTERVAL_SECONDS = 900  # 15 minutes — tighter than main agent's 4x/day

TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}


def load_watchlist() -> list:
    """Loads the list of out-of-stock products being tracked for restock."""
    if not os.path.exists(WATCHLIST_PATH):
        return []
    with open(WATCHLIST_PATH, 'r') as f:
        return json.load(f)


def save_watchlist(watchlist: list) -> None:
    os.makedirs(os.path.dirname(WATCHLIST_PATH), exist_ok=True)
    with open(WATCHLIST_PATH, 'w') as f:
        json.dump(watchlist, f, indent=2)


def add_to_watchlist(name: str, url: str, price: int) -> None:
    """Called externally (or manually) to add a newly out-of-stock product."""
    watchlist = load_watchlist()
    entry = {"name": name, "url": url, "price": price, "added": datetime.now().isoformat()}
    if not any(item["url"] == url for item in watchlist):
        watchlist.append(entry)
        save_watchlist(watchlist)
        logger.info(f"Added to stock watchlist: {name}")


def fetch_page(url: str) -> str:
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, proxies=TOR_PROXY, timeout=20)
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""


def is_in_stock(html: str) -> bool:
    """
    Simple heuristic: if the page contains common out-of-stock markers,
    treat as unavailable. Otherwise assume available.
    """
    if not html:
        return False
    lowered = html.lower()
    out_of_stock_markers = ["out of stock", "sold out", "unavailable", "notify me"]
    return not any(marker in lowered for marker in out_of_stock_markers)


def run_watch_cycle() -> None:
    watchlist = load_watchlist()
    if not watchlist:
        logger.info("Watchlist empty. Nothing to check.")
        return

    still_out_of_stock = []
    for item in watchlist:
        html = fetch_page(item["url"])
        in_stock = is_in_stock(html)
        logger.info(f"{item['name']}: in_stock={in_stock}")

        if in_stock:
            msg = f"RESTOCKED: {item['name']} at ₹{item['price']:,} is back in stock!\nLink: {item['url']}"
            logger.warning(msg)
            send_notification("Stock Watcher: Restock Alert!", msg)
            send_sms(msg)
        else:
            still_out_of_stock.append(item)

    save_watchlist(still_out_of_stock)


def main() -> None:
    logger.info("Stock Watcher started. Checking watchlist every %s seconds.", CHECK_INTERVAL_SECONDS)
    while True:
        run_watch_cycle()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
