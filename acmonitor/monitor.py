from __future__ import annotations
import html, logging
from .config import AppConfig
from .database import Database
from .emailer import Emailer
from .models import StockResult
from .retailers.generic import check_product_url

logger = logging.getLogger("acmonitor.monitor")

class Monitor:
    def __init__(self, cfg: AppConfig, db: Database, emailer: Emailer):
        self.cfg = cfg
        self.db = db
        self.emailer = emailer

    def run_once(self) -> None:
        logger.info("Starting monitoring cycle")
        checks = 0
        for product in self.cfg.products:
            if not product.urls:
                logger.info("Skipping %s: no configured URLs", product.name)
                continue
            for product_url in product.urls:
                checks += 1


result = check_product_url(
    product,
    product_url,
    user_agent=self.config.user_agent,
    timeout_seconds=self.config.request_timeout_seconds,
)


#result = check_product_url(product, product_url, user_agent=self.cfg.user_agent, timeout_seconds=self.cfg.request_timeout_seconds)

                self._handle_result(result, product.target_price)
        logger.info("Finished monitoring cycle: %s checks", checks)

    def _handle_result(self, result: StockResult, target_price: float | None) -> None:
        previous = self.db.previous_state(result)
        was_available = bool(previous["available"]) if previous else False
        self.db.save_result(result)

        logger.info("%s at %s: available=%s price=%s evidence=%s error=%s",
                    result.product_name, result.retailer, result.available, result.price_display, result.evidence, result.error)

        if not result.available:
            return
        if target_price is not None and result.price is not None and result.price > target_price:
            logger.info("Available but above target price: %s > %s", result.price, target_price)
            return
        if was_available:
            return

        self._send_stock_alert(result, target_price)
        self.db.mark_alert_sent(result)

    def _send_stock_alert(self, result: StockResult, target_price: float | None) -> None:
        subject = f"Portable AC in stock: {result.product_name}"
        target_line = f"Target price: £{target_price:.2f}" if target_price is not None else "Target price: none"
        text = (
            f"{result.product_name} is now in stock.\n\n"
            f"Retailer: {result.retailer}\n"
            f"Price: {result.price_display}\n"
            f"{target_line}\n"
            f"Evidence: {result.evidence}\n"
            f"Link: {result.url}\n"
            f"Checked at: {result.checked_at.isoformat(timespec='seconds')}\n"
        )
        html_body = f"""
        <html><body>
        <h2>Portable AC now in stock</h2>
        <p><strong>{html.escape(result.product_name)}</strong></p>
        <table>
        <tr><td><strong>Retailer</strong></td><td>{html.escape(result.retailer)}</td></tr>
        <tr><td><strong>Price</strong></td><td>{html.escape(result.price_display)}</td></tr>
        <tr><td><strong>Target</strong></td><td>{html.escape(target_line)}</td></tr>
        <tr><td><strong>Evidence</strong></td><td>{html.escape(result.evidence)}</td></tr>
        </table>
        <p><a href="{html.escape(result.url)}">Open product page</a></p>
        </body></html>
        """
        self.emailer.send(subject, text, html_body)

