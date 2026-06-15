# Autonomous Incident Commander

AI-powered incident response that investigates, analyzes, and reports — without a human in the loop.

Built for the **Splunk Agentic Ops Hackathon**.

## What It Does

When an incident fires, the platform:

1. **Queries Splunk MCP** — pulls logs, metrics, and alerts across all affected services
2. **Builds a timeline** — identifies the sequence of events leading to failure
3. **Runs root cause analysis** — AI reasons over log evidence and produces a root cause with a confidence score
4. **Generates an executive PDF report** — downloadable, shareable, ready for the post-mortem

Everything streams live to a single dashboard screen. No human types a query.

## Architecture

```
Browser (React + Vite)
      ↓ SSE stream
FastAPI Backend (Python)
      ↓ asyncio pipeline
[Investigation Agent] → [Timeline Agent] → [RCA Agent] → [Report Agent]
      ↓                                          ↓
Splunk MCP Server                      Anthropic claude-sonnet-4-6
(or built-in simulator)
      ↓
SQLite (incidents, investigations, agent_outputs)
```

## Quick Start

### 1. Clone and set up environment

```bash
git clone <repo>
cd autonomous-incident-commander
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Install dependencies

```bash
# Backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Run

Terminal 1 (backend):
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2 (frontend):
```bash
cd frontend
npm run dev
```

Open http://localhost:5173

### 4. Demo

1. The dashboard loads with a pre-seeded incident (or click "Trigger Demo Incident")
2. Click the incident → Investigation screen opens
3. Click **Start AI Investigation**
4. Watch: logs stream in, AI reasons, timeline builds, PDF generates
5. Click **Download PDF Report**

## Splunk MCP Setup

By default, `SPLUNK_MODE=simulator` — the built-in log generator handles everything.

To connect real Splunk Enterprise:

```bash
# Install Splunk MCP Server
pip install splunk-mcp

# Update .env
SPLUNK_MODE=live
SPLUNK_HOST=your-splunk-host
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your-password
```

**Day 0 checklist:**
- Confirm MCP tool name: run `session.list_tools()` and verify it matches `"search"` in `backend/splunk/mcp_client.py`
- Test the connection before the demo

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Get from console.anthropic.com |
| `SPLUNK_MODE` | `simulator` | `live` or `simulator` |
| `SPLUNK_HOST` | `localhost` | Splunk Enterprise host |
| `SPLUNK_PORT` | `8089` | Splunk management port |
| `SPLUNK_USERNAME` | `admin` | Splunk username |
| `SPLUNK_PASSWORD` | — | Splunk password |

## Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI app, SSE endpoints
│   ├── agents/
│   │   ├── schemas.py           # Pydantic models (shared contracts)
│   │   ├── investigation.py     # Agent 1: log collection
│   │   ├── timeline.py          # Agent 2: chronological ordering
│   │   ├── root_cause.py        # Agent 3: LLM root cause analysis
│   │   ├── report.py            # Agent 4: synthesis + PDF trigger
│   │   └── orchestrator.py      # Sequential pipeline, asyncio Queue
│   ├── splunk/
│   │   └── mcp_client.py        # Splunk MCP wrapper + simulator fallback
│   ├── simulator/
│   │   └── log_generator.py     # DB connection pool exhaustion scenario
│   ├── reports/
│   │   └── pdf_generator.py     # ReportLab PDF builder
│   ├── models.py                # SQLAlchemy ORM (SQLite)
│   ├── database.py              # DB connection + init
│   └── config.py                # Environment variable loading
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx    # Incident list
│       │   └── Investigation.tsx# THE wow screen
│       ├── components/
│       │   ├── LiveLogPanel.tsx # Left: streaming log events
│       │   ├── AIPanel.tsx      # Center: AI reasoning + root cause
│       │   ├── TimelinePanel.tsx# Right: building timeline
│       │   └── ReportPanel.tsx  # Bottom: PDF download
│       └── hooks/
│           └── useIncidentStream.ts  # SSE state management
├── requirements.txt
├── .env.example
└── Makefile
```

## Demo Scenario

**Database Connection Pool Exhaustion** — a realistic 8-minute cascade failure:

```
10:00  Connection pool: 22/50 (normal)
10:01  Connection pool: 42/50 (WARNING — 84% utilization)
10:02  Connection pool: 46/50 → EXHAUSTED 50/50
10:02  checkout-service: DB timeout after 30s
10:02  payment-service: checkout dependency unavailable
10:03  api-gateway: 5xx rate 23% on /checkout
10:04  Circuit breaker OPEN
10:08  ALERT: checkout-service critical error rate exceeded
```

AI investigates these 23 log events and correctly identifies the root cause in under 90 seconds.

## Agents

| Agent | Input | Output |
|---|---|---|
| Investigation | `incident_id`, `service`, `detected_at` | Logs from Splunk MCP across all affected services |
| Timeline | Investigation output | Chronological significant events |
| Root Cause | Investigation + Timeline | Root cause, confidence %, evidence, contributing factors |
| Report | All agent outputs | Executive markdown + PDF |

---

Built with: FastAPI · SQLite · Anthropic claude-sonnet-4-6 · Splunk MCP · React · Vite · TailwindCSS · ReportLab
