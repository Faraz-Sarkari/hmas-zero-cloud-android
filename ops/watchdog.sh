#!/data/data/com.termux/files/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENTRY_POINT="${1:-$PROJECT_ROOT/examples/retail_price_monitor/run.py}"
AGENT_LABEL="${2:-HMAS Agent}"

while true; do
    echo "Starting $AGENT_LABEL..."
    PYTHONPATH="$PROJECT_ROOT" python "$ENTRY_POINT"
    echo "$AGENT_LABEL crashed! Restarting in 10 seconds..."
    termux-notification \
        --title "$AGENT_LABEL" \
        --content "Agent crashed! Restarting..." \
        --priority high
    sleep 10
done
