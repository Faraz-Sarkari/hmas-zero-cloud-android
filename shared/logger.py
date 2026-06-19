"""
Centralized logging utility for all agents in the system.
"""
import logging
import os
import sys

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from config.settings import LOG_DIR

def get_logger(agent_name: str) -> logging.Logger:
    """
    Returns a configured logger instance for a given agent.
    Logs to both console and a dedicated file per agent.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{agent_name}.log")

    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
