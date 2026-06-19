"""
Predictive Analytics Engine: HMAS Framework
============================================
Responsibility: Reads historical price data logged by the Data Extraction
Agent, applies a linear regression trend model, and forecasts the
estimated date the configured target price will be reached.

This agent contains no domain-specific logic — all thresholds, paths, and
schedule assumptions come from config/user_config.yaml via config/settings.
"""
import time

from config import settings
from shared.logger import get_logger
from shared.notifier import send_notification
from shared.price_history import load_price_history

logger = get_logger("predictive_analytics_engine")

CHECK_INTERVAL_SECONDS = 3600  # how often this agent re-analyzes the trend

# Derive how many observations are logged per day from the configured
# schedule, instead of assuming a fixed number of daily checks.
OBSERVATIONS_PER_DAY = max(len(settings.CHECK_TIMES), 1)


def compute_linear_trend(data: list) -> dict:
    """
    Computes a simple linear regression (least squares) over price vs.
    time index, returning slope (price change per data point) and the
    most recent observed price.
    """
    n = len(data)
    if n < 3:
        return {"status": "insufficient_data", "points": n}

    prices = [d['price'] for d in data]
    x_values = list(range(n))

    x_mean = sum(x_values) / n
    y_mean = sum(prices) / n

    numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return {"status": "no_variance", "points": n}

    slope = numerator / denominator
    latest_price = prices[-1]

    return {
        "status": "ok",
        "slope_per_observation": slope,
        "latest_price": latest_price,
        "points": n
    }


def estimate_days_to_target(trend: dict) -> str:
    """Converts the regression slope into a human-readable forecast."""
    if trend["status"] != "ok":
        return f"Insufficient data for prediction ({trend['points']} points logged)."

    slope = trend["slope_per_observation"]
    latest_price = trend["latest_price"]

    if slope >= 0:
        return "Price trend is flat or rising. No reliable forecast to target."

    observations_needed = (latest_price - settings.TARGET_PRICE) / abs(slope)
    days_needed = round(observations_needed / OBSERVATIONS_PER_DAY, 1)

    return (
        f"{settings.PRODUCT_NAME}: projected to reach target price "
        f"({settings.TARGET_PRICE}) in approximately {days_needed} days "
        f"at current trend."
    )


def run_prediction_cycle() -> None:
    data = load_price_history()
    trend = compute_linear_trend(data)
    forecast = estimate_days_to_target(trend)

    logger.info(f"Trend analysis: {trend}")
    logger.info(f"Forecast: {forecast}")

    send_notification("Predictive Analytics Update", forecast)


def main() -> None:
    logger.info("Predictive Analytics Engine started. Analyzing trend every %s seconds.", CHECK_INTERVAL_SECONDS)
    while True:
        run_prediction_cycle()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
