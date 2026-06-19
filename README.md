# HMAS — Zero Cloud. Zero Budget. Just Architecture.

A production-grade Heterogeneous Multi-Agent System built entirely on an Android device using Python and Termux — no cloud infrastructure, no laptop, no API costs.

## What This Is

Most multi-agent systems are built on cloud servers with dedicated hardware, managed infrastructure, and significant budget. This one runs entirely on a phone.

HMAS is a system of six autonomous agents running concurrently, each with a distinct responsibility, communicating through shared state files. The architecture follows a decoupled, OS-level process model — similar to a microservices pattern — with zero infrastructure cost.

Built to solve a real problem: monitoring retail price data across multiple platforms without access to a GPU, a laptop, or a cloud subscription.

## The Problem It Solves

Retail price data is volatile. Manual monitoring is impossible at scale. Cloud solutions are expensive. This system automates the entire pipeline — from data collection to buy/wait recommendations — running silently on edge hardware most people use only for social media.

## System Architecture

Six agents. Each independently responsible. All communicating through shared state.

| Agent | Responsibility |
|---|---|
| **Data Extraction Agent** | Syncs catalog data across 9 retail platforms every 4 hours via distributed egress routing |
| **Predictive Analytics Engine** | Runs a local linear regression model over historical price vectors to forecast target baseline |
| **Decision Layer** | Synthesizes pricing trends into automated BUY/WAIT recommendations backed by telemetry |
| **Network Observability Agent** | Watches process health for data worker and background interfaces, triggering recovery on silent hangs |
| **Inventory State Listener** | Monitors high-volatility out-of-stock SKUs on a high-frequency polling thread, firing instant notifications on allocation |
| **Reacquisition Agent** | Targets and reacquires dropped or failed data connections based on decision layer signals |

## For Non-Technical Readers

Think of it like a team of six specialists working around the clock inside a single phone:

- One tracks prices across nine shopping platforms
- One predicts where prices are heading
- One decides whether to buy now or wait
- One makes sure the whole team stays healthy and running
- One watches for out-of-stock items and alerts instantly when they're back
- One recovers any dropped connections automatically

No human involvement needed once it's running. No cloud bill. No laptop left on overnight.

## Key Engineering Challenges Solved

- Distributed network routing and circuit stability on a constrained device
- Aggressive rate-limit handling across multiple retail platforms
- Filtering telemetry anomalies — ghost stock and stale caching — to prevent false positives
- Localized Termux:API hardware sandbox permissions
- Strict fail-safe over fail-open strategy during routing drops
- Self-healing process supervision via a watchdog loop that auto-restarts any crashed agent and survives full device reboots

## How to Run

1. Install Termux and Termux:API and Termux:Boot from F-Droid (Google Play versions are not supported)
2. Clone this repository and install dependencies:
3. Set your alert phone number as an environment variable:
4. To start all agents at once, run: `bash ops/start_all_agents.sh` — or run any single agent individually, e.g.:
5. For auto-restart on crash and phone reboot, the `ops/` folder contains `start-agent.sh` and `watchdog.sh` for Termux:Boot integration
6. To start all 6 agents at once, run: `bash ops/start_all_agents.sh`

Note: this is a working proof-of-concept architecture. A unified launcher to start all 6 agents together is a planned next step.

## Reporting & Alerts

All reporting happens on-device — no external services, no cloud dashboards.

- **Routine checks:** after each scheduled price check, a standard Android push notification and SMS are sent via Termux:API, summarizing current prices and stock status across all 9 platforms.
- **Emergency mode:** if any tracked price drops to or below the target budget, the system switches to high-priority alerting — sending a notification and SMS every 2 minutes for 20 minutes straight, with stronger vibration patterns, to guarantee the alert isn't missed.
- All communication uses Termux:API's native `termux-notification` and `termux-sms-send` commands — no third-party messaging APIs, no recurring costs.

## Stack

- **Language:** Python
- **Environment:** Termux (Android)
- **Communication:** Shared state files
- **ML:** Local linear regression (no external model APIs)
- **Infrastructure cost:** $0

## Status

Documentation live. Architecture complete. Full source code available in this repository.

## Why This Matters

Edge AI is not a future concept — it's already here. This project demonstrates that production-grade autonomous systems can be designed, deployed, and maintained on hardware that fits in your pocket, with no dependency on cloud providers or expensive infrastructure.

That has implications for emerging markets, resource-constrained organizations, and anyone building AI systems that need to operate where the internet is unreliable or cloud costs are prohibitive.

---

Built by **Faraz Sarkari** — CS student, systems thinker.
Open to internships and consulting in Agentic AI, Multi-Agent Systems Design, and AI Solutions Architecture.
