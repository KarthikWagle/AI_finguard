import sys, os
# Ensure the project root is in the import path for pytest execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.agents import load_alert, transaction_analysis, risk_assessment, generate_report

@pytest.fixture
def alert_state():
    """Load a known synthetic alert for testing."""
    return load_alert("alert_001")

def test_transaction_analysis_flags(alert_state):
    state = transaction_analysis(alert_state)
    flags = state["analysis"]["flags"]
    assert "Unusual amount" in flags
    assert "New beneficiary" in flags
    assert "High frequency" not in flags

def test_risk_assessment_fallback(monkeypatch, alert_state):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    state = transaction_analysis(alert_state)
    state = risk_assessment(state)
    assessment = state["assessment"]
    assert assessment.startswith("[Fallback assessment]")
    assert "Unusual amount" in assessment

def test_generate_report_structure(alert_state):
    state = transaction_analysis(alert_state)
    state = risk_assessment(state)
    state = generate_report(state)
    report = state["report"]
    for key in ["alert_id", "transaction_id", "analysis", "evidence", "assessment", "generated_at", "disclaimer"]:
        assert key in report
    assert "human review" in report["disclaimer"].lower()
