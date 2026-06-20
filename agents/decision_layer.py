"""
decision_layer.py — Buy/Wait Advisor Agent
===========================================
Generic decision/reasoning layer. Knows nothing about GPUs, prices,
or any specific domain.

Reads price history from a log file, applies configurable thresholds,
and produces a BUY or WAIT recommendation once per day.

All domain-specific values (target price, log path, advisory hour)
come from plugin_config passed in at runtime.
"""

import json
import os
import sys
import time
from datetime import datetime

from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("decision_layer")

CHECK_INTERVAL_SECONDS = 1800


def load_price_history(log_path: str) -> list:
    log_path = os.path.expanduser(log_path)
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        return json.load(f)


def compute_recommendation(data: list, target: float, item_label: str = "item") -> str:
    """
    Applies decision rules over recent price history.
    Returns a human-readable BUY or WAIT recommendation.
    No domain knowledge — works for any numeric price series.
    """
    if len(data) < 5:
        return "WAIT — Not enough price history yet to form a confident recommendation."

    recent = data[-50:] if len(data) >= 50 else data
    prices = [d["price"] for d in recent]
    latest = prices[-1]
    average = sum(prices) / len(prices)
    minimum = min(prices)

    if latest <= target:
        return (
            f"BUY NOW — Current price ₹{latest:,} has hit your "
            f"₹{target:,} target for {item_label}."
        )

    if latest <= average * 0.97:
        return (
            f"CONSIDER BUYING — Current price ₹{latest:,} is meaningfully "
            f"below the recent average of ₹{int(average):,}. Possible local dip."
        )

    if latest == minimum:
        return (
            f"CONSIDER BUYING — ₹{latest:,} is the lowest price seen recently "
            f"for {item_label}. Diminishing returns to waiting further."
        )

    return (
        f"WAIT — Current price ₹{latest:,} is near the recent average of "
        f"₹{int(average):,}. No strong signal to act yet."
    )


def run_advisory_cycle(config: dict) -> None:
    log_path = config.get("price_log", "~/agent-data/prices.json")
    target = config.get("target", 0)
    item_label = config.get("item_label", "item")

    data = load_price_history(log_path)
    recommendation = compute_recommendation(data, target, item_label)

    logger.info(f"Daily advisory: {recommendation}")
    send_notification("Buy/Wait Advisor", recommendation)
    send_sms(recommendation)


def main(config: dict) -> None:
    advisory_hour = config.get("advisory_hour", 10)
    item_label = config.get("item_label", "item")

    logger.info(
        "Decision Layer started. Daily recommendation at %s:00 for %s.",
        advisory_hour,
        item_label,
    )

    last_sent_date = None
    while True:
        now = datetime.now()
        if now.hour == advisory_hour and now.date() != last_sent_date:
            run_advisory_cycle(config)
            last_sent_date = now.date()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    import yaml

    config_path = os.path.join(
        os.path.dirname(__file__),
        "../examples/retail_price_monitor/plugin_config.yaml",
    )
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    main(config)
