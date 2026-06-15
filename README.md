# Autonomous Incident Commander

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

> **Splunk Agentic Ops Hackathon submission**

AI-powered incident response that **autonomously investigates, analyzes, and reports** — no human in the loop.

When an alert fires, the platform queries Splunk MCP, builds an incident timeline, identifies the root cause with a confidence score, and delivers an executive-ready PDF report — all without a human typing a single query.

---

## The Problem

Modern SRE teams spend **30–90 minutes per incident** on tasks that are mechanical:

- Searching logs across services
- Correlating timestamps to build a timeline
- Identifying what failed first and why
- Writing up an incident report for leadership

Existing AI tools (Splunk AI Assistant, Datadog Bits AI, Dynatrace Davis) are **copilots** — they answer questions when asked. They don't act.

**Autonomous Incident Commander acts.**

---

## Architecture

See [`architecture_diagram.md`](./architecture_diagram.md) for full diagrams (system architecture, data flow sequence, agent data contracts).

```
Browser (React + Vite)
      │
      │  POST /api/investigate/{id}/start
      │  GET  /api/investigate/{id}/stream  ← EventSource (SSE)
      ▼
FastAPI Backend (Python + asyncio)
      │
      │  asyncio.Queue → BackgroundTask
      ▼
┌─────────────────────────────────────────────────────────┐
│                  4-Agent Pipeline                        │
│                                                         │
│  [1] Investigation Agent                                │
│      └─ Queries Splunk MCP (or log simulator)           │
│         → InvestigationOutput                           │
│                   ↓                                     │
│  [2] Timeline Agent                                     │
│      └─ Chronological event ordering                    │
│         → TimelineOutput                                │
│                   ↓                                     │
│  [3] Root Cause Agent  ⭐                               │
│      └─ LLM streaming reasoning (claude-sonnet-4-6)     │
│         → RCAOutput {root_cause, confidence_pct, ...}   │
│                   ↓                                     │
│  [4] Report Agent                                       │
│      └─ Executive PDF generation (ReportLab)            │
│         → ReportOutput + PDF file                       │
└─────────────────────────────────────────────────────────┘
      │
      ├─ Splunk MCP Server (stdio) → Splunk Enterprise
      └─ Anthropic API (claude-sonnet-4-6, streaming)
```

---

## Features

- **Live Incident Theater** — single-screen dashboard where logs, AI reasoning, and timeline all stream simultaneously in real time
- **Splunk MCP Integration** — Investigation Agent calls Splunk as a tool via the MCP protocol; transparent fallback to the built-in log simulator
- **Root Cause Analysis with confidence scoring** — genuine LLM output, not hardcoded; streams token-by-token in the UI (typewriter effect)
- **Auto-generated incident timeline** — chronological event ordering with severity classification across all affected services
- **Executive PDF report** — incident summary, timeline table, root cause, evidence, prioritized remediation; downloadable at end of investigation
- **Pre-seeded demo scenario** — Database Connection Pool Exhaustion cascade (24 realistic log events, 5 services, 8-minute incident window)

---

## Requirements

### System

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Frontend package manager |

### Python packages (auto-installed via `requirements.txt`)

| Package | Purpose |
|---|---|
| `fastapi` | REST API + SSE streaming |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy` | ORM (SQLite) |
| `anthropic` | LLM API client (claude-sonnet-4-6) |
| `mcp` | Splunk MCP Server client |
| `reportlab` | PDF generation |
| `python-dotenv` | Environment variable loading |
| `pydantic` | Agent data contracts / schema validation |
| `aiofiles` | Async file I/O |

### API Keys

| Key | Required | Where to get |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | [console.anthropic.com](https://console.anthropic.com) |
| Splunk credentials | Optional | Only needed for `SPLUNK_MODE=live` |

---

## Setup & Run

### 1. Clone the repository

```bash
git clone https://github.com/abhijha8287/Autonomous-Incident-Commander.git
cd Autonomous-Incident-Commander
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Leave `SPLUNK_MODE=simulator` for the demo — no Splunk Enterprise required.

### 3. Install backend dependencies

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Run

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
# From project root, with venv activated
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

## Example Configuration

### `.env` — Development (simulator mode, no Splunk required)

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=
SPLUNK_MODE=simulator
```

### `.env` — Production (live Splunk Enterprise)

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
SPLUNK_HOST=your-splunk-host.company.com
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your-splunk-password
SPLUNK_MODE=live
```

### Environment Variable Reference

| Variable | Default | Required | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Yes** | Anthropic API key for claude-sonnet-4-6 |
| `SPLUNK_MODE` | `simulator` | No | `simulator` = built-in logs \| `live` = real Splunk |
| `SPLUNK_HOST` | `localhost` | If live | Splunk Enterprise hostname |
| `SPLUNK_PORT` | `8089` | If live | Splunk management port |
| `SPLUNK_USERNAME` | `admin` | If live | Splunk username |
| `SPLUNK_PASSWORD` | — | If live | Splunk password |

---

## Connecting to Splunk Enterprise

> Skip this section if using the built-in simulator (`SPLUNK_MODE=simulator`).

### 1. Install the Splunk MCP Server

Follow [Splunk's MCP Server setup guide](https://github.com/splunk/splunk-mcp) to install and configure the server.

### 2. Update `.env`

```env
SPLUNK_MODE=live
SPLUNK_HOST=your-splunk-instance
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your-password
```

### 3. Confirm the MCP tool name

The exact tool name exposed by the Splunk MCP Server varies by version. Run this once before the demo:

```python
# quick_check.py — run from project root with venv activated
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check():
    params = StdioServerParameters(
        command="splunk-mcp",
        args=["--host", "your-host", "--port", "8089",
              "--username", "admin", "--password", "your-pass"]
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

asyncio.run(check())
```

Update `backend/splunk/mcp_client.py` line with `call_tool(...)` if the tool name differs from `"search"`.

---

## Running the Demo Scenario

The platform pre-seeds a **Database Connection Pool Exhaustion** incident on startup. See [`demo.md`](./demo.md) for the full 4-minute demo script.

**Quick demo:**

1. Open http://localhost:5173 — one active incident is waiting
2. Click the incident → Investigation screen opens
3. Click **Start AI Investigation**
4. Watch: logs stream, timeline builds, AI reasons, PDF generates
5. Click **Download PDF Report**

To trigger a fresh incident at any time:

```bash
curl -X POST http://localhost:8000/api/incidents/trigger \
  -H "Content-Type: application/json" \
  -d '{"service": "checkout-service", "title": "Critical Error Rate — checkout-service"}'
```

---

## Project Structure

```
Autonomous-Incident-Commander/
├── backend/
│   ├── main.py                    # FastAPI app, all API endpoints, SSE stream
│   ├── config.py                  # Environment variable loading
│   ├── database.py                # SQLite connection + schema init
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── agents/
│   │   ├── schemas.py             # Pydantic models — shared agent data contracts
│   │   ├── orchestrator.py        # Sequential pipeline, asyncio.Queue handoff
│   │   ├── investigation.py       # Agent 1: Splunk MCP log collection
│   │   ├── timeline.py            # Agent 2: chronological event ordering
│   │   ├── root_cause.py          # Agent 3: LLM root cause analysis (streaming)
│   │   └── report.py              # Agent 4: synthesis + PDF trigger
│   ├── splunk/
│   │   └── mcp_client.py          # Splunk MCP wrapper + simulator fallback
│   ├── simulator/
│   │   └── log_generator.py       # 24-event DB connection pool exhaustion scenario
│   └── reports/
│       └── pdf_generator.py       # ReportLab PDF: summary, timeline, RCA, remediation
├── frontend/
│   └── src/
│       ├── App.tsx                # Router
│       ├── pages/
│       │   ├── Dashboard.tsx      # Incident list + trigger button
│       │   └── Investigation.tsx  # Live Incident Theater (the wow screen)
│       ├── components/
│       │   ├── LiveLogPanel.tsx   # Left: streaming log events
│       │   ├── AIPanel.tsx        # Center: AI reasoning + root cause card
│       │   ├── TimelinePanel.tsx  # Right: building incident timeline
│       │   └── ReportPanel.tsx    # Bottom bar: PDF download
│       └── hooks/
│           └── useIncidentStream.ts  # EventSource SSE state management
├── architecture_diagram.md        # System architecture + sequence diagrams
├── demo.md                        # 4-minute demo script for judges
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── Makefile                       # Dev shortcuts
├── LICENSE                        # MIT License
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/incidents` | List all incidents |
| `GET` | `/api/incidents/{id}` | Get incident + investigation history |
| `POST` | `/api/incidents/trigger` | Trigger a new demo incident |
| `POST` | `/api/investigate/{id}/start` | Start agent pipeline, returns `stream_url` |
| `GET` | `/api/investigate/{id}/stream` | SSE stream of agent progress |
| `GET` | `/api/investigate/{id}/results` | Final structured results (JSON) |
| `GET` | `/api/reports/{id}/pdf` | Download PDF report |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

---

## Demo Scenario — DB Connection Pool Exhaustion

The built-in simulator generates a realistic 8-minute cascade failure:

```
10:00:00  INFO     database         Connection pool initialized: 0/50
10:01:00  INFO     database         Connection pool: 22/50 — normal load
10:01:30  WARNING  database         Connection pool: 42/50 — 84% utilization
10:01:50  WARNING  checkout-service DB query latency elevated: 620ms
10:02:00  CRITICAL database         Connection pool EXHAUSTED: 50/50
10:02:05  ERROR    checkout-service Database connection timeout after 30s
10:02:25  ERROR    payment-service  Checkout dependency unavailable — halted
10:02:45  ERROR    api-gateway      5xx rate: 18% on /api/checkout
10:03:05  CRITICAL checkout-service Circuit breaker OPEN
10:04:00  CRITICAL payment-service  47 transactions failed in last 60s
10:08:00  ALERT    alerting         INCIDENT: checkout-service critical error rate
```

The AI analyzes these 24 events and correctly identifies **Database Connection Pool Exhaustion** as the root cause, with evidence citations and prioritized remediation steps.

---

## License

MIT — see [LICENSE](./LICENSE)

---

Built for the **Splunk Agentic Ops Hackathon** · FastAPI · SQLite · Anthropic claude-sonnet-4-6 · Splunk MCP · React · Vite · TailwindCSS · ReportLab
