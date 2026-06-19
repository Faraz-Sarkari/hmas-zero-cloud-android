"""
network_observability_agent.py — Agent Monitor
===============================================
Generic. Watches configured process names for health.
Alerts if any monitored process goes down.
All process names come from config.
"""

import subprocess
import time
import os

from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("network_observability_agent")


def is_process_running(keyword: str) -> bool:
    try:
        result = subprocess.run(["pgrep", "-f", keyword], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to check process '{keyword}': {e}")
        return False


def run_monitor_cycle(config: dict) -> None:
    processes = config.get("monitored_processes", [])
    all_healthy = True

    for proc in processes:
        name = proc.get("name", proc.get("keyword"))
        keyword = proc.get("keyword")
        alive = is_process_running(keyword)
        logger.info(f"{name}: alive={alive}")

        if not alive:
            all_healthy = False
            msg = f"ALERT: {name} is DOWN.\n{proc.get('down_message', 'Process not running.')}"
            logger.warning(msg)
            send_notification(f"Monitor: {name} Down", msg)
            send_sms(msg)

    if all_healthy:
        logger.info("All processes healthy.")


def main(config: dict) -> None:
    interval = config.get("monitor_interval_seconds", 1800)
    logger.info("Network Observability Agent started. Interval: %ss.", interval)
    while True:
        run_monitor_cycle(config)
        time.sleep(interval)


if __name__ == "__main__":
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../user_config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    main(config)
