from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from .config import EmailConfig

logger = logging.getLogger("acmonitor.emailer")


class Emailer:
    def __init__(self, config: EmailConfig):
        self.config = config

    def send(
        self,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> None:
        """
        Send an email.

        If email is disabled in config.yaml, the message is logged
        instead of being sent.
        """

        if not self.config.enabled:
            logger.info(
                "Email disabled - would have sent '%s'",
                subject,
            )
            print(f"[EMAIL DISABLED]\nSubject: {subject}\n\n{text}")
            return

        if not self.config.to_addrs:
            raise ValueError("No recipients configured.")

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = self.config.from_addr
        message["To"] = ", ".join(self.config.to_addrs)

        message.set_content(text)

        if html:
            message.add_alternative(html, subtype="html")

        logger.info(
            "Connecting to SMTP server %s:%s",
            self.config.smtp_host,
            self.config.smtp_port,
        )

        with smtplib.SMTP(
            self.config.smtp_host,
            self.config.smtp_port,
            timeout=30,
        ) as smtp:

            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            if self.config.username:
                smtp.login(
                    self.config.username,
                    self.config.password,
                )

            smtp.send_message(message)

        logger.info("Email sent successfully.")

