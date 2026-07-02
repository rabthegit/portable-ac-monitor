from pathlib import Path

import pytest

from acmonitor.config import load_config


def test_load_config(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
interval_minutes: 15
request_timeout_seconds: 10
email:
  enabled: false
products:
  - name: Test Product
    target_price: 100
    urls:
      - retailer: Test Shop
        url: https://example.com/product
""",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.interval_minutes == 15
    assert config.request_timeout_seconds == 10
    assert config.products[0].target_price == 100
    assert config.products[0].urls[0].retailer == "Test Shop"


def test_missing_config_has_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="config.example.yaml"):
        load_config(tmp_path / "missing.yaml")


def test_interval_must_be_positive(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("interval_minutes: 0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="interval_minutes"):
        load_config(path)
