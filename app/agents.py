# app/agents.py
"""Agents for FinGuard AI investigation workflow.
Implemented using simple functions; LangGraph composes them into a graph.
Each agent returns a dict that is passed to the next step.
"""

import json
import os
from typing import List, Dict, Any

from datetime import datetime

# Load synthetic compliance policies (simple list of dicts)
POLICIES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "policies.json")
if os.path.exists(POLICIES_PATH):
    with open(POLICIES_PATH, "r") as f:
        COMPLIANCE_POLICIES = json.load(f)
else:
    COMPLIANCE_POLICIES = []  # fallback empty list


def load_alert(alert_id: str) -> Dict[str, Any]:
    """Load a synthetic alert from ``data/sample_alerts.json``.
    Returns the alert dict and a ``metadata`` key for provenance.
    """
    alerts_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_alerts.json")
    with open(alerts_path, "r") as f:
        alerts = json.load(f)
    alert = next((a for a in alerts if a["alert_id"] == alert_id), alerts[0])
    return {"alert": alert, "metadata": {"loaded_at": datetime.utcnow().isoformat()}}


def transaction_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simple rule‑based analysis of a transaction using only the standard library.
    Flags:
      - ``unusual_amount``: amount > 10,000 or > 3× median for the customer.
      - ``high_frequency``: more than 5 transactions in the last 24 h for the customer.
      - ``new_beneficiary``: beneficiary not seen before for this customer.
    """
    alert = state["alert"]
    history = alert.get("historical_transactions", [])
    cur = alert["transaction"]
    # Compute median amount manually
    amounts = [tx["amount"] for tx in history]
    if amounts:
        sorted_amounts = sorted(amounts)
        n = len(sorted_amounts)
        median_amount = (sorted_amounts[n // 2] if n % 2 == 1 else
                         (sorted_amounts[n // 2 - 1] + sorted_amounts[n // 2]) / 2)
    else:
        median_amount = cur["amount"]
    unusual_amount = cur["amount"] > max(10_000, 3 * median_amount)
    # High frequency in last 24h (simple string comparison assuming ISO timestamps)
    from datetime import datetime, timedelta
    cur_time = datetime.fromisoformat(cur["timestamp"].replace("Z", "+00:00"))
    window_start = cur_time - timedelta(hours=24)
    high_frequency = sum(1 for tx in history
                         if datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00")) >= window_start) >= 5
    # New beneficiary
    known_beneficiaries = {tx["beneficiary"] for tx in history}
    new_beneficiary = cur["beneficiary"] not in known_beneficiaries
    flags = []
    if unusual_amount:
        flags.append("Unusual amount")
    if high_frequency:
        flags.append("High frequency")
    if new_beneficiary:
        flags.append("New beneficiary")
    analysis = {
        "unusual_amount": unusual_amount,
        "high_frequency": high_frequency,
        "new_beneficiary": new_beneficiary,
        "flags": flags,
    }
    state["analysis"] = analysis
    return state


def evidence_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant compliance policy snippets.
    Very simple keyword match against ``COMPLIANCE_POLICIES``.
    """
    flags = state["analysis"]["flags"]
    # Build a naive keyword list from flags
    keywords = [kw.lower() for kw in flags]
    matches: List[Dict[str, str]] = []
    for pol in COMPLIANCE_POLICIES:
        text = pol.get("text", "").lower()
        if any(kw in text for kw in keywords):
            matches.append({"policy_id": pol.get("policy_id"), "excerpt": pol.get("text")[:200]})
    state["evidence"] = matches
    return state


def risk_assessment(state: Dict[str, Any]):
    """Call OpenAI to summarise findings.
    If the API fails or the key is missing, fall back to a deterministic template.
    """
    import os
    from openai import OpenAI
    from openai import APIError

    analysis = state["analysis"]
    evidence = state["evidence"]
    alert = state["alert"]
    # Build a short prompt
    prompt = f"""You are an AML analyst. Summarise the following transaction alert and the analysis flags.
    Transaction ID: {alert['transaction']['transaction_id']}
    Flags: {', '.join(analysis['flags']) or 'None'}
    Evidence snippets: {', '.join(e['excerpt'] for e in evidence) or 'None'}
    Provide a short risk assessment and list any missing information that would be useful for a human reviewer.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        assessment = resp.choices[0].message.content.strip()
    except Exception as e:  # includes missing key, network error, APIError
        # Deterministic fallback – a simple templated string
        assessment = (
            "[Fallback assessment] The transaction flagged the following issues: "
            f"{', '.join(analysis['flags']) or 'none'}. "
            "No additional evidence was retrieved. "
            "Human review is required to confirm AML risk."
        )
    state["assessment"] = assessment
    return state


def generate_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Combine all pieces into a JSON‑serialisable investigation report.
    The report contains:
      - alert metadata
      - analysis flags
      - evidence references
      - risk assessment text
      - disclaimer
    """
    report = {
        "alert_id": state["alert"]["alert_id"],
        "transaction_id": state["alert"]["transaction"]["transaction_id"],
        "analysis": state["analysis"]["flags"],
        "evidence": state["evidence"],
        "assessment": state["assessment"],
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": (
            "This investigation is automated and provided for assistance only. "
            "All findings require review by a qualified AML analyst before any action is taken."
        ),
    }
    state["report"] = report
    return state

# LangGraph graph definition (lightweight, no custom node classes)
from langgraph.graph import StateGraph, END

# Define the state schema – we keep it simple (any dict works)
workflow = StateGraph(dict)
workflow.add_node("load_alert", lambda state: load_alert(state.get("alert_id", "")))
workflow.add_node("analysis", transaction_analysis)
workflow.add_node("evidence", evidence_retrieval)
workflow.add_node("assessment", risk_assessment)
workflow.add_node("report", generate_report)

workflow.set_entry_point("load_alert")
workflow.add_edge("load_alert", "analysis")
workflow.add_edge("analysis", "evidence")
workflow.add_edge("evidence", "assessment")
workflow.add_edge("assessment", "report")
workflow.add_edge("report", END)

# Export the compiled graph for import in FastAPI
app_graph = workflow.compile()
