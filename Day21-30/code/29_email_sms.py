"""
Day 29 - Python Email and SMS Sending
======================================

Comprehensive coverage of sending emails via smtplib and the email module,
including plain text, HTML, attachments, and MIME types. Also covers SMS
sending via third-party gateways with the requests library.

Topics:
    - smtplib: SMTP_SSL connection, login, sendmail
    - email module: MIMEMultipart, MIMEText, MIMEBase, MIMEImage
    - MIME types: text/plain, text/html, application/octet-stream, image/*
    - HTML email with inline images
    - File attachments with BASE64 encoding
    - SMS sending via HTTP gateway (requests)
    - Bulk email, report emailer, notification system, alert system

C++ Comparison:
    Python smtplib vs C++ libcurl for SMTP
    ---------------------------------------
    Python's smtplib provides a high-level, batteries-included API for SMTP
    communication. With just a few lines, you can connect to a server, log in,
    and send emails with attachments. The email module handles MIME encoding,
    headers, and multipart messages automatically.

    In C++, you would typically use libcurl (specifically the CURLOPT_* options
    for SMTP). This requires:
        - Manual socket/TLS setup via CURLOPT_USE_SSL
        - Manual MIME part construction via curl_mime_* API
        - Manual base64 encoding for attachments
        - Manual header formatting
        - Explicit memory management for all buffers

    Python advantage: ~10 lines vs ~80+ lines in C++ for equivalent functionality.
    C++ advantage: finer control over connection pooling, async I/O, and
    performance-critical bulk sending scenarios.

    Example C++ libcurl SMTP (skeleton):
        CURL *curl = curl_easy_init();
        curl_easy_setopt(curl, CURLOPT_URL, "smtps://smtp.example.com:465");
        curl_easy_setopt(curl, CURLOPT_USERNAME, "user@example.com");
        curl_easy_setopt(curl, CURLOPT_PASSWORD, "auth_code");
        curl_easy_setopt(curl, CURLOPT_MAIL_FROM, "<user@example.com>");
        struct curl_slist *recipients = curl_slist_append(NULL, "<to@example.com>");
        curl_easy_setopt(curl, CURLOPT_MAIL_RCPT, recipients);
        // ... read callback for message body ...
        curl_easy_perform(curl);
        curl_slist_free_all(recipients);
        curl_easy_cleanup(curl);

    Python equivalent is just: SMTP_SSL -> login -> sendmail -> quit.

Standard library references:
    - smtplib: https://docs.python.org/3/library/smtplib.html
    - email:   https://docs.python.org/3/library/email.html
    - base64:  https://docs.python.org/3/library/base64.html

Author: Python-100-Days Course
"""

import os
import re
import ssl
import json
import time
import smtplib
import logging
import mimetypes
from typing import Optional
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email import encoders
from urllib.parse import quote
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =========================================================================
# Section 1: SMTP Configuration
# =========================================================================

@dataclass
class SMTPConfig:
    """Immutable SMTP server configuration.

    Attributes:
        host:      SMTP server hostname (e.g. 'smtp.126.com').
        port:      SMTP port, typically 465 for SSL or 587 for STARTTLS.
        username:  Login username / email address.
        password:  Authorization code (NOT the account password).
        use_ssl:   Whether to use implicit SSL (SMTP_SSL).
        timeout:   Socket timeout in seconds.
    """
    host: str = "smtp.126.com"
    port: int = 465
    username: str = ""
    password: str = ""
    use_ssl: bool = True
    timeout: int = 30


# =========================================================================
# Section 2: Core Email Sender
# =========================================================================

class EmailSender:
    """High-level email sender supporting plain text, HTML, inline images,
    and file attachments.

    Usage:
        config = SMTPConfig(
            host="smtp.126.com", port=465,
            username="you@126.com", password="your_auth_code"
        )
        sender = EmailSender(config)
        sender.send(
            to=["friend@example.com"],
            subject="Hello",
            body="<h1>Hi!</h1>",
            content_type="html",
            attachments=["report.pdf"],
        )
    """

    def __init__(self, config: SMTPConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def send(
        self,
        to: list[str],
        subject: str,
        body: str,
        content_type: str = "plain",
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        attachments: Optional[list[str]] = None,
        inline_images: Optional[dict[str, str]] = None,
        reply_to: Optional[str] = None,
    ) -> dict[str, object]:
        """Send an email message.

        Args:
            to:             List of recipient email addresses.
            subject:        Email subject line.
            body:           Email body content (plain text or HTML).
            content_type:   'plain' or 'html'.
            cc:             Carbon-copy recipients.
            bcc:            Blind carbon-copy recipients.
            attachments:    List of file paths to attach.
            inline_images:  Dict mapping CID -> file path for inline images.
                            Use <img src="cid:myimage"> in HTML body.
            reply_to:       Optional Reply-To header address.

        Returns:
            Dict with 'success' (bool), 'message' (str), and 'recipients' (list).
        """
        msg = self._build_message(
            to=to,
            subject=subject,
            body=body,
            content_type=content_type,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            inline_images=inline_images,
            reply_to=reply_to,
        )

        all_recipients = list(to)
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        return self._send_message(msg, all_recipients)

    # ------------------------------------------------------------------ #
    # Message construction helpers
    # ------------------------------------------------------------------ #

    def _build_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        content_type: str,
        cc: Optional[list[str]],
        bcc: Optional[list[str]],
        attachments: Optional[list[str]],
        inline_images: Optional[dict[str, str]],
        reply_to: Optional[str],
    ) -> MIMEMultipart:
        """Construct a MIMEMultipart email message."""
        has_attachments = bool(attachments)
        has_inline = bool(inline_images)

        if has_attachments or has_inline:
            msg: MIMEMultipart = MIMEMultipart("mixed")
        else:
            msg = MIMEMultipart()

        # -- Headers --
        msg["From"] = self._config.username
        msg["To"] = "; ".join(to)
        if cc:
            msg["Cc"] = "; ".join(cc)
        msg["Subject"] = Header(subject, "utf-8")
        if reply_to:
            msg["Reply-To"] = reply_to

        # -- Body --
        if has_inline:
            # Build a related part for inline images
            related = MIMEMultipart("related")
            html_part = MIMEText(body, "html", "utf-8")
            related.attach(html_part)
            for cid, img_path in inline_images.items():  # type: ignore[arg-type]
                related.attach(self._make_inline_image(cid, img_path))
            msg.attach(related)
        else:
            msg.attach(MIMEText(body, content_type, "utf-8"))

        # -- Attachments --
        if attachments:
            for filepath in attachments:
                msg.attach(self._make_attachment(filepath))

        return msg

    @staticmethod
    def _make_attachment(filepath: str) -> MIMEBase:
        """Create a MIME attachment from a file path.

        The MIME type is guessed from the file extension.  Falls back to
        application/octet-stream when the type cannot be determined.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {filepath}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = mime_type.split("/", 1)

        with open(path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())

        encoders.encode_base64(part)

        # RFC 2231 encoding for non-ASCII filenames
        filename = quote(path.name)
        part.add_header(
            "Content-Disposition", "attachment", filename=("utf-8", "", filename)
        )
        return part

    @staticmethod
    def _make_inline_image(cid: str, filepath: str) -> MIMEImage:
        """Create an inline image part with a Content-ID header."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Inline image not found: {filepath}")

        mime_type, _ = mimetypes.guess_type(str(path))
        with open(path, "rb") as f:
            img = MIMEImage(f.read(), _subtype=mime_type.split("/")[-1] if mime_type else "png")

        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=("utf-8", "", quote(path.name)))
        return img

    def _send_message(self, msg: MIMEMultipart, recipients: list[str]) -> dict[str, object]:
        """Connect to the SMTP server and send the message."""
        result: dict[str, object] = {"success": False, "message": "", "recipients": recipients}
        smtp_obj: Optional[smtplib.SMTP | smtplib.SMTP_SSL] = None

        try:
            if self._config.use_ssl:
                context = ssl.create_default_context()
                smtp_obj = smtplib.SMTP_SSL(
                    self._config.host, self._config.port, timeout=self._config.timeout, context=context
                )
            else:
                smtp_obj = smtplib.SMTP(self._config.host, self._config.port, timeout=self._config.timeout)
                smtp_obj.starttls()

            smtp_obj.login(self._config.username, self._config.password)
            smtp_obj.sendmail(self._config.username, recipients, msg.as_string())

            result["success"] = True
            result["message"] = "Email sent successfully."
            logger.info("Email sent to %s", ", ".join(recipients))

        except smtplib.SMTPAuthenticationError as exc:
            result["message"] = f"Authentication failed: {exc}"
            logger.error("SMTP auth error: %s", exc)
        except smtplib.SMTPException as exc:
            result["message"] = f"SMTP error: {exc}"
            logger.error("SMTP error: %s", exc)
        except OSError as exc:
            result["message"] = f"Network error: {exc}"
            logger.error("Network error: %s", exc)
        finally:
            if smtp_obj is not None:
                try:
                    smtp_obj.quit()
                except Exception:
                    pass

        return result


# =========================================================================
# Section 3: Bulk Email Sender (Enterprise Example)
# =========================================================================

@dataclass
class BulkEmailResult:
    """Result of a bulk email send operation."""
    total: int = 0
    sent: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class BulkEmailSender:
    """Send emails to a large list of recipients with rate limiting and
    error handling.

    Enterprise use case: marketing campaigns, newsletters, announcements.

    Usage:
        config = SMTPConfig(username="marketing@company.com", password="...")
        bulk = BulkEmailSender(config, rate_limit=50)
        results = bulk.send_campaign(
            recipients=["user1@example.com", "user2@example.com"],
            subject="Summer Sale!",
            template="<h1>Hi {name}!</h1><p>Check out our deals.</p>",
            substitutions={"user1@example.com": {"name": "Alice"}},
        )
    """

    def __init__(self, config: SMTPConfig, rate_limit: int = 100) -> None:
        """
        Args:
            config:     SMTP configuration.
            rate_limit: Maximum emails per batch before pausing.
        """
        self._sender = EmailSender(config)
        self._rate_limit = rate_limit

    def send_campaign(
        self,
        recipients: list[str],
        subject: str,
        template: str,
        content_type: str = "html",
        substitutions: Optional[dict[str, dict[str, str]]] = None,
        attachments: Optional[list[str]] = None,
    ) -> BulkEmailResult:
        """Send a templated email to multiple recipients.

        Args:
            recipients:     List of email addresses.
            subject:        Subject line (may contain {placeholders}).
            template:       Body template with {placeholder} tokens.
            content_type:   'plain' or 'html'.
            substitutions:  Per-recipient replacement dict.
            attachments:    File paths to attach to every email.

        Returns:
            BulkEmailResult with success/failure counts.
        """
        result = BulkEmailResult(total=len(recipients))
        substitutions = substitutions or {}

        for idx, recipient in enumerate(recipients, 1):
            # Apply per-recipient substitutions
            subs = substitutions.get(recipient, {})
            personalized_body = template
            personalized_subject = subject
            for key, value in subs.items():
                personalized_body = personalized_body.replace(f"{{{key}}}", value)
                personalized_subject = personalized_subject.replace(f"{{{key}}}", value)

            send_result = self._sender.send(
                to=[recipient],
                subject=personalized_subject,
                body=personalized_body,
                content_type=content_type,
                attachments=attachments,
            )

            if send_result["success"]:
                result.sent += 1
                logger.info("[%d/%d] Sent to %s", idx, result.total, recipient)
            else:
                result.failed += 1
                error_msg = f"{recipient}: {send_result['message']}"
                result.errors.append(error_msg)
                logger.warning("[%d/%d] Failed for %s: %s", idx, result.total, recipient, send_result["message"])

            # Rate limiting: pause between batches
            if idx % self._rate_limit == 0 and idx < result.total:
                logger.info("Rate limit reached (%d), sleeping 1 second...", self._rate_limit)
                time.sleep(1)

        return result


# =========================================================================
# Section 4: Report Emailer (Enterprise Example)
# =========================================================================

class ReportEmailer:
    """Generate and send formatted reports via email.

    Enterprise use case: daily/weekly automated reports, KPI dashboards,
    data exports sent to stakeholders.

    Usage:
        emailer = ReportEmailer(config)
        emailer.send_report(
            to=["manager@company.com"],
            report_title="Weekly Sales Report",
            metrics={"Revenue": "$125,000", "New Customers": "42"},
            attachments=["sales_report.xlsx"],
        )
    """

    def __init__(self, config: SMTPConfig) -> None:
        self._sender = EmailSender(config)

    def send_report(
        self,
        to: list[str],
        report_title: str,
        metrics: dict[str, str],
        summary: str = "",
        attachments: Optional[list[str]] = None,
        cc: Optional[list[str]] = None,
    ) -> dict[str, object]:
        """Send a formatted report email.

        Args:
            to:          Recipients.
            report_title: Report title (used as email subject).
            metrics:     Key-value pairs to display as a metrics table.
            summary:     Optional narrative summary paragraph.
            attachments: Report files (Excel, PDF, CSV, etc.).
            cc:          CC recipients.

        Returns:
            Result dict from EmailSender.send().
        """
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        html = self._build_report_html(report_title, report_date, metrics, summary)

        subject = f"[Report] {report_title} - {report_date}"
        return self._sender.send(
            to=to,
            subject=subject,
            body=html,
            content_type="html",
            cc=cc,
            attachments=attachments,
        )

    @staticmethod
    def _build_report_html(
        title: str, date: str, metrics: dict[str, str], summary: str
    ) -> str:
        """Build a clean HTML report from metrics data."""
        rows = ""
        for key, value in metrics.items():
            rows += f"""
            <tr>
                <td style="padding:8px 16px;border:1px solid #ddd;font-weight:bold;background:#f9f9f9;">{key}</td>
                <td style="padding:8px 16px;border:1px solid #ddd;">{value}</td>
            </tr>"""

        summary_section = ""
        if summary:
            summary_section = f"""
            <div style="margin-top:20px;padding:12px;background:#f0f7ff;border-left:4px solid #2196F3;">
                <strong>Summary:</strong> {summary}
            </div>"""

        return f"""
        <html>
        <body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px;">
            <h2 style="color:#333;border-bottom:2px solid #2196F3;padding-bottom:10px;">{title}</h2>
            <p style="color:#666;">Generated: {date}</p>
            <table style="border-collapse:collapse;width:100%;margin-top:16px;">
                <thead>
                    <tr style="background:#2196F3;color:white;">
                        <th style="padding:10px 16px;border:1px solid #ddd;text-align:left;">Metric</th>
                        <th style="padding:10px 16px;border:1px solid #ddd;text-align:left;">Value</th>
                    </tr>
                </thead>
                <tbody>{rows}
                </tbody>
            </table>
            {summary_section}
            <hr style="margin-top:30px;border:none;border-top:1px solid #eee;">
            <p style="color:#999;font-size:12px;">This is an automated report. Do not reply.</p>
        </body>
        </html>"""


# =========================================================================
# Section 5: Notification System (Enterprise Example)
# =========================================================================

@dataclass
class Notification:
    """Represents a single notification to be sent."""
    recipient: str
    title: str
    message: str
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class NotificationSystem:
    """Enterprise notification system supporting email delivery with
    priority levels and HTML formatting.

    Usage:
        system = NotificationSystem(config)
        system.notify(
            recipient="dev@company.com",
            title="Deployment Complete",
            message="v2.3.1 deployed to production successfully.",
            priority="high",
        )
        system.notify_batch([...])
    """

    PRIORITY_COLORS: dict[str, str] = {
        "low": "#4CAF50",
        "normal": "#2196F3",
        "high": "#FF9800",
        "urgent": "#F44336",
    }

    def __init__(self, config: SMTPConfig) -> None:
        self._sender = EmailSender(config)
        self._history: list[Notification] = []

    def notify(
        self,
        recipient: str,
        title: str,
        message: str,
        priority: str = "normal",
        attachments: Optional[list[str]] = None,
    ) -> dict[str, object]:
        """Send a single notification.

        Args:
            recipient:   Email address.
            title:       Notification title.
            message:     Notification body text.
            priority:    'low', 'normal', 'high', or 'urgent'.
            attachments: Optional file attachments.

        Returns:
            Result dict from EmailSender.send().
        """
        notification = Notification(
            recipient=recipient, title=title, message=message, priority=priority
        )
        self._history.append(notification)

        color = self.PRIORITY_COLORS.get(priority, "#2196F3")
        html = self._build_notification_html(title, message, priority, color, notification.timestamp)  # type: ignore[arg-type]

        subject_prefix = "[URGENT] " if priority == "urgent" else ""
        subject_prefix = "[HIGH] " if priority == "high" else subject_prefix

        return self._sender.send(
            to=[recipient],
            subject=f"{subject_prefix}{title}",
            body=html,
            content_type="html",
            attachments=attachments,
        )

    def notify_batch(self, notifications: list[dict[str, str]]) -> list[dict[str, object]]:
        """Send multiple notifications.

        Args:
            notifications: List of dicts with keys 'recipient', 'title',
                           'message', and optionally 'priority'.

        Returns:
            List of result dicts.
        """
        results: list[dict[str, object]] = []
        for notif in notifications:
            result = self.notify(
                recipient=notif["recipient"],
                title=notif["title"],
                message=notif["message"],
                priority=notif.get("priority", "normal"),
            )
            results.append(result)
        return results

    def get_history(self) -> list[Notification]:
        """Return the list of sent notifications."""
        return list(self._history)

    @staticmethod
    def _build_notification_html(
        title: str, message: str, priority: str, color: str, timestamp: str
    ) -> str:
        return f"""
        <html>
        <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <div style="border-left:4px solid {color};padding:16px;background:#fafafa;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h3 style="margin:0;color:#333;">{title}</h3>
                    <span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;text-transform:uppercase;">
                        {priority}
                    </span>
                </div>
                <p style="color:#555;margin-top:12px;line-height:1.6;">{message}</p>
                <p style="color:#999;font-size:11px;margin-top:16px;">{timestamp}</p>
            </div>
        </body>
        </html>"""


# =========================================================================
# Section 6: Alert System (Enterprise Example)
# =========================================================================

@dataclass
class AlertRule:
    """Defines when and how an alert should fire."""
    name: str
    condition: str  # Human-readable condition description
    recipients: list[str] = field(default_factory=list)
    cooldown_seconds: int = 300  # Minimum seconds between alerts of same type
    last_fired: float = 0.0


class AlertSystem:
    """Monitoring alert system that sends email notifications when system
    metrics exceed defined thresholds.

    Enterprise use case: server monitoring, application health checks,
    SLA breach notifications.

    Usage:
        alert_sys = AlertSystem(config)
        alert_sys.add_rule(AlertRule(
            name="HighCPU",
            condition="CPU > 90%",
            recipients=["ops@company.com"],
            cooldown_seconds=600,
        ))
        alert_sys.check_and_alert("HighCPU", current_value=95.3, threshold=90)
    """

    def __init__(self, config: SMTPConfig) -> None:
        self._notification = NotificationSystem(config)
        self._rules: dict[str, AlertRule] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule."""
        self._rules[rule.name] = rule
        logger.info("Alert rule registered: %s", rule.name)

    def check_and_alert(
        self,
        rule_name: str,
        current_value: float,
        threshold: float,
        details: str = "",
    ) -> Optional[dict[str, object]]:
        """Check a metric against a threshold and fire an alert if exceeded.

        Args:
            rule_name:     Name of a previously registered AlertRule.
            current_value: The current metric value.
            threshold:     The threshold that triggers the alert.
            details:       Additional context for the alert message.

        Returns:
            Result dict if alert was fired, None if suppressed or unknown rule.
        """
        rule = self._rules.get(rule_name)
        if rule is None:
            logger.warning("Unknown alert rule: %s", rule_name)
            return None

        if current_value <= threshold:
            return None

        # Cooldown check
        now = time.time()
        if (now - rule.last_fired) < rule.cooldown_seconds:
            logger.info("Alert '%s' suppressed (cooldown).", rule_name)
            return None

        rule.last_fired = now

        message = (
            f"Alert: {rule.name}\n"
            f"Condition: {rule.condition}\n"
            f"Current Value: {current_value}\n"
            f"Threshold: {threshold}\n"
        )
        if details:
            message += f"Details: {details}\n"

        # Send to all rule recipients
        last_result: Optional[dict[str, object]] = None
        for recipient in rule.recipients:
            last_result = self._notification.notify(
                recipient=recipient,
                title=f"[ALERT] {rule.name} - Threshold Exceeded",
                message=message.replace("\n", "<br>"),
                priority="urgent",
            )

        return last_result

    def get_rules(self) -> dict[str, AlertRule]:
        """Return all registered alert rules."""
        return dict(self._rules)


# =========================================================================
# Section 7: SMS Sending
# =========================================================================

class SMSSender:
    """Send SMS messages via third-party HTTP gateway.

    This is a generic SMS sender using the requests library.  Adapt the
    URL, authentication, and payload format to match your SMS provider
    (e.g., Luosimao, Twilio, Alibaba Cloud SMS, etc.).

    Usage:
        sms = SMSSender(api_url="http://sms-api.luosimao.com/v1/send.json",
                        api_key="your-api-key")
        result = sms.send("13800138000", "Your code is 123456")
    """

    def __init__(self, api_url: str, api_key: str, timeout: int = 10) -> None:
        self._api_url = api_url
        self._api_key = api_key
        self._timeout = timeout

    def send(self, mobile: str, message: str) -> dict[str, object]:
        """Send an SMS message.

        Args:
            mobile:  Recipient phone number.
            message: SMS text content (include platform-required signature).

        Returns:
            Response dict from the SMS gateway.
        """
        try:
            import requests  # optional dependency
        except ImportError:
            return {"error": -1, "msg": "requests library not installed"}

        try:
            resp = requests.post(
                url=self._api_url,
                auth=("api", self._api_key),
                data={"mobile": mobile, "message": message},
                timeout=self._timeout,
                verify=False,
            )
            return resp.json()
        except requests.RequestException as exc:
            return {"error": -1, "msg": str(exc)}

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate a random numeric verification code."""
        import random
        return "".join(random.choices("0123456789", k=length))


# =========================================================================
# Section 8: Utility Functions (Legacy / Quick-Use Wrappers)
# =========================================================================

def send_simple_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    to: list[str],
    subject: str,
    body: str,
    content_type: str = "plain",
) -> bool:
    """Send a simple email (no attachments).  Quick helper function.

    Returns True on success, False on failure.
    """
    config = SMTPConfig(host=smtp_host, port=smtp_port, username=username, password=password)
    sender = EmailSender(config)
    result = sender.send(to=to, subject=subject, body=body, content_type=content_type)
    return result["success"]  # type: ignore[return-value]


def send_email_with_attachments(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    to: list[str],
    subject: str,
    body: str,
    attachments: list[str],
    content_type: str = "html",
) -> bool:
    """Send an email with file attachments.  Quick helper function.

    Returns True on success, False on failure.
    """
    config = SMTPConfig(host=smtp_host, port=smtp_port, username=username, password=password)
    sender = EmailSender(config)
    result = sender.send(
        to=to, subject=subject, body=body,
        content_type=content_type, attachments=attachments,
    )
    return result["success"]  # type: ignore[return-value]


# =========================================================================
# Section 9: Demonstration / __main__
# =========================================================================

def _demo_smtp_config() -> SMTPConfig:
    """Create a demo SMTP config (replace with real credentials)."""
    return SMTPConfig(
        host=os.environ.get("SMTP_HOST", "smtp.126.com"),
        port=int(os.environ.get("SMTP_PORT", "465")),
        username=os.environ.get("SMTP_USER", "demo@126.com"),
        password=os.environ.get("SMTP_AUTH", "your_auth_code"),
    )


def _demo_plain_email() -> None:
    """Demonstrate sending a plain text email."""
    print("\n--- Demo: Plain Text Email ---")
    config = _demo_smtp_config()
    sender = EmailSender(config)
    result = sender.send(
        to=["recipient@example.com"],
        subject="Plain Text Test",
        body="This is a plain text email sent from Python using smtplib.",
    )
    print(f"Result: {result}")


def _demo_html_email() -> None:
    """Demonstrate sending an HTML email."""
    print("\n--- Demo: HTML Email ---")
    config = _demo_smtp_config()
    sender = EmailSender(config)
    html_body = """
    <html>
    <body>
        <h1 style="color:#2196F3;">Hello from Python!</h1>
        <p>This is an <strong>HTML email</strong> with formatting.</p>
        <table border="1" cellpadding="8" cellspacing="0">
            <tr><th>Language</th><th>SMTP Module</th></tr>
            <tr><td>Python</td><td>smtplib</td></tr>
            <tr><td>C++</td><td>libcurl</td></tr>
        </table>
    </body>
    </html>
    """
    result = sender.send(
        to=["recipient@example.com"],
        subject="HTML Email Test",
        body=html_body,
        content_type="html",
    )
    print(f"Result: {result}")


def _demo_report_emailer() -> None:
    """Demonstrate the report emailer."""
    print("\n--- Demo: Report Emailer ---")
    config = _demo_smtp_config()
    emailer = ReportEmailer(config)
    result = emailer.send_report(
        to=["manager@example.com"],
        report_title="Daily Operations Report",
        metrics={
            "Total Orders": "1,247",
            "Revenue": "$52,380.00",
            "Avg Response Time": "120ms",
            "Error Rate": "0.3%",
            "Active Users": "8,921",
        },
        summary="All metrics within normal range. No incidents reported.",
    )
    print(f"Result: {result}")


def _demo_notification_system() -> None:
    """Demonstrate the notification system."""
    print("\n--- Demo: Notification System ---")
    config = _demo_smtp_config()
    system = NotificationSystem(config)
    result = system.notify(
        recipient="devops@example.com",
        title="Database Migration Complete",
        message="Schema v4.2 migration completed in 12.3 seconds. All tables verified.",
        priority="high",
    )
    print(f"Result: {result}")
    print(f"Notification history: {len(system.get_history())} item(s)")


def _demo_alert_system() -> None:
    """Demonstrate the alert system."""
    print("\n--- Demo: Alert System ---")
    config = _demo_smtp_config()
    alert_sys = AlertSystem(config)

    alert_sys.add_rule(AlertRule(
        name="HighCPU",
        condition="CPU usage > 90%",
        recipients=["ops@example.com"],
        cooldown_seconds=600,
    ))

    # Simulate a high CPU reading
    result = alert_sys.check_and_alert(
        rule_name="HighCPU",
        current_value=95.3,
        threshold=90.0,
        details="Server web-prod-01, sustained for 3 minutes.",
    )
    if result:
        print(f"Alert fired: {result}")
    else:
        print("No alert triggered.")


def _demo_sms() -> None:
    """Demonstrate SMS sending."""
    print("\n--- Demo: SMS Sending ---")
    sms = SMSSender(
        api_url="http://sms-api.luosimao.com/v1/send.json",
        api_key="your-api-key",
    )
    code = sms.generate_code()
    message = f"Your verification code is {code}. Do not share it. [PythonCourse]"
    print(f"Generated code: {code}")
    print(f"SMS message: {message}")
    # Uncomment to actually send:
    # result = sms.send("13800138000", message)
    # print(f"SMS result: {result}")


def _demo_bulk_email() -> None:
    """Demonstrate bulk email sending."""
    print("\n--- Demo: Bulk Email Sender ---")
    config = _demo_smtp_config()
    bulk = BulkEmailSender(config, rate_limit=50)

    recipients = [f"user{i}@example.com" for i in range(1, 6)]
    substitutions = {
        f"user{i}@example.com": {"name": f"User {i}"} for i in range(1, 6)
    }

    print(f"Would send to {len(recipients)} recipients with personalized templates.")
    # Uncomment to actually send:
    # result = bulk.send_campaign(
    #     recipients=recipients,
    #     subject="Hello {name}!",
    #     template="<h1>Hi {name}!</h1><p>This is your personalized email.</p>",
    #     substitutions=substitutions,
    # )
    # print(f"Bulk result: sent={result.sent}, failed={result.failed}")


def main() -> None:
    """Run all demonstrations.

    NOTE: The demos use placeholder credentials.  To send real emails,
    set the environment variables SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_AUTH,
    or modify _demo_smtp_config() directly.

    Environment variables:
        SMTP_HOST  - SMTP server hostname (default: smtp.126.com)
        SMTP_PORT  - SMTP port (default: 465)
        SMTP_USER  - Login email address
        SMTP_AUTH  - Authorization code / app password
    """
    print("=" * 60)
    print("Day 29: Python Email and SMS Sending - Demonstrations")
    print("=" * 60)

    _demo_plain_email()
    _demo_html_email()
    _demo_report_emailer()
    _demo_notification_system()
    _demo_alert_system()
    _demo_sms()
    _demo_bulk_email()

    print("\n" + "=" * 60)
    print("All demos complete.  Set SMTP_* env vars to send real emails.")
    print("=" * 60)


if __name__ == "__main__":
    main()
