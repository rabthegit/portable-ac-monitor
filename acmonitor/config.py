from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProductUrl:
    retailer: str
    url: str
    availability_selector: str | None = None
    price_selector: str | None = None


@dataclass(frozen=True)
class ProductConfig:
    name: str
    target_price: float | None = None
    urls: list[ProductUrl] = field(default_factory=list)


@dataclass(frozen=True)
class AppConfig:
    interval_minutes: int
    database_path: str
    log_path: str
    user_agent: str
    request_timeout_seconds: int
    email: EmailConfig
    products: list[ProductConfig]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a YAML mapping")
    return value


def _positive_int(value: Any, label: str) -> int:
    result = int(value)
    if result <= 0:
        raise ValueError(f"{label} must be greater than zero")
    return result


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file '{config_path}' was not found. "
            "Copy config.example.yaml to config.yaml and edit it."
        )
    raw = _mapping(yaml.safe_load(config_path.read_text(encoding="utf-8")), "configuration")
    email_raw = _mapping(raw.get("email"), "email")
    product_items = raw.get("products", [])
    if not isinstance(product_items, list):
        raise TypeError("products must be a YAML list")

    products: list[ProductConfig] = []
    for product_index, product_value in enumerate(product_items, start=1):
        item = _mapping(product_value, f"products[{product_index}]")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"products[{product_index}].name is required")
        url_items = item.get("urls", [])
        if not isinstance(url_items, list):
            raise TypeError(f"products[{product_index}].urls must be a YAML list")
        urls: list[ProductUrl] = []
        for url_index, url_value in enumerate(url_items, start=1):
            entry = _mapping(url_value, f"products[{product_index}].urls[{url_index}]")
            url = str(entry.get("url", "")).strip()
            if not url:
                raise ValueError(f"products[{product_index}].urls[{url_index}].url is required")
            urls.append(
                ProductUrl(
                    retailer=str(entry.get("retailer", "Unknown")).strip() or "Unknown",
                    url=url,
                    availability_selector=entry.get("availability_selector"),
                    price_selector=entry.get("price_selector"),
                )
            )
        target = item.get("target_price")
        products.append(
            ProductConfig(
                name=name,
                target_price=None if target is None else float(target),
                urls=urls,
            )
        )

    recipients = email_raw.get("to_addrs", [])
    if not isinstance(recipients, list):
        raise TypeError("email.to_addrs must be a YAML list")
    username = str(email_raw.get("username", ""))
    email = EmailConfig(
        enabled=bool(email_raw.get("enabled", False)),
        smtp_host=str(email_raw.get("smtp_host", "smtp.gmail.com")),
        smtp_port=_positive_int(email_raw.get("smtp_port", 587), "email.smtp_port"),
        username=username,
        password=str(email_raw.get("password", "")),
        from_addr=str(email_raw.get("from_addr", username)),
        to_addrs=[str(address) for address in recipients],
    )
    if email.enabled and (not email.from_addr or not email.to_addrs):
        raise ValueError("enabled email requires email.from_addr and at least one recipient")

    return AppConfig(
        interval_minutes=_positive_int(raw.get("interval_minutes", 30), "interval_minutes"),
        database_path=str(raw.get("database_path", "data/monitor.db")),
        log_path=str(raw.get("log_path", "logs/acmonitor.log")),
        user_agent=str(raw.get("user_agent", "PortableACMonitor/1.0")),
        request_timeout_seconds=_positive_int(
            raw.get("request_timeout_seconds", 20), "request_timeout_seconds"
        ),
        email=email,
        products=products,
    )
