from __future__ import annotations
import sqlite3
from pathlib import Path
from .models import StockResult

class Database:
    def __init__(self, path: str):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_state (
                    product_name TEXT NOT NULL,
                    retailer TEXT NOT NULL,
                    url TEXT NOT NULL,
                    available INTEGER NOT NULL,
                    price REAL,
                    title TEXT,
                    evidence TEXT,
                    error TEXT,
                    checked_at TEXT NOT NULL,
                    last_alert_at TEXT,
                    PRIMARY KEY (product_name, retailer, url)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    retailer TEXT NOT NULL,
                    url TEXT NOT NULL,
                    available INTEGER NOT NULL,
                    price REAL,
                    title TEXT,
                    evidence TEXT,
                    error TEXT,
                    checked_at TEXT NOT NULL
                )
            """)

    def previous_state(self, result: StockResult):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM stock_state WHERE product_name=? AND retailer=? AND url=?",
                (result.product_name, result.retailer, result.url),
            ).fetchone()

    def save_result(self, result: StockResult) -> None:
        checked = result.checked_at.isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_history
                (product_name, retailer, url, available, price, title, evidence, error, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (result.product_name, result.retailer, result.url, int(result.available),
                 result.price, result.title, result.evidence, result.error, checked),
            )
            conn.execute(
                """
                INSERT INTO stock_state
                (product_name, retailer, url, available, price, title, evidence, error, checked_at, last_alert_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(product_name, retailer, url)
                DO UPDATE SET available=excluded.available, price=excluded.price,
                title=excluded.title, evidence=excluded.evidence, error=excluded.error,
                checked_at=excluded.checked_at
                """,
                (result.product_name, result.retailer, result.url, int(result.available),
                 result.price, result.title, result.evidence, result.error, checked),
            )

    def mark_alert_sent(self, result: StockResult) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE stock_state SET last_alert_at=? WHERE product_name=? AND retailer=? AND url=?",
                (result.checked_at.isoformat(timespec="seconds"), result.product_name, result.retailer, result.url),
            )

