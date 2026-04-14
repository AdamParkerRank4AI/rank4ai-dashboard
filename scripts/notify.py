#!/usr/bin/env python3
"""
Failure notification module.
Sends email alerts when any Rank4AI script fails.
Uses the same Gmail SMTP creds as the intelligence briefing.
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

EMAIL_TO = "adam@muswellrose.com"
EMAIL_FROM = os.environ.get("SMTP_FROM", "adam@muswellrose.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "adam@muswellrose.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")


def send_failure_alert(script_name, errors, log_file=None):
    """
    Send an email alert when a script fails.

    Args:
        script_name: Name of the failed script/task (e.g. "Dashboard Refresh", "Daily Questions")
        errors: List of error strings, or a single error string
        log_file: Optional path to log file for reference
    """
    if not SMTP_PASS:
        print(f"[notify] No SMTP_PASS set — cannot send alert for {script_name}")
        return False

    if isinstance(errors, str):
        errors = [errors]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    error_list = "\n".join(f"  • {e}" for e in errors[:20])

    body = f"""Rank4AI Alert — {script_name} failed

Time: {timestamp}

Errors:
{error_list}
"""
    if log_file:
        body += f"\nFull log: {log_file}\n"

    body += "\n— Rank4AI Monitor"

    msg = MIMEText(body)
    msg["Subject"] = f"⚠ Rank4AI: {script_name} failed"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"[notify] Alert sent for {script_name}")
        return True
    except Exception as e:
        print(f"[notify] Failed to send alert: {e}")
        return False
