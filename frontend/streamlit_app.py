import streamlit as st
import requests
import json
import os
from pathlib import Path

# Backend URL – assume FastAPI runs on localhost:8000
API_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")

# Load alerts locally for UI dropdown
alerts_path = Path(__file__).parent.parent / "data" / "sample_alerts.json"
with open(alerts_path) as f:
    alerts = json.load(f)

alert_options = {alert["alert_id"]: alert for alert in alerts}

st.title("FinGuard AI – AML Investigation Assistant")
st.caption("Select a synthetic alert and run an automated investigation. Results require human review.")

selected_id = st.selectbox("Select Alert", list(alert_options.keys()))
selected_alert = alert_options[selected_id]

if st.button("Run Investigation"):
    with st.spinner("Running investigation via backend …"):
        try:
            resp = requests.post(f"{API_URL}/investigate", json={"alert_id": selected_id})
            resp.raise_for_status()
            report = resp.json()
            st.success("Investigation completed")
            st.subheader("Report")
            st.json(report)
        except Exception as e:
            st.error(f"Error contacting backend: {e}")

st.markdown("---")
st.caption(
    "Disclaimer: This investigation is automated and provided for assistance only. "
    "All findings require review by a qualified AML analyst before any action is taken."
)
