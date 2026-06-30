from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StockResult:
    product_name: str
    retailer: str
    url: str
    available: bool
    price: float | None
    title: str | None
    evidence: str
    checked_at: datetime
    error: str | None = None

    @property
    def price_display(self) -> str:
        return "unknown" if self.price is None else f"£{self.price:.2f}"

