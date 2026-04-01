"""
core/alerting.py — Automated Bias & Drift Alert Engine
=======================================================

WHAT THIS MODULE DOES (Simple Explanation to a Junior):
  Imagine you have a smoke detector in your house. It doesn't call the fire
  brigade itself — it just beeps. This module is the SMART version: when our
  ML model "beeps" (drift detected, bias found), this engine actually picks
  up the phone and calls someone — on Slack, by email, or both.

  Three modes:
  - MOCK mode   → Just prints to the console. Great for demos and testing.
  - SLACK mode  → Sends a formatted message to a Slack channel via webhook.
  - EMAIL mode  → Sends an email via SMTP (e.g., Gmail, Outlook, SendGrid).

WHY THIS IS AN INTERVIEW WINNER:
  Most ML projects detect bias but do NOTHING about it automatically.
  This module closes the "Observe → Alert" loop, making the system
  truly production-grade. An interviewer will ask: "Who gets notified
  when bias is detected?" — and you have a working, coded answer.

TECHNICAL APPROACH:
  We use a dataclass-based config (AlertConfig) following the
  "Strategy Pattern" — the engine doesn't care which channel it uses,
  it just calls .send(). This makes it easy to swap channels at runtime.

USAGE:
  from core.alerting import BiasAlertEngine, AlertConfig
  
  engine = BiasAlertEngine(AlertConfig(mode="mock"))
  engine.check_and_alert(model_id="credit_model", analysis_results={...})
"""

import os
import json
import smtplib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List

import httpx  # async-compatible HTTP client (installed with FastAPI)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION (Dataclass-driven — no magic strings scattered in code)
# ============================================================================

@dataclass
class AlertConfig:
    """
    Configuration for the alerting system.

    SIMPLE EXPLANATION:
      This is the "settings panel" for the alarm system.
      You tell it WHERE to send alerts and WHEN to trigger them.

    INTERVIEW TIP:
      "I use a dataclass for configuration instead of a plain dict because
      it gives me type-checking, IDE autocomplete, and clear documentation
      of what settings are available."
    """
    # Where to send alerts. Options: "mock", "slack", "email", "all"
    mode: str = field(default_factory=lambda: os.getenv("ALERT_MODE", "mock"))

    # Slack Incoming Webhook URL (from api.slack.com)
    slack_webhook_url: Optional[str] = field(
        default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL")
    )

    # Email settings
    email_from: Optional[str] = field(
        default_factory=lambda: os.getenv("ALERT_EMAIL_FROM")
    )
    email_to: Optional[str] = field(
        default_factory=lambda: os.getenv("ALERT_EMAIL_TO")
    )
    smtp_host: str = field(
        default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com")
    )
    smtp_port: int = field(
        default_factory=lambda: int(os.getenv("SMTP_PORT", "587"))
    )
    smtp_password: Optional[str] = field(
        default_factory=lambda: os.getenv("SMTP_PASSWORD")
    )

    # THRESHOLDS — these are the "danger lines"
    psi_threshold: float = field(
        default_factory=lambda: float(os.getenv("PSI_ALERT_THRESHOLD", "0.25"))
    )
    fairness_score_min: float = field(
        default_factory=lambda: float(os.getenv("FAIRNESS_SCORE_MIN", "80"))
    )


# ============================================================================
# MESSAGE BUILDER (Separating "what to say" from "how to say it")
# ============================================================================

def _build_alert_payload(
    model_id: str,
    triggered_by: List[str],
    analysis_results: dict,
    severity: str = "WARNING"
) -> dict:
    """
    Builds a structured alert payload from analysis results.

    SIMPLE EXPLANATION:
      This is the "message writer." It takes raw analysis numbers
      and turns them into a human-readable alert card.

    Returns a dict with both a plain-text and Slack Block-formatted message.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    drift_analysis = analysis_results.get("drift_analysis", [])
    bias_analysis = analysis_results.get("bias_analysis", {})
    total_preds = analysis_results.get("total_predictions", 0)

    # Find drifted features for the summary
    drifted_features = [
        f"{d['feature']} (PSI={d.get('psi', 0):.3f})"
        for d in drift_analysis
        if d.get("alert") is True
    ] if drift_analysis else []

    fairness_score = bias_analysis.get("fairness_score", "N/A")

    # --- Plain text (for email and logging) ---
    plain_text = f"""
[{severity}] Bias Drift Guardian Alert — {timestamp}
Model ID   : {model_id}
Triggered By: {", ".join(triggered_by)}
Total Predictions: {total_preds}
Drifted Features  : {", ".join(drifted_features) if drifted_features else "None"}
Fairness Score    : {fairness_score}/100

ACTION REQUIRED:
  1. Review the MLflow dashboard for this experiment.
  2. Check root cause analysis: GET /api/v1/metrics/{model_id}
  3. If confirmed, trigger retraining pipeline.

-- Bias Drift Guardian Auto-Alert
"""

    # --- Slack Block Kit (rich, formatted Slack message) ---
    emoji = ":red_circle:" if severity == "CRITICAL" else ":warning:"
    slack_payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Bias Drift Alert: {model_id}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{timestamp}"},
                    {"type": "mrkdwn", "text": f"*Predictions Analyzed:*\n{total_preds}"},
                    {"type": "mrkdwn", "text": f"*Fairness Score:*\n{fairness_score}/100"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Triggered By:* {', '.join(triggered_by)}\n"
                        f"*Drifted Features:* {', '.join(drifted_features) if drifted_features else 'None'}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Recommended Actions:*\n"
                        "1. :mag: Review root cause via `/api/v1/metrics/" + model_id + "`\n"
                        "2. :chart_with_downwards_trend: Check MLflow for model drift history\n"
                        "3. :arrows_counterclockwise: Trigger retraining if confirmed"
                    )
                }
            },
            {"type": "divider"}
        ]
    }

    return {
        "plain_text": plain_text.strip(),
        "slack_payload": slack_payload,
        "subject": f"[{severity}] Bias Alert: {model_id} @ {timestamp}"
    }


# ============================================================================
# ALERT CHANNELS (Strategy Pattern — each channel is independent)
# ============================================================================

def _send_mock_alert(payload: dict, model_id: str) -> bool:
    """
    MOCK mode: prints alert to console instead of sending externally.

    WHEN TO USE: Local development, CI pipelines, and demo environments.
    INTERVIEW VALUE: Shows you built a testable system — mock mode means
    tests never need a real Slack workspace.
    """
    print("\n" + "=" * 70)
    print("  [MOCK ALERT] Bias Drift Guardian Notification")
    print("=" * 70)
    print(payload["plain_text"])
    print("=" * 70 + "\n")
    logger.info(f"Mock alert fired for model '{model_id}'")
    return True


def _send_slack_alert(payload: dict, webhook_url: str) -> bool:
    """
    Sends a formatted Block Kit message to a Slack channel.

    SIMPLE EXPLANATION:
      Slack gives us a special URL (webhook). We just POST our JSON
      message to that URL and Slack delivers it to the channel.
      No Slack SDK needed — it's just a regular HTTP request.

    INTERVIEW TIP:
      "I chose HTTP webhooks over the Slack SDK because webhooks are
      simpler, don't require OAuth token management, and can be rotated
      without code changes — just update the environment variable."
    """
    try:
        # Using httpx (sync) for simplicity — in async contexts use httpx.AsyncClient
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                webhook_url,
                json=payload["slack_payload"],
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                logger.info("Slack alert sent successfully.")
                return True
            else:
                logger.error(f"Slack returned status {response.status_code}: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def _send_email_alert(payload: dict, config: AlertConfig) -> bool:
    """
    Sends an HTML/plain-text email alert via SMTP.

    SIMPLE EXPLANATION:
      Like the post office for your alerts. We connect to Gmail's SMTP
      server (the "post office"), authenticate, and send the message.
      Uses TLS (encryption) so credentials are protected in transit.

    INTERVIEW TIP:
      "In a real production system, I'd use a dedicated transactional
      email service like SendGrid or AWS SES instead of raw SMTP —
      they handle deliverability, bounces, and unsubscribe automatically.
      But for a self-hosted or on-premise system, SMTP works perfectly."
    """
    if not all([config.email_from, config.email_to, config.smtp_password]):
        logger.warning("Email alerting skipped: SMTP credentials not configured.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = payload["subject"]
        msg["From"] = config.email_from
        msg["To"] = config.email_to

        # Plain text fallback for email clients that don't render HTML
        plain_part = MIMEText(payload["plain_text"], "plain")

        # Simple HTML version for richer display
        html_body = f"""
        <html><body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
          <div style="background: white; border-radius: 8px; padding: 20px; border-left: 5px solid #e53e3e;">
            <h2 style="color: #e53e3e;">⚠️ Bias Drift Alert</h2>
            <pre style="background: #f8f8f8; padding: 15px; border-radius: 4px; font-size: 13px;">
{payload["plain_text"]}
            </pre>
          </div>
        </body></html>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(plain_part)
        msg.attach(html_part)

        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(config.email_from, config.smtp_password)
            server.send_message(msg)

        logger.info(f"Email alert sent to {config.email_to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


# ============================================================================
# THE BRAIN: BiasAlertEngine (Decides WHEN to alert and WHERE to send)
# ============================================================================

class BiasAlertEngine:
    """
    The central orchestrator for the alerting system.

    SIMPLE EXPLANATION TO A JUNIOR:
      Think of this as a security guard sitting at a control panel.
      After every analysis run, the guard checks the numbers. If something
      looks wrong (drift too high, fairness too low), the guard picks
      the right channel (Slack/Email/Both) and calls for help.

    DESIGN DECISION — Why a class and not a function?
      The engine needs to maintain its AlertConfig across multiple calls
      (one config, many analysis runs), and it needs to coordinate
      between multiple delivery strategies — that's a perfect fit for a class.
    """

    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig()
        logger.info(f"BiasAlertEngine initialized in '{self.config.mode}' mode")

    def check_and_alert(self, model_id: str, analysis_results: dict) -> dict:
        """
        Main entry point. Checks thresholds and fires alerts if needed.

        Returns:
            dict with 'alert_fired', 'triggers', and 'channels_used' keys.
        """
        triggers = []
        severity = "WARNING"

        # ── CHECK 1: Data Drift ──────────────────────────────────────────
        # A drifted feature means the production data distribution has shifted
        # away from what the model was trained on. If many features drift,
        # the model's predictions become unreliable.
        drift_analysis = analysis_results.get("drift_analysis", [])
        if isinstance(drift_analysis, list):
            high_drift = [
                d for d in drift_analysis
                if d.get("alert") is True or d.get("psi", 0) > self.config.psi_threshold
            ]
            if high_drift:
                triggers.append(f"DATA DRIFT: {len(high_drift)} feature(s) exceeded PSI threshold ({self.config.psi_threshold})")
                if len(high_drift) >= 3:
                    severity = "CRITICAL"

        # ── CHECK 2: Fairness Score ──────────────────────────────────────
        # A low fairness score means the model treats different demographic
        # groups unequally — this is both an ethical and a legal risk.
        bias_analysis = analysis_results.get("bias_analysis", {})
        fairness_score = bias_analysis.get("fairness_score", 100)
        if isinstance(fairness_score, (int, float)) and fairness_score < self.config.fairness_score_min:
            triggers.append(
                f"BIAS DETECTED: Fairness Score {fairness_score:.1f}/100 "
                f"(minimum: {self.config.fairness_score_min})"
            )
            if fairness_score < 60:
                severity = "CRITICAL"

        # ── No issues found — everything is healthy ──────────────────────
        if not triggers:
            logger.info(f"[{model_id}] All metrics within safe thresholds. No alert needed.")
            return {"alert_fired": False, "triggers": [], "channels_used": []}

        # ── Build and dispatch the alert ─────────────────────────────────
        payload = _build_alert_payload(
            model_id=model_id,
            triggered_by=triggers,
            analysis_results=analysis_results,
            severity=severity
        )

        channels_used = self._dispatch(payload, model_id)

        return {
            "alert_fired": True,
            "severity": severity,
            "triggers": triggers,
            "channels_used": channels_used,
            "timestamp": datetime.now().isoformat()
        }

    def _dispatch(self, payload: dict, model_id: str) -> list:
        """Routes the alert to the correct channel(s) based on config.mode."""
        mode = self.config.mode.lower()
        channels_used = []

        if mode in ("mock", "all"):
            if _send_mock_alert(payload, model_id):
                channels_used.append("mock_console")

        if mode in ("slack", "all"):
            if self.config.slack_webhook_url:
                if _send_slack_alert(payload, self.config.slack_webhook_url):
                    channels_used.append("slack")
            else:
                logger.warning("Slack mode enabled but SLACK_WEBHOOK_URL is not set.")

        if mode in ("email", "all"):
            if _send_email_alert(payload, self.config):
                channels_used.append("email")

        if not channels_used:
            logger.error("Alert could not be dispatched to any channel. Check your config.")

        return channels_used
