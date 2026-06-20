"""
validator.py — Generic Result Validation Layer
=================================================
Knows nothing about GPUs, retail sites, or any specific domain.

Catches three classes of bad data before they reach the Decision Layer:
  1. Price anomalies   — scraped price is implausibly far below recent history
  2. Title mismatches  — scraped title doesn't contain expected brand/keyword terms
  3. Cross-source drift — one source's price disagrees wildly with others in the
                           same check cycle

All thresholds are config-driven. No hardcoded product or brand names.
"""

from statistics import mean
from typing import List, Tuple, Optional


def is_price_anomalous(price, recent_prices, max_drop_pct=0.35):
    if len(recent_prices) < 3:
        return False
    avg = mean(recent_prices)
    if avg <= 0:
        return False
    drop = (avg - price) / avg
    return drop > max_drop_pct


def title_matches_expected(title, expected_keywords, min_matches=1):
    if not expected_keywords:
        return True
    title_lower = title.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in title_lower)
    return hits >= min_matches


def find_outlier_sources(results, max_deviation_pct=0.30):
    if len(results) < 2:
        return []
    prices = sorted(p for _, p, _, _ in results)
    n = len(prices)
    median = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2
    if median <= 0:
        return []
    outliers = []
    for name, price, source, url in results:
        deviation = abs(price - median) / median
        if deviation > max_deviation_pct:
            outliers.append(source)
    return outliers


def validate_result(
    name, price, source,
    recent_prices=None, expected_keywords=None, outlier_sources=None,
    max_drop_pct=0.35, min_keyword_matches=1,
):
    reasons = []
    if recent_prices and is_price_anomalous(price, recent_prices, max_drop_pct):
        reasons.append(f"price ₹{price:,.0f} is >{int(max_drop_pct*100)}% below recent average")
    if expected_keywords and not title_matches_expected(name, expected_keywords, min_keyword_matches):
        reasons.append(f"title does not match expected keywords {expected_keywords}")
    if outlier_sources and source in outlier_sources:
        reasons.append("price diverges sharply from other sources this cycle")
    return (len(reasons) == 0, reasons)
