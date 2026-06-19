#!/data/data/com.termux/files/usr/bin/bash
while true; do
    echo "Starting agent..."
    python ~/rtx-agent/agent.py
    echo "Agent crashed! Restarting in 10 seconds..."
    termux-notification --title "RTX Agent" --content "Agent crashed! Restarting..." --priority high
    sleep 10
done
