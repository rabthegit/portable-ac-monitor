from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_addr: str
    to_addrs: list[str]


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


def load_config(path: str) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    email_raw = raw.get("email", {})

    products = []
    for item in raw.get("products", []):
        urls = []
        for u in item.get("urls", []):
            url = str(u.get("url", "")).strip()
            if not url or "PASTE_PRODUCT_URL_HERE" in url:
                continue
            urls.append(ProductUrl(
                retailer=str(u.get("retailer", "Unknown")),
                url=url,
                availability_selector=u.get("availability_selector"),
                price_selector=u.get("price_selector"),
            ))
        products.append(ProductConfig(
            name=str(item["name"]),
            target_price=item.get("target_price"),
            urls=urls,
        ))

    return AppConfig(
        interval_minutes=int(raw.get("interval_minutes", 30)),
        database_path=str(raw.get("database_path", "data/monitor.db")),
        log_path=str(raw.get("log_path", "logs/acmonitor.log")),
        user_agent=str(raw.get("user_agent", "PortableACMonitor/1.0")),
        request_timeout_seconds=int(raw.get("request_timeout_seconds", 20)),
        email=EmailConfig(
            enabled=bool(email_raw.get("enabled", False)),
            smtp_host=str(email_raw.get("smtp_host", "smtp.gmail.com")),
            smtp_port=int(email_raw.get("smtp_port", 587)),
            username=str(email_raw.get("username", "")),
            password=str(email_raw.get("password", "")),
            from_addr=str(email_raw.get("from_addr", email_raw.get("username", ""))),
            to_addrs=list(email_raw.get("to_addrs", [])),
        ),
        products=products,
    )
