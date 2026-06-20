import os
import sys
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.data_extraction_agent import DataExtractionAgent

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PLUGIN_DIR, "plugin_config.yaml")


def termux_notifier(title, message, urgent=False):
    import subprocess
    import time
    contact = os.environ.get("ALERT_PHONE_NUMBER", "")
    if urgent:
        for _ in range(10):
            subprocess.Popen([
                "termux-notification", "--id", "999",
                "--title", title, "--content", message,
                "--priority", "high", "--vibrate", "1000,500,1000", "--ongoing",
            ])
            if contact:
                subprocess.Popen(["termux-sms-send", "-n", contact, message])
            time.sleep(120)
    else:
        subprocess.Popen([
            "termux-notification",
            "--title", title, "--content", message,
            "--priority", "high", "--vibrate", "500,200,500",
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
            termux_notifier(title=f"{item_label} Check Done", message=msg, urgent=False)
            print(msg)
            return

        urgent = any(price <= target for _, price, _, _ in results)
        lines = [f"DEAL FOUND — {item_label} [{now}]\n"]
        for name, price, source, url in results:
            offset = price - target
            if offset <= 0:
                verdict = "AT TARGET — BUY NOW!"
            elif offset <= 2000:
                verdict = "VERY CLOSE!"
            elif offset <= 5000:
                verdict = "Getting close"
            else:
                verdict = f"₹{offset:,} away"
            lines.append(f"{name}\n  ₹{price:,} @ {source}\n  {verdict}\n  {url}\n")

        msg = "\n".join(lines)
        termux_notifier(
            title=f"{'🚨 ' if urgent else ''}{item_label} Alert",
            message=msg,
            urgent=urgent,
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
