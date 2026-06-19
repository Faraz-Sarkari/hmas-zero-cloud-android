# Product Requirements Document — HMAS
### Heterogeneous Multi-Agent System for Zero-Cloud Retail Price Monitoring

**Author:** Faraz Sarkari

**Status:** Architecture complete · all 6 agents implemented · self-healing supervision live

**Repo:** github.com/faraz-sarkari/hmas-zero-cloud-android

---

## 1. Problem Statement

Retail prices on high-demand items move without warning, and stock windows for the same items can close in minutes. Watching this manually doesn't scale past one or two products, and the obvious alternative — a cloud-hosted monitoring service — introduces a recurring bill and a piece of infrastructure that has to be paid for and maintained indefinitely, for what is fundamentally a personal, low-throughput problem.

HMAS exists to answer one question continuously, without a human watching: **is right now a good time to buy, and is the item even available?** It does this by running entirely on hardware the user already owns and never turns off — an Android phone — with no server, no API subscription, and no recurring cost.

## 2. Goals

- Continuously sync catalog/price data across 9 retail platforms on a fixed schedule.
- Convert raw price history into a forecasted baseline, so the system can judge a price against where prices are *trending*, not just whether it changed.
- Collapse that judgment into a single actionable signal: BUY or WAIT.
- Detect stock-availability changes (in vs. out of stock) on a much tighter loop than price, since availability windows are shorter-lived than price trends.
- Run unattended, indefinitely, recovering from its own crashes and from full device reboots.
- Hold infrastructure cost at $0 — no cloud compute, no paid APIs, no third-party messaging services.

## 3. Non-Goals

- Not a general-purpose scraping framework — it's scoped to the platforms and items it was built to watch.
- Not built for multi-user or high-request-volume use — this is a single-device, single-owner system by design.
- Not optimized for sub-second latency. A 4-hour extraction cycle and polling-based listeners are a deliberate cost/freshness tradeoff, not a limitation the team is trying to engineer away.
- Not a cloud-portable service. Portability off the phone was explicitly *not* a requirement — proving the opposite (that this class of system doesn't need cloud) is the point of the project.

## 4. Why This Architecture (System Design Reasoning)

### 4.1 Why six separate agents instead of one script
Each responsibility has a different failure mode and a different rhythm: extraction fails because a platform rate-limits or changes its page; forecasting fails because of bad input data, not network issues; the decision layer should never go down just because one retail platform is being difficult that hour. Splitting along these fault lines means a failure in one agent doesn't take the rest of the system down with it — the decision layer can still work off the last good forecast even if extraction is mid-retry. This is the same reasoning behind a microservices split, applied at OS-process granularity instead of network-service granularity.

### 4.2 Why shared state files instead of direct agent-to-agent calls
There's no message broker or RPC layer available — or worth building — on a phone with no persistent server process. Flat shared-state files solve the same coordination problem with three properties a broker doesn't give for free here: they survive a crash or reboot without any replay logic (the last written state is just *there* on disk), they're debuggable with nothing more than reading a file, and they decouple every agent's read/write cadence from every other agent's — nobody is blocked waiting on a call to return. It's effectively a poor-man's pub/sub, traded down in sophistication on purpose because the deployment target doesn't support anything heavier.

### 4.3 Why a phone instead of a laptop or cloud instance
A phone is already on, already charged, and already paid for — it's the one piece of compute most people leave running 24/7 without thinking about it. Termux turns that into a real Linux userland capable of running Python, cron-like scheduling, and background processes. The architectural bet is that "production-grade" doesn't have to mean "cloud-hosted" — it means decoupled, fault-isolated, and self-recovering, and none of those properties actually require a data center.

### 4.4 Why a watchdog / self-healing supervision layer
Any process left running unattended on consumer hardware for long enough will eventually crash — OOM kills, dropped network state, a malformed response from a retail platform. Without supervision, a crash is silent and permanent until someone notices the alerts stopped. The watchdog turns "crashes" from an outage into a non-event, and Termux:Boot integration extends the same guarantee across a full device reboot, so the system never needs a human to restart it.

## 5. The Six Agents

| Agent | Responsibility | Cadence |
|---|---|---|
| **Data Extraction Agent** | Syncs catalog/price data across 9 retail platforms via distributed egress routing | Every 4 hours |
| **Predictive Analytics Engine** | Local linear regression over historical price vectors to forecast a target baseline | After each extraction cycle |
| **Decision Layer** | Synthesizes price trend + forecast into a BUY/WAIT recommendation | After each forecast update |
| **Network Observability Agent** | Watches process health of data + background workers, triggers recovery on silent hangs | Continuous |
| **Inventory State Listener** | High-frequency polling for out-of-stock SKUs, fires instant alerts on restock | High-frequency loop |
| **Reacquisition Agent** | Re-establishes dropped/failed data connections based on signals from the Decision Layer | Event-triggered |

## 6. Non-Functional Requirements

- **Cost:** $0 recurring infrastructure spend, by design, not as a stretch goal.
- **Resilience:** every agent must be independently restartable; the system must survive a full device reboot with zero manual intervention.
- **Resource constraints:** must operate inside Termux's sandbox permission model and stay mindful of a phone's battery and mobile data budget — this rules out anything compute-heavy, which is part of why forecasting uses a local linear regression rather than a heavier model.
- **Observability:** all state must be inspectable with nothing more than a text viewer — no dashboard, no log aggregator.
- **Alert reliability:** a real buy-trigger event must escalate (repeated notification + SMS, stronger vibration) rather than firing once and risking being missed.

## 7. System Architecture Overview

See `architecture-diagram.svg` in the repo root. At a glance: all six agents are peers around a shared-state hub — none of them call each other directly. A separate watchdog/launcher process supervises all six from outside that data flow, restarting any agent that dies and re-launching the full set on device boot.

## 8. Data Flow (High Level)

1. **Data Extraction Agent** writes fresh price/catalog data to shared state.
2. **Predictive Analytics Engine** reads that state, computes a forecast, writes it back.
3. **Decision Layer** reads raw data + forecast, writes a BUY/WAIT recommendation.
4. The reporting layer reads the recommendation and fires the appropriate notification (routine summary, or emergency high-priority alert if a buy threshold is hit).

Running in parallel, on independent loops: **Network Observability Agent** watches process health and can trigger recovery at any point; **Inventory State Listener** polls stock state and can fire an alert outside the above cycle entirely, since stock changes don't wait for the 4-hour extraction window; **Reacquisition Agent** listens for connection-drop signals and re-establishes them without waiting to be told by a human.

## 9. Success Metrics

- Agent crash-to-recovery time (watchdog restart latency).
- Time from a stock-availability change to a delivered notification.
- Zero missed "price at or below target" events over an observation period.
- Sustained $0 infrastructure cost over the system's operating lifetime.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Retail platforms rate-limit or block repeated requests | Distributed egress routing, aggressive rate-limit handling across platforms |
| Stale cache or "ghost stock" produces false buy/restock signals | Telemetry anomaly filtering before signals reach the Decision Layer |
| The phone itself is a single point of failure — no redundant hardware | Accepted tradeoff at this budget; mitigated by watchdog + boot-survival, not by redundancy |
| Routing/network instability mid-cycle | Fail-safe (not fail-open) strategy — the system favors missing a cycle over acting on bad data |

## 11. Out of Scope / Future Work

- Multi-user or multi-device support.
- An optional cloud failover path for when the phone is offline for an extended period.
- Expanding beyond price/stock monitoring into a more general edge-agent framework.

## 12. Open Questions

- What specific circuit-breaker thresholds govern when the Reacquisition Agent gives up vs. retries?
- What does "silent hang" detection actually check for in the Network Observability Agent?
- These are being resolved agent-by-agent in the code walkthrough track of this project's documentation.
