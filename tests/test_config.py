from pathlib import Path

from acmonitor.config import load_config


def test_load_config(tmp_path: Path):
    config = tmp_path / "config.yaml"

    config.write_text(
        """
interval_minutes: 15

database_path: data/test.db
log_path: logs/test.log

user_agent: TestAgent
request_timeout_seconds: 10

email:
  enabled: false

products:
  - name: Test Product
    target_price: 100

    urls:
      - retailer: Test Shop
        url: https://example.com/product
"""
    )

    cfg = load_config(str(config))

    assert cfg.interval_minutes == 15
    assert cfg.request_timeout_seconds == 10
    assert len(cfg.products) == 1

    product = cfg.products[0]

    assert product.name == "Test Product"
    assert product.target_price == 100
    assert product.urls[0].retailer == "Test Shop"
