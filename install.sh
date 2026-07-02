#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e .

if [[ ! -f config.yaml ]]; then
  cp config.example.yaml config.yaml
fi
mkdir -p data logs

echo "Installed. Edit config.yaml, then run:"
echo "  ./.venv/bin/acmonitor --once"
