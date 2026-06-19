"""
Buy/Wait Advisor Agent: Heterogeneous Multi-Agent System (HMAS)
==================================================================
Responsibility: Acts as the decision/reasoning layer of the system.
Synthesizes the latest price data and trend direction (price rising,
falling, or flat) into a clear, actionable BUY or WAIT recommendation
for the user, delivered once per day.

This agent embodies the "rules engine / decision logic" layer.
"""
import json
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("buy_wait_advisor")

PRIMARY_PRICE_LOG = os.path.expanduser("~/rtx-agent/data/prices.json")
TARGET_PRICE = 55000
BUDGET_CEILING = 60000
ADVISORY_HOUR = 10  # Sends advisory once daily around 10 AM
CHECK_INTERVAL_SECONDS = 1800


def load_price_history() -> list:
    if not os.path.exists(PRIMARY_PRICE_LOG):
        return []
    with open(PRIMARY_PRICE_LOG, 'r') as f:
        return json.load(f)


def compute_recommendation(data: list) -> str:
    """
    Applies simple decision rules over recent price history to produce
    a human-readable BUY or WAIT recommendation with reasoning.
    """
    if len(data) < 5:
        return "WAIT — Not enough price history yet to form a confident recommendation."

    recent = data[-10:] if len(data) >= 10 else data
    prices = [d['price'] for d in recent]
    latest = prices[-1]
    average = sum(prices) / len(prices)
    minimum = min(prices)

    if latest <= TARGET_PRICE:
        return f"BUY NOW — Current price ₹{latest:,} has hit your ₹{TARGET_PRICE:,} target."

    if latest <= average * 0.97:
        return (f"CONSIDER BUYING — Current price ₹{latest:,} is meaningfully below "
                f"the recent average of ₹{int(average):,}. This may be a local dip.")

    if latest == minimum:
        return (f"CONSIDER BUYING — Current price ₹{latest:,} is the lowest seen "
                f"in recent history. Diminishing returns to waiting further.")

    return (f"WAIT — Current price ₹{latest:,} is close to the recent average of "
            f"₹{int(average):,}. No strong signal to act yet.")


def run_advisory_cycle() -> None:
    data = load_price_history()
    recommendation = compute_recommendation(data)

    logger.info(f"Daily advisory: {recommendation}")
    send_notification("Buy/Wait Advisor", recommendation)
    send_sms(recommendation)


def main() -> None:
    logger.info("Buy/Wait Advisor started. Daily recommendation around %s:00.", ADVISORY_HOUR)
    last_sent_date = None

    while True:
        now = datetime.now()
        if now.hour == ADVISORY_HOUR and now.date() != last_sent_date:
            run_advisory_cycle()
            last_sent_date = now.date()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
