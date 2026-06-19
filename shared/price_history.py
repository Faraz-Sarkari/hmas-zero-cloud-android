"""
Shared price-history storage.

Single source of truth for the price log's path and format, used by the
Data Extraction Agent (writer) and Predictive Analytics Engine (reader),
so both agents always agree on where the data lives and how it's shaped.
"""
import json
import os
from datetime import datetime

from config import settings


def load_price_history() -> list:
    """Loads logged price history. Returns [] if no data has been logged yet."""
    if not os.path.exists(settings.PRICE_LOG_PATH):
        return []
    with open(settings.PRICE_LOG_PATH, 'r') as f:
        return json.load(f)


def log_price(price, site) -> None:
    """Appends one observed price point to the shared history file."""
    os.makedirs(os.path.dirname(settings.PRICE_LOG_PATH), exist_ok=True)
    data = load_price_history()
    data.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "price": price,
        "site": site,
    })
    with open(settings.PRICE_LOG_PATH, 'w') as f:
        json.dump(data, f)
