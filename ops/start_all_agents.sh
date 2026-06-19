#!/data/data/com.termux/files/usr/bin/bash
cd ~/hmas-zero-cloud-android
python agents/data_extraction_agent.py &
python agents/predictive_analytics_engine.py &
python agents/decision_layer.py &
python agents/network_observability_agent.py &
python agents/inventory_state_listener.py &
python agents/reacquisition_agent.py &
echo "All 6 agents started."
