"""
Network Monitor Agent: Heterogeneous Multi-Agent System (HMAS)
==================================================================
Responsibility: Monitors the health of the network/infrastructure
layer that the entire system depends on — Tor SOCKS proxy
availability, general internet connectivity, and reachability of
each of the 9 target e-commerce domains. Surfaces actionable alerts
when infrastructure degrades, helping explain "why no deals were
found" (site down vs genuinely no deal).

This agent embodies the "infrastructure / DevOps observability" layer.
"""
import socket
import time
import sys
import os
import requests

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from shared.logger import get_logger
from shared.notifier import send_notification

logger = get_logger("network_monitor")

CHECK_INTERVAL_SECONDS = 1800  # 30 minutes

TARGET_DOMAINS = [
    "www.primeabgb.com",
    "mdcomputers.in",
    "www.vedantcomputers.com",
    "elitehubs.com",
    "famberzbuilt.in",
    "www.smartprix.com",
    "www.amazon.in",
    "www.flipkart.com",
    "www.nehruplacemarket.com",
]

TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}


def is_tor_alive() -> bool:
    """Checks if the Tor SOCKS proxy port is open and accepting connections."""
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=3)
        s.close()
        return True
    except Exception:
        return False


def check_domain_reachable(domain: str) -> bool:
    """Checks if a target domain is reachable through Tor."""
    try:
        response = requests.get(f"https://{domain}", proxies=TOR_PROXY, timeout=10)
        return response.status_code < 500
    except Exception:
        return False


def run_network_check() -> None:
    tor_status = is_tor_alive()
    logger.info(f"Tor proxy reachable: {tor_status}")

    if not tor_status:
        msg = "Network Monitor: Tor proxy is DOWN. All scraping is currently blocked (fail-safe, no real-IP fallback)."
        logger.warning(msg)
        send_notification("Network Monitor: Tor Down", msg)
        return

    unreachable = []
    for domain in TARGET_DOMAINS:
        reachable = check_domain_reachable(domain)
        logger.info(f"{domain} reachable: {reachable}")
        if not reachable:
            unreachable.append(domain)

    if unreachable:
        msg = "Sites currently unreachable: " + ", ".join(unreachable)
        logger.warning(msg)
        send_notification("Network Monitor: Site(s) Down", msg)
    else:
        logger.info("All 9 target domains reachable. Network healthy.")


def main() -> None:
    logger.info("Network Monitor started. Checking infra every %s seconds.", CHECK_INTERVAL_SECONDS)
    while True:
        run_network_check()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
