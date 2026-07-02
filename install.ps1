$ErrorActionPreference = "Stop"

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e .

if (-not (Test-Path config.yaml)) {
    Copy-Item config.example.yaml config.yaml
}
New-Item -ItemType Directory -Force data, logs | Out-Null

Write-Host "Installed. Edit config.yaml, then run:"
Write-Host "  .\.venv\Scripts\acmonitor.exe --once"
