# CityPulse AI — Metropolis Crisis Commander & Mayor Advisor

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Google ADK](https://img.shields.io/badge/Agent%20Development%20Kit-ADK-34A853)](https://github.com/google/adk)
[![Agent Runtime](https://img.shields.io/badge/Deployed-Agent%20Runtime%20%2F%20Cloud%20Run-EA4335)](https://cloud.google.com/run)

**CityPulse AI** is an autonomous municipal crisis response advisor and city simulator built with the **Google Agent Development Kit (ADK)** and powered by **Gemini 3.8 Flash**. It monitors real-time municipal health across multiple urban districts, dispatches emergency first responders, coordinates infrastructure budgets, inspects live weather patterns, generates isometric visual crisis renderings, and retains long-term memory across sessions using **Vertex AI Memory Bank**.

---

## 🏛️ System Architecture

```
[ Browser / Custom Chat UI (Dark Theme) ]
                  │
                  ▼
[ FastAPI Proxy on Cloud Run (A2A Protocol Client) ]
                  │
                  ▼
[ Agent Platform / Agent Runtime (Gemini 3.8 Flash) ]
  ├── PreloadMemoryTool & Memory Bank (agentengine://932435338377297920)
  ├── Firestore Native Database (Municipal District State & Dispatch Logs)
  ├── Public Cloud Storage (Public Situational Crisis Snapshots)
  ├── Generative Image Synthesis (gemini-3.1-flash-lite-image)
  ├── Meteorological Intelligence (Live Open-Meteo API)
  └── A2UI v0.8 Rich Component Card Rendering
```

---

## 🛠️ Implemented Capabilities & Google Cloud Stack

* **Autonomous Reasoning**: `gemini-3.8-flash` deployed to **Agent Runtime** (`projects/671379726052/locations/us-east1/reasoningEngines/932435338377297920`).
* **Cross-Session Memory**: `PreloadMemoryTool` and `add_session_to_memory()` callback connected to **Vertex AI Memory Bank** for persistent recall of mayoral directives.
* **Persistent State Management**: **Google Cloud Firestore** native mode storing real-time district statistics (`districts` collection) and audit history (`dispatch_logs` and `budget_allocations`).
* **Visual Crisis Generation**: Generates high-fidelity isometric scene snapshots using `gemini-3.1-flash-lite-image` via Google GenAI, saving local artifacts and uploading to a public **Google Cloud Storage** bucket (`citypulse-ai-qwiklabs-gcp-04-f41e5ebdaead`).
* **External Weather API**: Real-time atmospheric condition lookups via Open-Meteo.
* **Adaptive User Interface (A2UI)**: Schema v0.8 card and component streaming via `a2ui_callback`.
* **Frontend Web Application**: Fast, responsive dark-mode chat UI on **Cloud Run** with one-click quick-action chips.

---

## 🚀 Running Locally

### 1. Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials
- `agents-cli` installed

### 2. Setup & Seeding
```bash
cd citypulse-ai
uv pip install -r requirements.txt
uv pip install google-cloud-firestore google-cloud-storage pillow a2ui-agent-sdk

# Seed Firestore database
uv run python seed_firestore.py
```

### 3. Run Agent CLI
```bash
# Query district status
agents-cli run "What is the health and crisis status of our industrial district?"

# Dispatch emergency units
agents-cli run "Dispatch 2 hazmat units to industrial district to contain the chemical leak"
```

### 4. Run Frontend Locally
```bash
cd frontend
export AGENT_ENGINE_RESOURCE_NAME="projects/671379726052/locations/us-east1/reasoningEngines/932435338377297920"
export AGENT_DIRECTORY="app"
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8080
```
Open [http://localhost:8080](http://localhost:8080) to interact with the city advisor.

---

## ☁️ Deployment

### Deploy Agent Engine
```bash
agents-cli deploy --no-confirm-project
```

### Deploy Frontend to Cloud Run
```bash
gcloud beta run deploy citypulse-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars="AGENT_ENGINE_RESOURCE_NAME=projects/671379726052/locations/us-east1/reasoningEngines/932435338377297920,AGENT_DIRECTORY=app"
```
