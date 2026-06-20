#!/data/data/com.termux/files/usr/bin/bash
# HMAS First-Run Setup Script
# Run once after cloning: bash setup.sh

set -e

echo "==> Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "==> Installing system dependencies..."
pkg install -y python git tor

echo "==> Installing Python dependencies..."
pip install --break-system-packages -r requirements.txt

echo "==> Creating runtime directories..."
mkdir -p ~/agent-data
mkdir -p logs
mkdir -p data

echo "==> Setting up user config..."
if [ ! -f config/user_config.yaml ]; then
    cp config/user_config.example.yaml config/user_config.yaml
    echo "    Created config/user_config.yaml — edit it before starting agents."
else
    echo "    config/user_config.yaml already exists — skipping."
fi

echo "==> Setting executable permissions on ops scripts..."
chmod +x ops/start_all_agents.sh
chmod +x ops/watchdog.sh
chmod +x ops/start-agent.sh

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit config/user_config.yaml with your target price, phone number, etc."
echo "  2. Start Tor:         tor &"
echo "  3. Start all agents:  bash ops/start_all_agents.sh"
echo "  4. For auto-start on reboot, copy ops/start-agent.sh to ~/.termux/boot/"
echo "     mkdir -p ~/.termux/boot && cp ops/start-agent.sh ~/.termux/boot/"
