from __future__ import annotations
import argparse, logging, sys, time
from .config import load_config
from .database import Database
from .emailer import Emailer
from .logging_setup import setup_logging
from .monitor import Monitor

def main() -> int:
    parser = argparse.ArgumentParser(description="Portable AC stock monitor")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--test-email", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.log_path)
    logger = logging.getLogger("acmonitor")

    db = Database(cfg.database_path)
    db.init()
    emailer = Emailer(cfg.email)

    if args.test_email:
        emailer.send(
            "Portable AC Monitor test",
            "This is a test email from your Portable AC Monitor.",
            "<p>This is a test email from your <strong>Portable AC Monitor</strong>.</p>",
        )
        print("Test email sent.")
        return 0

    monitor = Monitor(cfg, db, emailer)
    if args.once:
        monitor.run_once()
        return 0

    logger.info("Starting continuous monitor")
    while True:
        try:
            monitor.run_once()
        except Exception:
            logger.exception("Monitoring cycle failed")
        time.sleep(cfg.interval_minutes * 60)

if __name__ == "__main__":
    sys.exit(main())

