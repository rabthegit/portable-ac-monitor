#!/usr/bin/env bash
set -euo pipefail

python -m venv venv
./venv/Scripts/python -m pip install --upgrade pip
./venv/Scripts/pip install -r requirements.txt

mkdir -p data logs

echo "Installed."
echo "Run:"
echo "  ./venv/Scripts/python -m acmonitor --config config.yaml --once"

