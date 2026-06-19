"""
Central configuration for the Heterogeneous Multi-Agent RTX Price Intelligence System.
"""
import os

# Budget thresholds
BUDGET_CEILING = 60000
TARGET_PRICE = 55000
WARNING_THRESHOLD = 57000

# Contact info
CONTACT_NUMBER = os.environ.get("ALERT_PHONE_NUMBER", "")

# Paths
BASE_DIR = os.path.expanduser("~/multi-agent-system")
PRICE_LOG_PATH = os.path.join(BASE_DIR, "shared", "price_history.json")
AGENT_STATUS_PATH = os.path.join(BASE_DIR, "shared", "agent_status.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Tor proxy
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# Scheduler times
CHECK_TIMES = ["08:00", "13:00", "18:00", "21:00"]
