"""
Central configuration for the HMAS Zero-Cloud Framework.
All user-specific values are loaded from config/user_config.yaml —
edit that file, not this one.
"""
import os
import yaml

# Resolve project root dynamically (works wherever the repo is cloned)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load user config
_CONFIG_PATH = os.path.join(BASE_DIR, "config", "user_config.yaml")

with open(_CONFIG_PATH, "r") as _f:
    _cfg = yaml.safe_load(_f)

# Thresholds
BUDGET_CEILING    = _cfg["thresholds"]["budget_ceiling"]
TARGET_PRICE       = _cfg["thresholds"]["target_price"]
WARNING_THRESHOLD = _cfg["thresholds"]["warning_threshold"]

# Contact
CONTACT_NUMBER = os.environ.get("ALERT_PHONE_NUMBER") or _cfg.get("contact", {}).get("phone", "")

# Product / plugin selection
PRODUCT_NAME   = _cfg.get("product", {}).get("name", "Item")
SOURCES_MODULE = _cfg.get("sources_module", "examples.retail_price_monitor.sources")

LOG_DIR           = os.path.join(BASE_DIR, "logs")

# Network
_tor = _cfg.get("network", {}).get("tor_proxy", {})
TOR_PROXY = {
    "http":  _tor.get("http",  "socks5h://127.0.0.1:9050"),
    "https": _tor.get("https", "socks5h://127.0.0.1:9050"),
} if _cfg.get("network", {}).get("use_tor", True) else None

# Scheduler
CHECK_TIMES = _cfg.get("scheduler", {}).get("check_times", ["08:00", "13:00", "18:00", "21:00"])
