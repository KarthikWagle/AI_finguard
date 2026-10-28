# FinGuard AI – AI‑Powered AML Investigation Assistant

## Overview
FinGuard AI is a lightweight Python prototype that demonstrates an end‑to‑end AML investigation workflow using **LangGraph** for multi‑agent orchestration, the **OpenAI** API for risk assessment, **FastAPI** for a simple backend, and **Streamlit** for a user‑facing dashboard.

It creates **synthetic transaction alerts**, runs rule‑based analysis, retrieves relevant compliance policy snippets, asks an LLM for a risk summary (with a deterministic fallback), and outputs a structured JSON investigation report.  All findings are **disclaimers‑aware** – a human analyst must review the results before any action.

The project is intentionally minimal: no database, no cloud services, and no Docker.  It can be cloned, installed, and run on a Windows machine with a standard Python installation.

---

## Project Structure
```
FinGuardAI/
├─ app/
│  ├─ __init__.py          # (optional) makes the package importable
│  ├─ agents.py            # LangGraph agents & workflow
│  └─ main.py              # FastAPI app exposing /health and /investigate
├─ frontend/
│  └─ streamlit_app.py     # Simple UI to trigger investigations
├─ data/
│  ├─ sample_alerts.json   # Synthetic transaction alerts
│  └─ policies.json        # Small set of compliance policies
├─ tests/
│  └─ test_rules.py        # pytest tests for analysis & report logic
├─ .env.example            # Example environment file (do NOT commit secrets)
├─ .gitignore              # Ignores caches, env files, etc.
├─ requirements.txt        # Python dependencies (core only)
└─ README.md               # You are reading it!
```

*The `requirements.txt` contains only the core libraries required for the backend and agent logic.  `streamlit` is optional and can be installed later if you want to run the UI.*

---

## Setup Instructions (Windows PowerShell)
```powershell
# 1️⃣ Clone the repository (replace <repo-url> with your repo)
git clone <repo-url> FinGuardAI
cd FinGuardAI

# 2️⃣ Create a virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # activate in PowerShell

# 3️⃣ Install core dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4️⃣ (Optional) Install Streamlit for the dashboard
#    If you only need the API, skip this step.
python -m pip install streamlit

# 5️⃣ Configure environment variables
#    Copy the example and fill in your OpenAI key.
copy .env.example .env
# Then edit .env with a text editor and set:
# OPENAI_API_KEY=sk-xxxxxx   (or leave empty to force the fallback)

# 6️⃣ Run the FastAPI backend
uvicorn app.main:app --reload --port 8000
# The API will be reachable at http://127.0.0.1:8000

# 7️⃣ (Optional) Run the Streamlit dashboard in a new terminal
streamlit run frontend\streamlit_app.py
# Open the URL shown by Streamlit (by default http://localhost:8501)

# 8️⃣ Run the test suite
pytest -q
```

---

## How the Workflow Works
1. **Synthetic Alert** – `data/sample_alerts.json` contains a few fabricated transaction alerts.
2. **Transaction Analysis Agent** – Flags unusual amount, high frequency, and new beneficiary using only the Python standard library.
3. **Evidence Retrieval Agent** – Performs a cheap keyword match against `data/policies.json` to pull relevant policy excerpts.
4. **Risk Assessment Agent** – Calls the OpenAI API to generate a short narrative.  If the key is missing or the call fails, a deterministic fallback string is returned.
5. **Report Generator** – Packages everything into a JSON report that includes a disclaimer requiring human review.
6. **FastAPI Endpoint** – `POST /investigate` accepts an `alert_id` and returns the JSON report.
7. **Streamlit UI** – Lets a user pick an alert, invoke the backend, and view the report.

---

## Testing
The `tests/test_rules.py` file checks three core behaviours:
* Correct flags are produced by the analysis step.
* The OpenAI fallback path works when `OPENAI_API_KEY` is absent.
* The final report contains all required fields and the disclaimer.

Run the tests with:
```powershell
pytest -q
```
If the OpenAI key is not set, the fallback test will still pass.

---

## Limitations & Future Work
* **No persistence** – All data is in‑memory/JSON files.
* **No real AML logic** – The rule set is deliberately simple for demo purposes.
* **Streamlit optional** – It is excluded from the core `requirements.txt` to keep the install lightweight on machines without a C++ build chain.
* **No Docker / Cloud** – The MVP runs locally; containerisation can be added later.
* **Security** – Remember to keep `.env` out of version control; never commit real API keys.

---

## Disclaimer
> This investigation is automated and provided for assistance only. All findings require review by a qualified AML analyst before any action is taken.

---

*Happy hacking, and good luck with your AI/ML Engineer Intern application!*