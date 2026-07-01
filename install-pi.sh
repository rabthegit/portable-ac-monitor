#!/usr/bin/env bash
set -euo pipefail

python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

mkdir -p data logs

echo "Installed."
echo "Run:"
echo "  ./venv/bin/python -m acmonitor --config config.yaml --once"

