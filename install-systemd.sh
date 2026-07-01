#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(id -un)"

sudo cp systemd/acmonitor.service /etc/systemd/system/acmonitor.service
sudo cp systemd/acmonitor.timer /etc/systemd/system/acmonitor.timer

sudo sed -i "s|__APP_DIR__|$APP_DIR|g" /etc/systemd/system/acmonitor.service
sudo sed -i "s|__USER__|$USER_NAME|g" /etc/systemd/system/acmonitor.service

sudo systemctl daemon-reload

echo "Installed systemd files."
echo "Enable with:"
echo "  sudo systemctl enable --now acmonitor.timer"

