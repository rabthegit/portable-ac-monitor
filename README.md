# Portable AC Monitor

A Python service that checks product pages for portable air-conditioner availability and price, stores results in SQLite, and sends an email when an eligible product becomes available.

## Setup

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp config.example.yaml config.yaml
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and use `Copy-Item config.example.yaml config.yaml`.

Edit `config.yaml`, then run one check:

```bash
acmonitor --once
```

Run continuously with `acmonitor`. On Linux, `./install-systemd.sh` installs the included timer.

The checker uses schema.org JSON-LD first, optional CSS selectors second, and common stock phrases last. Retailer markup changes, so verify results and use selectors when necessary. Respect retailer terms and avoid aggressive intervals.

## Configuration

- `interval_minutes`: delay between continuous checks.
- `database_path` and `log_path`: local output paths.
- `request_timeout_seconds`: per-page HTTP timeout.
- `email`: SMTP settings; disabled alerts are printed.
- `products`: product names, target prices, and retailer URLs.

`config.yaml`, databases, and logs are ignored to protect local settings.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m acmonitor --help
```

## License

MIT
