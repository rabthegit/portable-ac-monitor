#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

"$APP_DIR/install.sh"

echo "Raspberry Pi setup complete."
echo "Edit $APP_DIR/config.yaml, then run:"
echo "  $APP_DIR/.venv/bin/acmonitor --once"
echo "Optional systemd setup:"
echo "  $APP_DIR/install-systemd.sh"
