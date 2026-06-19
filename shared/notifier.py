"""
Shared notification utility for sending Android push notifications and SMS
across all agents in the multi-agent system.
"""
import subprocess
import sys
import os

sys.path.append(os.path.expanduser("~/multi-agent-system"))
from config.settings import CONTACT_NUMBER


def send_notification(title: str, message: str, priority: str = "high") -> None:
    """Sends a native Android push notification via Termux:API."""
    subprocess.Popen([
        'termux-notification',
        '--title', title,
        '--content', message,
        '--priority', priority,
        '--vibrate', '500,200,500'
    ])


def send_sms(message: str) -> None:
    """Sends an SMS to the configured contact number via Termux:API."""
    subprocess.Popen(['termux-sms-send', '-n', CONTACT_NUMBER, message])
