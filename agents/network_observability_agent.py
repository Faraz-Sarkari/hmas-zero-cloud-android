"""
Agent Monitor: Heterogeneous Multi-Agent System (HMAS)
========================================================
Responsibility: Watches the health of the primary price-hunting agent
(rtx-agent) and the supporting infrastructure (Tor process). If the
primary agent process is not running, or Tor is down, this agent
raises an alert so the user is never silently left unprotected.

This agent embodies the "observability" layer of the system.
"""
import subprocess
import time
import sys
import os

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from shared.logger import get_logger
from shared.notifier import send_notification, send_sms

logger = get_logger("agent_monitor")

CHECK_INTERVAL_SECONDS = 1800  # 10 minutes


def is_process_running(keyword: str) -> bool:
    """Checks if a process containing `keyword` is currently running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', keyword],
            capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to check process '{keyword}': {e}")
        return False


def run_monitor_cycle() -> None:
    """Single health-check cycle of the primary agent + Tor."""
    agent_alive = is_process_running("rtx-agent/agent.py")
    tor_alive = is_process_running("tor")

    logger.info(f"rtx-agent alive: {agent_alive} | tor alive: {tor_alive}")

    if not agent_alive:
        msg = "ALERT: Primary RTX price agent is DOWN. It is not currently monitoring prices."
        logger.warning(msg)
        send_notification("Agent Monitor: Primary Agent Down", msg)
        send_sms(msg)

    if not tor_alive:
        msg = "ALERT: Tor process is DOWN. Scraping is currently halted (privacy-safe failover)."
        logger.warning(msg)
        send_notification("Agent Monitor: Tor Down", msg)
        send_sms(msg)

    if agent_alive and tor_alive:
        logger.info("System healthy. No action needed.")


def main() -> None:
    logger.info("Agent Monitor started. Watching system health every %s seconds.", CHECK_INTERVAL_SECONDS)
    while True:
        run_monitor_cycle()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
