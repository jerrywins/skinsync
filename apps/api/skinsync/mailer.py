"""Outgoing mail. SMTP when SKINSYNC_SMTP_HOST is set (Mailpit in dev); otherwise an
in-memory outbox used by tests. Mail bodies never go to logs."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

OUTBOX: list[EmailMessage] = []


def send(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = os.environ.get("SKINSYNC_MAIL_FROM", "SkinSync <no-reply@skinsync.local>")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    host = os.environ.get("SKINSYNC_SMTP_HOST")
    if not host:
        OUTBOX.append(msg)
        return
    with smtplib.SMTP(host, int(os.environ.get("SKINSYNC_SMTP_PORT", "1025")), timeout=10) as s:
        s.send_message(msg)
