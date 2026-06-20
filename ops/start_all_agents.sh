#!/data/data/com.termux/files/usr/bin/bash
# Starts selected HMAS agents, each under its own watchdog instance.
# Control which agents run via `enabled_agents` in plugin_config.yaml.
# Defaults to all 6 if the key is absent.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WATCHDOG="$SCRIPT_DIR/watchdog.sh"
CONFIG="$PROJECT_ROOT/examples/retail_price_monitor/plugin_config.yaml"

cd "$PROJECT_ROOT" || { echo "ERROR: Could not cd to $PROJECT_ROOT"; exit 1; }

# Read enabled_agents list from config (requires python3 + pyyaml)
ENABLED=$(python3 - << PYEOF
import yaml, sys
try:
    cfg = yaml.safe_load(open("$CONFIG"))
    agents = cfg.get("enabled_agents", [
        "data_extraction", "predictive_analytics", "decision_layer",
        "network_observability", "inventory_state_listener", "reacquisition"
    ])
    print("\n".join(agents))
except Exception as e:
    print("ERROR: " + str(e), file=sys.stderr)
    sys.exit(1)
PYEOF
)

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to read config. Check plugin_config.yaml."
    exit 1
fi

echo "Starting agents: $(echo $ENABLED | tr '\n' ' ')"

echo "$ENABLED" | while read -r agent; do
    case "$agent" in
        data_extraction)
            bash "$WATCHDOG" "$PROJECT_ROOT/examples/retail_price_monitor/run.py" "Data Extraction Agent" &
            ;;
        predictive_analytics)
            bash "$WATCHDOG" "$PROJECT_ROOT/agents/predictive_analytics_engine.py" "Predictive Analytics Engine" &
            ;;
        decision_layer)
            bash "$WATCHDOG" "$PROJECT_ROOT/agents/decision_layer.py" "Decision Layer" &
            ;;
        network_observability)
            bash "$WATCHDOG" "$PROJECT_ROOT/agents/network_observability_agent.py" "Network Observability Agent" &
            ;;
        inventory_state_listener)
            bash "$WATCHDOG" "$PROJECT_ROOT/agents/inventory_state_listener.py" "Inventory State Listener" &
            ;;
        reacquisition)
            bash "$WATCHDOG" "$PROJECT_ROOT/agents/reacquisition_agent.py" "Reacquisition Agent" &
            ;;
        *)
            echo "WARNING: Unknown agent '$agent' in enabled_agents — skipping."
            ;;
    esac
done

echo "All selected agents started under watchdog supervision."
