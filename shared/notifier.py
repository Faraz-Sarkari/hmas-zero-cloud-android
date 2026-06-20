"""
Shared notification utility for sending Android push notifications and SMS
across all agents in the HMAS framework.
"""
import subprocess

from config.settings import CONTACT_NUMBER


def send_notification(title: str, message: str, priority: str = "high") -> None:
    """Sends a native Android push notification via Termux:API."""
    try:
        subprocess.Popen([
            "termux-notification",
            "--title", title,
            "--content", message,
            "--priority", priority,
            "--vibrate", "500,200,500",
        ])
    except FileNotFoundError:
        print(f"[notifier] termux-notification not found — is Termux:API installed?")
    except Exception as e:
        print(f"[notifier] send_notification failed: {e}")


def send_sms(message: str) -> None:
    """Sends an SMS to the configured contact number via Termux:API."""
    if not CONTACT_NUMBER:
        print("[notifier] send_sms skipped — no CONTACT_NUMBER configured.")
        return
    try:
        subprocess.Popen(["termux-sms-send", "-n", CONTACT_NUMBER, message])
    except FileNotFoundError:
        print(f"[notifier] termux-sms-send not found — is Termux:API installed?")
    except Exception as e:
        print(f"[notifier] send_sms failed: {e}")
