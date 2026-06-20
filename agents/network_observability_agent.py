"""
network_observability_agent.py — Network Monitor
=================================================
Generic. Checks Tor proxy + reachability of any configured domains.
All domains and proxy settings come from config.
"""

import socket
import time
import os
import subprocess

import requests
from stem import Signal
from stem.control import Controller

from shared.logger import get_logger
from shared.notifier import send_notification

logger = get_logger("network_observability_agent")


def is_tor_alive(host: str = "127.0.0.1", port: int = 9050) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=3)
        s.close()
        return True
    except Exception:
        return False


def request_new_tor_circuit(password: str = None) -> bool:
    """Requests a fresh Tor circuit (new exit IP) without a full restart."""
    password = password or os.environ.get("TOR_CONTROL_PASSWORD", "changeme")
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)
        time.sleep(5)
        return True
    except Exception as e:
        logger.warning(f"Failed to request new Tor circuit: {e}")
        return False


def check_domain(domain: str, proxies: dict) -> bool:
    try:
        r = requests.get(f"https://{domain}", proxies=proxies, timeout=10)
        return r.status_code < 500
    except Exception:
        return False


def run_network_check(config: dict) -> None:
    proxy_cfg = config.get("network", {}).get("tor_proxy", {})
    use_tor = config.get("network", {}).get("use_tor", False)
    domains = config.get("monitored_domains", [])

    if use_tor:
        alive = is_tor_alive()
        if not alive:
            logger.warning("Tor is DOWN. Attempting restart...")
            subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(8)
            alive = is_tor_alive()
        logger.info(f"Tor alive: {alive}")
        if not alive:
            msg = "Network Monitor: Tor is DOWN and restart failed. Scraping is blocked."
            logger.warning(msg)
            send_notification("Network Monitor: Tor Down", msg)
            return
        proxies = proxy_cfg
    else:
        proxies = {}

    unreachable = [d for d in domains if not check_domain(d, proxies)]

    if unreachable and use_tor:
        logger.warning(f"Unreachable via current circuit: {unreachable}. Requesting new Tor circuit...")
        if request_new_tor_circuit():
            unreachable = [d for d in unreachable if not check_domain(d, proxies)]

    if unreachable:
        msg = "Unreachable sites: " + ", ".join(unreachable)
        logger.warning(msg)
        send_notification("Network Monitor: Sites Down", msg)
    else:
        logger.info("All domains reachable. Network healthy.")


def main(config: dict) -> None:
    interval = config.get("network_check_interval_seconds", 1800)
    logger.info("Network Observability Agent started. Interval: %ss.", interval)
    while True:
        run_network_check(config)
        time.sleep(interval)


if __name__ == "__main__":
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../config/user_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    main(config)
