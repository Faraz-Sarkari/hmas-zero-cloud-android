import os
import sys
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.data_extraction_agent import DataExtractionAgent

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PLUGIN_DIR, "plugin_config.yaml")


def termux_notifier(title, message, urgent=False, config=None):
    import subprocess
    import time
    cfg = config or {}
    contact = os.environ.get("ALERT_PHONE_NUMBER", "") or cfg.get("contact", {}).get("phone", "")
    repeat_count    = cfg.get("urgent_repeat_count", 10)
    repeat_interval = cfg.get("urgent_repeat_interval_seconds", 120)
    vibrate_urgent  = cfg.get("vibrate_urgent", "1000,500,1000")
    vibrate_normal  = cfg.get("vibrate_normal", "500,200,500")
    if urgent:
        for _ in range(repeat_count):
            subprocess.Popen([
                "termux-notification", "--id", "999",
                "--title", title, "--content", message,
                "--priority", "high", "--vibrate", vibrate_urgent, "--ongoing",
            ])
            if contact:
                subprocess.Popen(["termux-sms-send", "-n", contact, message])
            time.sleep(repeat_interval)
    else:
        subprocess.Popen([
            "termux-notification",
            "--title", title, "--content", message,
            "--priority", "high", "--vibrate", vibrate_normal,
        ])
        if contact:
            subprocess.Popen(["termux-sms-send", "-n", contact, message])


def make_on_results(config):
    """Returns an on_results callback with config explicitly bound — safe to import."""
    def on_results(results):
        from datetime import datetime
        now = datetime.now().strftime("%d %b %I:%M %p")
        target     = config.get("target", 0)
        item_label = config.get("item_label", "item")

        if not results:
            msg = f"Check [{now}] — No results under budget.\nStill watching {item_label}..."
            termux_notifier(title=f"{item_label} Check Done", message=msg, urgent=False, config=config)
            print(msg)
            return

        urgent = any(price <= target for _, price, _, _ in results)
        tiers = config.get("tiers", [
            {"max_offset": 0,    "label": "AT TARGET — BUY NOW!"},
            {"max_offset": 2000, "label": "VERY CLOSE!"},
            {"max_offset": 5000, "label": "Getting close"},
        ])
        lines = [f"DEAL FOUND — {item_label} [{now}]\n"]
        for name, price, source, url in results:
            offset = price - target
            verdict = f"₹{offset:,} away"
            for tier in sorted(tiers, key=lambda t: t["max_offset"]):
                if offset <= tier["max_offset"]:
                    verdict = tier["label"]
                    break
            lines.append(f"{name}\n  ₹{price:,} @ {source}\n  {verdict}\n  {url}\n")

        msg = "\n".join(lines)
        termux_notifier(
            title=f"{'🚨 ' if urgent else ''}{item_label} Alert",
            message=msg,
            urgent=urgent,
            config=config,
        )
        print(msg)

    return on_results


if __name__ == "__main__":
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    agent = DataExtractionAgent(
        plugin_config=config,
        plugin_dir=PLUGIN_DIR,
        on_results=make_on_results(config),
    )
    agent.start()
