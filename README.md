# HMAS — Zero Cloud. Zero Budget. Just Architecture.

A production-minded Heterogeneous Multi-Agent System built entirely on an Android device using Python and Termux — no cloud infrastructure, no laptop, no API costs.

## What This Is

Most multi-agent systems are built on cloud servers with dedicated hardware and significant budget. This one runs entirely on a phone.

HMAS is a **generic multi-agent framework** of six autonomous agents running concurrently, each with a distinct responsibility, communicating through shared state files. The architecture follows a decoupled, OS-level process model — similar to a microservices pattern — with zero infrastructure cost.

All domain-specific logic (what to track, where, thresholds) lives in config and swappable plugin folders. The core agents know nothing about what they're tracking. You can reuse the same framework to monitor anything — retail prices, concert tickets, stock alerts, job postings — by writing a new plugin instead of rewriting the agents.

The included example plugin tracks GPU retail prices across 9 Indian e-commerce platforms.

## System Architecture

Six agents. Each independently responsible. All communicating through shared state.

See `architecture-diagram.svg` for the full visual, and `PRD.md` for the requirements and design rationale.

| Agent | Responsibility |
|---|---|
| Data Extraction Agent | Dynamically loads scraper plugins and syncs data across configured sources on a schedule |
| Predictive Analytics Engine | Runs a local linear regression model over historical price data to forecast when the target will be reached |
| Decision Layer | Synthesizes trends into automated BUY/WAIT recommendations driven by configurable thresholds |
| Network Observability Agent | Monitors process health and domain reachability, alerting on infrastructure degradation |
| Inventory State Listener | Polls a watchlist of out-of-stock items on a tight interval, firing instant alerts on restock |
| Reacquisition Agent | Re-checks previously missed deals and alerts when conditions are met again |

## Plugin System

To track something new, create a folder under `examples/` with:

```
examples/
  your_plugin/
    plugin_config.yaml   # thresholds, schedule, keywords
    run.py               # wires config + notifier into the agent
    scrapers/
      site_one.py        # each file exposes scrape(session, config) -> list
      site_two.py
```

No changes to any core agent needed.

## How to Run

1. Install Termux, Termux:API, and Termux:Boot from F-Droid (Google Play versions are not supported).

2. Clone the repo and run the one-time setup script — installs all dependencies, creates runtime directories, and copies the config template:
```bash
git clone https://github.com/Faraz-Sarkari/hmas-zero-cloud-android.git
cd hmas-zero-cloud-android
bash setup.sh
```

3. Edit your config with your target price, phone number, and preferences:
```bash
nano config/user_config.yaml
```

4. Set your alert phone number as an environment variable (or put it in `config/user_config.yaml`):
```bash
export ALERT_PHONE_NUMBER="+XXXXXXXXXXX"
```

5. Start Tor (required if `use_tor: true` in config — skip otherwise). If you set up Termux:Boot, Tor starts automatically on reboot — no need to run this manually again:
```bash
tor &
```

6. Start all 6 agents, each under watchdog supervision:
```bash
bash ops/start_all_agents.sh
```

Or run any single agent individually:
```bash
python agents/data_extraction_agent.py
```

**Auto-restart on reboot (Termux:Boot):** copy `start-agent.sh` into the boot folder once:
```bash
mkdir -p ~/.termux/boot
cp ops/start-agent.sh ~/.termux/boot/
```
The watchdog restarts any crashed agent automatically and survives full device reboots.

## Reporting & Alerts

All reporting happens on-device — no external services, no cloud dashboards.

- **Routine checks:** push notification and SMS after each scheduled check, summarizing current status.
- **Emergency mode:** if price hits or drops below target, the system switches to high-priority alerting — notification and SMS every 2 minutes for 20 minutes, with stronger vibration.

All communication uses Termux:API's native `termux-notification` and `termux-sms-send` — no third-party APIs, no recurring costs.

## Validation Layer

To prevent acting on bad data — scraper errors, mismatched listings, or scam-like pricing — every scraped result passes through three automated checks before being logged or surfaced as a recommendation:

| Check | Purpose |
|---|---|
| Price Sanity | Flags any price that drops more than a configurable % below recent average — catches scraper bugs and "too good to be true" listings |
| Title/Brand Match | Flags results whose scraped title doesn't contain expected brand or product keywords — catches mismatched or garbage listings |
| Cross-Source Consistency | Flags any single source whose price diverges sharply from the median across all sources checked that cycle |

Suspicious results are still logged (tagged `suspicious: true` with reasons) but trigger an immediate warning notification instead of being silently trusted. Thresholds are fully configurable per plugin.

## Stack

- **Language:** Python
- **Environment:** Termux (Android)
- **Communication:** Shared state files
- **ML:** Local linear regression (no external model APIs)
- **Infrastructure cost:** $0

## Status

Architecture complete. All 6 agents generalized and pushed. Plugin system implemented with retail price monitor as reference example. Documentation live. Not yet load-tested for extended unattended runs — see `PRD.md` for open items.

## Why This Matters

Edge AI is not a future concept — it's already here. This project demonstrates that production-minded autonomous systems can be designed, deployed, and maintained on hardware that fits in your pocket, with no dependency on cloud providers or expensive infrastructure.

That has implications for emerging markets, resource-constrained organizations, and anyone building AI systems where the internet is unreliable or cloud costs are prohibitive.

---

Built by Faraz Sarkari — CS student, systems thinker. Open to internships and consulting in Agentic AI, Multi-Agent Systems Design, AI-Product Manager and AI Solutions Architecture.

## Proof of Concept

Live agent run on Android/Termux:

<img width="720" height="871" alt="Image" src="https://github.com/user-attachments/assets/64696780-a64a-424a-a8d4-9071f1294240" />

<img width="720" height="1435" alt="Image" src="https://github.com/user-attachments/assets/796e57e0-0170-4c5d-9413-75efa43effa5" />

<img width="720" height="1370" alt="Image" src="https://github.com/user-attachments/assets/8904c61e-c275-4bc7-b1ba-7ac5ccc8fb24" />
