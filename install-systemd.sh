#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(id -un)"

if [[ ! -x "$APP_DIR/.venv/bin/acmonitor" ]]; then
  "$APP_DIR/install.sh"
fi

sudo sed \
  -e "s|__APP_DIR__|$APP_DIR|g" \
  -e "s|__USER__|$USER_NAME|g" \
  "$APP_DIR/systemd/acmonitor.service" \
  | sudo tee /etc/systemd/system/acmonitor.service >/dev/null
sudo cp "$APP_DIR/systemd/acmonitor.timer" /etc/systemd/system/acmonitor.timer
sudo systemctl daemon-reload

echo "Installed systemd files."
echo "Enable with: sudo systemctl enable --now acmonitor.timer"
