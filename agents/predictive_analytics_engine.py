"""
predictive_analytics_engine.py — Price Predictor Agent
=======================================================
Generic. Reads price history, runs linear regression,
forecasts when target price will be reached.
All domain values come from config.
"""

import json
import os
import time

from shared.logger import get_logger
from shared.notifier import send_notification

logger = get_logger("predictive_analytics_engine")


def load_price_history(log_path: str) -> list:
    log_path = os.path.expanduser(log_path)
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        return json.load(f)


def compute_linear_trend(data: list) -> dict:
    n = len(data)
    if n < 3:
        return {"status": "insufficient_data", "points": n}

    prices = [d["price"] for d in data]
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(prices) / n

    num = sum((x[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))

    if den == 0:
        return {"status": "no_variance", "points": n}

    return {
        "status": "ok",
        "slope": num / den,
        "latest_price": prices[-1],
        "points": n,
    }


def forecast(trend: dict, target: float, checks_per_day: int, item_label: str) -> str:
    if trend["status"] != "ok":
        return f"Insufficient data ({trend['points']} points logged)."

    slope = trend["slope"]
    latest = trend["latest_price"]

    if slope >= 0:
        return f"{item_label}: Price is flat or rising. No reliable forecast."

    observations_needed = (latest - target) / abs(slope)
    days = round(observations_needed / checks_per_day, 1)

    return f"{item_label}: Projected to reach ₹{target:,} in ~{days} days at current trend."


def run_prediction_cycle(config: dict) -> None:
    log_path = config.get("price_log", "~/agent-data/prices.json")
    target = config.get("target", 0)
    item_label = config.get("item_label", "item")
    checks_per_day = config.get("checks_per_day", 4)

    data = load_price_history(log_path)
    trend = compute_linear_trend(data)
    message = forecast(trend, target, checks_per_day, item_label)

    logger.info(message)
    send_notification("Price Predictor", message)


def main(config: dict) -> None:
    interval = config.get("prediction_interval_seconds", 3600)
    logger.info("Predictive Analytics Engine started. Interval: %ss.", interval)
    while True:
        run_prediction_cycle(config)
        time.sleep(interval)


if __name__ == "__main__":
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../user_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    main(config)
