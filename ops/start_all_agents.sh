#!/data/data/com.termux/files/usr/bin/bash
# Starts all 6 HMAS agents, each under its own watchdog instance.
# Any agent that crashes will be automatically restarted.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WATCHDOG="$SCRIPT_DIR/watchdog.sh"

cd "$PROJECT_ROOT" || { echo "ERROR: Could not cd to $PROJECT_ROOT"; exit 1; }

bash "$WATCHDOG" "$PROJECT_ROOT/examples/retail_price_monitor/run.py"  "Data Extraction Agent"       &
bash "$WATCHDOG" "$PROJECT_ROOT/agents/predictive_analytics_engine.py" "Predictive Analytics Engine" &
bash "$WATCHDOG" "$PROJECT_ROOT/agents/decision_layer.py"              "Decision Layer"               &
bash "$WATCHDOG" "$PROJECT_ROOT/agents/network_observability_agent.py" "Network Observability Agent"  &
bash "$WATCHDOG" "$PROJECT_ROOT/agents/inventory_state_listener.py"    "Inventory State Listener"     &
bash "$WATCHDOG" "$PROJECT_ROOT/agents/reacquisition_agent.py"         "Reacquisition Agent"          &

echo "All 6 agents started under watchdog supervision."
