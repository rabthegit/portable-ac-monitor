from __future__ import annotations

import argparse
import logging
import sys
import time

from .config import load_config
from .database import Database
from .emailer import Emailer
from .logging_setup import setup_logging
from .monitor import Monitor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable AC stock monitor")
    parser.add_argument("--config", default="config.yaml", help="path to the YAML configuration")
    parser.add_argument("--once", action="store_true", help="run one monitoring cycle")
    parser.add_argument("--test-email", action="store_true", help="send a test alert and exit")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except (OSError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    setup_logging(config.log_path)
    logger = logging.getLogger("acmonitor")
    database = Database(config.database_path)
    database.init()
    emailer = Emailer(config.email)

    if args.test_email:
        emailer.send(
            "Portable AC Monitor test",
            "This is a test email from your Portable AC Monitor.",
            "<p>This is a test email from your <strong>Portable AC Monitor</strong>.</p>",
        )
        return 0

    monitor = Monitor(config, database, emailer)
    if args.once:
        monitor.run_once()
        return 0

    logger.info("Starting continuous monitor")
    try:
        while True:
            try:
                monitor.run_once()
            except Exception:
                logger.exception("Monitoring cycle failed")
            time.sleep(config.interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Monitor stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
