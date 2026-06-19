"""
Centralized logging utility for all agents in the HMAS framework.
Compatible with any Termux/Android deployment path.
"""
import logging
import os
import sys

# Resolve project root dynamically — works regardless of where the repo is cloned
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import LOG_DIR


def get_logger(agent_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger for any agent in the system.

    Args:
        agent_name: Identifier for the agent (used as log filename and logger name).
        level:      Logging level. Defaults to INFO. Pass logging.DEBUG for verbose output.

    Returns:
        A Logger instance writing to both console and logs/<agent_name>.log
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{agent_name}.log")

    logger = logging.getLogger(agent_name)
    logger.setLevel(level)

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
