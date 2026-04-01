"""
tests/test_alerting.py — Unit Tests for the BiasAlertEngine
============================================================

WHAT WE ARE TESTING (Simple Explanation):
  We test the alerting engine the same way you'd test a smoke detector.
  We create a "fake fire" (inject analysis results with high drift/low fairness)
  and verify that:
    1. The alarm fires (alert_fired == True)
    2. The right reason is recorded (triggers list)
    3. The message is well-formed (payload has required fields)

TEST PHILOSOPHY (AAA Pattern):
  ARRANGE → Set up the conditions
  ACT     → Call the function under test
  ASSERT  → Verify the outcome is correct

COVERAGE:
  - No alert fires when everything is healthy
  - Alert fires on high PSI drift
  - Alert fires on low fairness score
  - CRITICAL severity is set correctly for extreme cases
  - Mock channel is used in test mode
  - Payload builder creates valid Slack and plain-text messages
"""

import pytest
from core.alerting import (
    BiasAlertEngine,
    AlertConfig,
    _build_alert_payload,
    _send_mock_alert,
)


# ──────────────────────────────────────────────────────────────────────────────
# FIXTURES — Reusable test data
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_engine():
    """Returns an engine configured in MOCK mode (no external calls)."""
    config = AlertConfig(
        mode="mock",
        psi_threshold=0.25,
        fairness_score_min=80.0
    )
    return BiasAlertEngine(config=config)


@pytest.fixture
def healthy_analysis():
    """Analysis results that SHOULD NOT trigger any alert."""
    return {
        "model_id": "test_model",
        "total_predictions": 200,
        "drift_analysis": [
            {"feature": "age", "psi": 0.05, "alert": False},
            {"feature": "income", "psi": 0.08, "alert": False},
        ],
        "bias_analysis": {
            "fairness_score": 92,
        },
        "root_cause_report": None
    }


@pytest.fixture
def high_drift_analysis():
    """Analysis results with PSI well ABOVE the threshold (should trigger alert)."""
    return {
        "model_id": "credit_model",
        "total_predictions": 500,
        "drift_analysis": [
            {"feature": "age", "psi": 0.35, "alert": True},
            {"feature": "housing", "psi": 0.42, "alert": True},
        ],
        "bias_analysis": {
            "fairness_score": 85,  # Still OK
        },
        "root_cause_report": "Feature 'housing' is the primary drift driver."
    }


@pytest.fixture
def low_fairness_analysis():
    """Analysis results with fairness BELOW the minimum (should trigger alert)."""
    return {
        "model_id": "hiring_model",
        "total_predictions": 1000,
        "drift_analysis": [
            {"feature": "age", "psi": 0.03, "alert": False},
        ],
        "bias_analysis": {
            "fairness_score": 62,  # Below 80 minimum → alert!
        },
        "root_cause_report": None
    }


@pytest.fixture
def critical_analysis():
    """Analysis with BOTH high drift AND very low fairness → CRITICAL severity."""
    return {
        "model_id": "risk_model",
        "total_predictions": 800,
        "drift_analysis": [
            {"feature": "age", "psi": 0.55, "alert": True},
            {"feature": "income", "psi": 0.48, "alert": True},
            {"feature": "housing", "psi": 0.61, "alert": True},
        ],
        "bias_analysis": {
            "fairness_score": 45,  # Critically low → CRITICAL severity
        },
        "root_cause_report": "Multiple features drifting simultaneously."
    }


# ──────────────────────────────────────────────────────────────────────────────
# TEST CASES
# ──────────────────────────────────────────────────────────────────────────────

class TestAlertThresholds:
    """Tests for the threshold detection logic."""

    def test_no_alert_when_healthy(self, mock_engine, healthy_analysis):
        """ARRANGE/ACT/ASSERT: No alert when all metrics are within bounds."""
        result = mock_engine.check_and_alert("test_model", healthy_analysis)

        assert result["alert_fired"] is False
        assert result["triggers"] == []
        assert result["channels_used"] == []

    def test_alert_fires_on_high_drift(self, mock_engine, high_drift_analysis):
        """Alert should fire when PSI exceeds the threshold."""
        result = mock_engine.check_and_alert("credit_model", high_drift_analysis)

        assert result["alert_fired"] is True
        assert len(result["triggers"]) >= 1
        # The trigger message should mention DRIFT
        assert any("DRIFT" in t for t in result["triggers"])

    def test_alert_fires_on_low_fairness(self, mock_engine, low_fairness_analysis):
        """Alert should fire when fairness score drops below minimum."""
        result = mock_engine.check_and_alert("hiring_model", low_fairness_analysis)

        assert result["alert_fired"] is True
        assert any("BIAS" in t for t in result["triggers"])

    def test_critical_severity_on_extreme_case(self, mock_engine, critical_analysis):
        """Both high drift AND critically low fairness → CRITICAL severity."""
        result = mock_engine.check_and_alert("risk_model", critical_analysis)

        assert result["alert_fired"] is True
        assert result["severity"] == "CRITICAL"
        assert len(result["triggers"]) == 2  # Both drift and bias triggers

    def test_mock_channel_used_in_mock_mode(self, mock_engine, high_drift_analysis):
        """In mock mode, the 'mock_console' channel should be listed."""
        result = mock_engine.check_and_alert("credit_model", high_drift_analysis)

        assert result["alert_fired"] is True
        assert "mock_console" in result["channels_used"]


class TestPayloadBuilder:
    """Tests for the message formatting functions."""

    def test_payload_has_required_keys(self):
        """The payload dict must have all three required keys."""
        payload = _build_alert_payload(
            model_id="test_model",
            triggered_by=["DATA DRIFT: 2 features exceeded PSI"],
            analysis_results={
                "total_predictions": 100,
                "drift_analysis": [{"feature": "age", "psi": 0.3, "alert": True}],
                "bias_analysis": {"fairness_score": 75}
            }
        )
        assert "plain_text" in payload
        assert "slack_payload" in payload
        assert "subject" in payload

    def test_plain_text_contains_model_id(self):
        """The plain text alert should mention the model ID."""
        payload = _build_alert_payload(
            model_id="my_special_model",
            triggered_by=["TEST TRIGGER"],
            analysis_results={}
        )
        assert "my_special_model" in payload["plain_text"]

    def test_slack_payload_has_blocks(self):
        """Slack payload must use Block Kit structure (has 'blocks' key)."""
        payload = _build_alert_payload(
            model_id="slack_test",
            triggered_by=["DATA DRIFT"],
            analysis_results={"bias_analysis": {"fairness_score": 70}}
        )
        assert "blocks" in payload["slack_payload"]
        assert len(payload["slack_payload"]["blocks"]) > 0

    def test_severity_in_subject(self):
        """The email subject should include the severity level."""
        payload = _build_alert_payload(
            model_id="test",
            triggered_by=["TRIGGER"],
            analysis_results={},
            severity="CRITICAL"
        )
        assert "CRITICAL" in payload["subject"]


class TestEdgeCases:
    """Tests for graceful handling of missing or malformed data."""

    def test_engine_handles_empty_drift_analysis(self, mock_engine):
        """Engine should not crash when drift_analysis list is empty."""
        result = mock_engine.check_and_alert("model_x", {
            "drift_analysis": [],
            "bias_analysis": {"fairness_score": 95}
        })
        assert result["alert_fired"] is False

    def test_engine_handles_missing_bias_analysis(self, mock_engine):
        """Engine should not crash when bias_analysis key is missing."""
        result = mock_engine.check_and_alert("model_y", {
            "drift_analysis": [],
            # 'bias_analysis' key is absent
        })
        assert result["alert_fired"] is False

    def test_engine_handles_none_fairness_score(self, mock_engine):
        """Engine should not crash when fairness_score is None."""
        result = mock_engine.check_and_alert("model_z", {
            "drift_analysis": [],
            "bias_analysis": {"fairness_score": None}
        })
        # None fairness score should not trigger alert (treated as healthy)
        assert result["alert_fired"] is False

    def test_custom_thresholds_respected(self):
        """Custom PSI and fairness thresholds should override defaults."""
        # Set a very strict threshold (PSI > 0.01 triggers alert)
        strict_config = AlertConfig(mode="mock", psi_threshold=0.01, fairness_score_min=95)
        engine = BiasAlertEngine(config=strict_config)

        # PSI of 0.05 is "safe" by default but unsafe with strict threshold
        result = engine.check_and_alert("strict_model", {
            "drift_analysis": [{"feature": "age", "psi": 0.05, "alert": False}],
            "bias_analysis": {"fairness_score": 98}  # OK even with strict threshold
        })
        # Only drift should trigger (PSI 0.05 > custom threshold 0.01)
        assert result["alert_fired"] is True
        assert any("DRIFT" in t for t in result["triggers"])
