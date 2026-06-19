"""
reacquisition_agent.py — Reacquisition Agent
=============================================
Generic. Monitors a list of deals that were previously seen
but missed (out of stock, over budget at the time, etc).
Re-checks them on a tight interval and alerts the moment
conditions are met again.
All domain values come from config.
"""

import json
import os
import time
from datetime import datetime

import requests

from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("reacquisition_agent")

MISSED_DEALS_PATH_DEFAULT = "~/agent-data/missed_deals.json"


def load_missed_deals(path: str) -> list:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_missed_deals(path: str, deals: list) -> None:
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(deals, f, indent=2)


def add_missed_deal(path: str, name: str, url: str, last_price: float) -> None:
    """Call this from data_extraction_agent when a deal is seen but missed."""
    deals = load_missed_deals(path)
    if not any(d["url"] == url for d in deals):
        deals.append({
            "name": name,
            "url": url,
            "last_price": last_price,
            "added": datetime.now().isoformat(),
        })
        save_missed_deals(path, deals)
        logger.info(f"Added to missed deals: {name}")


def fetch_page(url: str, session: requests.Session) -> str:
    try:
        return session.get(url, timeout=20).text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""


def is_available(html: str, oos_markers: list) -> bool:
    if not html:
        return False
    lowered = html.lower()
    return not any(marker in lowered for marker in oos_markers)


def run_reacquisition_cycle(config: dict, session: requests.Session) -> None:
    path = config.get("missed_deals_path", MISSED_DEALS_PATH_DEFAULT)
    oos_markers = config.get("oos_markers", ["out of stock", "sold out", "unavailable", "notify me"])
    budget = config.get("thresholds", {}).get("budget_ceiling", float("inf"))
    target = config.get("thresholds", {}).get("target_price", 0)
    item_label = config.get("product", {}).get("name", "item")

    deals = load_missed_deals(path)
    if not deals:
        logger.info("No missed deals to recheck.")
        return

    still_missed = []
    for deal in deals:
        html = fetch_page(deal["url"], session)
        available = is_available(html, oos_markers)
        logger.info(f"{deal['name']}: available={available}")

        if available:
            price = deal.get("last_price", 0)
            urgent = price <= target
            msg = (
                f"REACQUIRE: {deal['name']} is available again!\n"
                f"Last seen price: ₹{price:,}\n"
                f"Link: {deal['url']}"
            )
            logger.warning(msg)
            send_notification(f"{'🚨 ' if urgent else ''}Reacquisition Alert", msg)
            send_sms(msg)
        else:
            still_missed.append(deal)

    save_missed_deals(path, still_missed)


def main(config: dict) -> None:
    interval = config.get("reacquisition_interval_seconds", 900)
    proxy_cfg = config.get("network", {}).get("tor_proxy", {})
    use_tor = config.get("network", {}).get("use_tor", False)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    if use_tor:
        session.proxies = proxy_cfg

    logger.info("Reacquisition Agent started. Interval: %ss.", interval)
    while True:
        run_reacquisition_cycle(config, session)
        time.sleep(interval)


if __name__ == "__main__":
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../user_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    main(config)
