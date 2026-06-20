"""
data_extraction_agent.py — Generic Data Extraction Agent
=========================================================
Knows nothing about GPUs, retail sites, or any specific domain.

Responsibilities:
  - Load scraper plugins dynamically from a plugin folder
  - Make HTTP requests (with optional proxy support)
  - Log raw results to a price/data log
  - Schedule recurring checks
  - Hand results to the Decision Layer

All domain-specific logic (what to scrape, how to parse, what to filter)
lives in the plugin's scrapers/ folder.
"""

import importlib.util
import json
import os
import schedule
import time
from datetime import datetime
from typing import Callable, List, Optional, Tuple

import requests
from shared.validator import validate_result, find_outlier_sources
from shared.notifier import send_notification


# ------------------------------------------------------------------ #
#  HTTP helper — generic, proxy-aware                                 #
# ------------------------------------------------------------------ #

def build_session(proxy_url: Optional[str] = None, user_agent: str = "Mozilla/5.0") -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    if proxy_url:
        session.proxies = {"http": proxy_url, "https": proxy_url}
    return session


def fetch(session: requests.Session, url: str, timeout: int = 20) -> Optional[requests.Response]:
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"[fetch] Error fetching {url}: {e}")
        return None


# ------------------------------------------------------------------ #
#  Price / data logging — generic                                     #
# ------------------------------------------------------------------ #

def log_result(log_path: str, price: float, source: str, extra: dict = None):
    """Append a result entry to the JSON log."""
    log_path = os.path.expanduser(log_path)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    data = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "price": price,
        "source": source,
    }
    if extra:
        entry.update(extra)

    data.append(entry)

    with open(log_path, "w") as f:
        json.dump(data, f, indent=2)


# ------------------------------------------------------------------ #
#  Plugin loader — dynamically imports scraper modules                #
# ------------------------------------------------------------------ #

def load_scrapers(plugin_dir: str, plugin_config: dict = None) -> List[Callable]:
    """
    Scans plugin_dir/scrapers/ for Python files.
    Each file must expose a `scrape(session, config) -> list` function.
    Returns a list of those callables.
    """
    scrapers_dir = os.path.join(plugin_dir, "scrapers")
    if not os.path.isdir(scrapers_dir):
        print(f"[loader] No scrapers/ folder found in {plugin_dir}")
        return []

    # If plugin config specifies enabled_scrapers, only load those files.
    # Use "all" or omit the key entirely to load everything in the folder.
    enabled = plugin_config.get("enabled_scrapers", "all") if plugin_config else "all"

    scrapers = []
    for filename in sorted(os.listdir(scrapers_dir)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        if enabled != "all" and filename not in enabled:
            print(f"[loader] Skipped {filename} — not in enabled_scrapers")
            continue
        filepath = os.path.join(scrapers_dir, filename)
        spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "scrape"):
                scrapers.append(module.scrape)
                print(f"[loader] Loaded scraper: {filename}")
            else:
                print(f"[loader] Skipped {filename} — no `scrape()` function found")
        except Exception as e:
            print(f"[loader] Failed to load {filename}: {e}")

    return scrapers


# ------------------------------------------------------------------ #
#  Core agent class                                                   #
# ------------------------------------------------------------------ #

class DataExtractionAgent:
    def __init__(self, plugin_config: dict, plugin_dir: str, on_results: Callable = None):
        """
        plugin_config: dict loaded from plugin's config file. Expected keys:
          - price_log:    path to JSON log file
          - proxy_url:    optional SOCKS5/HTTP proxy string
          - user_agent:   optional custom UA string
          - schedule:     list of "HH:MM" strings for daily check times
          - budget:       upper price ceiling (passed to scrapers for filtering)
          - target:       ideal target price (passed to scrapers)

        plugin_dir:   path to the plugin folder (contains scrapers/)
        on_results:   callback(results: list) called after each check cycle
                      results = list of (name, price, source, url) tuples
        """
        self.config = plugin_config
        self.plugin_dir = plugin_dir
        self.on_results = on_results
        self.log_path = plugin_config.get("price_log", "~/agent-data/prices.json")

        proxy_url = plugin_config.get("proxy_url")
        user_agent = plugin_config.get("user_agent", "Mozilla/5.0")
        self.session = build_session(proxy_url=proxy_url, user_agent=user_agent)

        self.scrapers = load_scrapers(plugin_dir, plugin_config)

    def run_check(self):
        now = datetime.now().strftime("%d %b %I:%M %p")
        print(f"\n[agent] Check started at {now}")

        results: List[Tuple] = []
        for scraper in self.scrapers:
            try:
                found = scraper(self.session, self.config)
                if found:
                    results.extend(found)
            except Exception as e:
                print(f"[agent] Scraper error: {e}")

        print(f"[agent] Found {len(results)} result(s) this cycle.")

        outlier_sources = find_outlier_sources(
            results, self.config.get("max_source_deviation_pct", 0.30)
        )
        recent_prices = self._load_recent_prices()
        expected_keywords = self.config.get("expected_keywords", [])

        for name, price, source, url in results:
            is_valid, reasons = validate_result(
                name, price, source,
                recent_prices=recent_prices,
                expected_keywords=expected_keywords,
                outlier_sources=outlier_sources,
                max_drop_pct=self.config.get("max_price_drop_pct", 0.35),
            )

            extra = {"name": name, "url": url}
            if not is_valid:
                extra["suspicious"] = True
                extra["flags"] = reasons
                warning = (
                    f"⚠️ Suspicious result flagged from {source}:\n"
                    f"{name} — ₹{price:,.0f}\n"
                    f"Reason(s): {'; '.join(reasons)}"
                )
                print(f"[agent] {warning}")
                send_notification("Validation Warning", warning)

            log_result(self.log_path, price, source, extra)

        if self.on_results:
            self.on_results(results)

    def _load_recent_prices(self, window: int = 10) -> List[float]:
        """Loads the last `window` prices from the log for anomaly comparison."""
        import json
        log_path = os.path.expanduser(self.log_path)
        if not os.path.exists(log_path):
            return []
        try:
            with open(log_path, "r") as f:
                data = json.load(f)
            return [d["price"] for d in data[-window:] if not d.get("suspicious")]
        except Exception:
            return []

    def start(self):
        """Schedule recurring checks and run the first one immediately."""
        check_times = self.config.get("schedule", ["08:00", "13:00", "18:00", "21:00"])
        for t in check_times:
            schedule.every().day.at(t).do(self.run_check)
            print(f"[agent] Scheduled check at {t}")

        print("[agent] Running initial check now...")
        self.run_check()

        while True:
            schedule.run_pending()
            time.sleep(30)


if __name__ == "__main__":
    import yaml

    _config_path = os.path.join(
        os.path.dirname(__file__),
        "../examples/retail_price_monitor/plugin_config.yaml",
    )
    with open(_config_path, "r") as _f:
        _config = yaml.safe_load(_f)

    _plugin_dir = os.path.join(
        os.path.dirname(__file__),
        "../examples/retail_price_monitor",
    )

    agent = DataExtractionAgent(plugin_config=_config, plugin_dir=_plugin_dir)
    agent.start()
