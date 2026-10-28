# Autonomous Incident Commander

When an alert fires, this agent searches the logs, builds an incident timeline, finds the likely root cause with a confidence score and writes an executive PDF report.

## Why this exists
Submission for the Splunk Agentic Ops Hackathon. Engineers often spend 30-90 minutes per incident on mechanical work: searching logs across services, lining up timestamps, finding what failed first and writing the report. Most AI tools answer questions when asked; this one runs the investigation itself.

## What it does
- Investigation agent queries Splunk as a tool through MCP, or a built-in log simulator when Splunk is not available
- Timeline agent orders events across services and classifies severity
- Root-cause agent (Claude) explains what failed first, with a confidence score and evidence, streamed to the UI
- Report agent writes a downloadable PDF: summary, timeline, root cause, evidence and prioritised fixes
- Single dashboard streams logs, agent reasoning and timeline live (server-sent events)
- Ships with a demo incident: database connection-pool exhaustion cascading across 5 services

## Project structure
```
Autonomous-Incident-Commander/
├── backend/
│   ├── agents/           Orchestrator, investigation, timeline, root cause, report
│   ├── splunk/           Splunk MCP client
│   ├── simulator/        Demo log generator
│   ├── reports/          PDF report builder
│   ├── main.py           FastAPI app and SSE stream
│   ├── models.py         Database models
│   ├── database.py       SQLite setup
│   └── config.py         Settings
├── frontend/src/         React dashboard
├── architecture_diagram.md  System diagram
├── demo.md               Demo script
├── Makefile              Install and run shortcuts
└── requirements.txt      Python dependencies
```

## Getting started
Requirements: Python 3.11+, Node.js 18+, an Anthropic API key.
```bash
git clone https://github.com/abhijha8287/Autonomous-Incident-Commander.git
cd Autonomous-Incident-Commander
cp .env.example .env                     # set ANTHROPIC_API_KEY, keep SPLUNK_MODE=simulator
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
python -m uvicorn backend.main:app --reload --port 8000    # terminal 1
cd frontend && npm run dev                                  # terminal 2, http://localhost:5173
```
Or use `make install` and `make dev`.

## Configuration
| Variable | Purpose |
|:--|:--|
| `ANTHROPIC_API_KEY` | Claude API key (required) |
| `SPLUNK_MODE` | `simulator` (default) or `live` |
| `SPLUNK_HOST`, `SPLUNK_PORT`, `SPLUNK_USERNAME`, `SPLUNK_PASSWORD` | Only for `SPLUNK_MODE=live` |

## Tech stack
Python, FastAPI, Anthropic Claude API, MCP, SQLAlchemy, SQLite, ReportLab, React, TypeScript, Vite, Tailwind CSS

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

## License

MIT — see [LICENSE](./LICENSE)

---

Built for the **Splunk Agentic Ops Hackathon** · FastAPI · SQLite · Anthropic claude-sonnet-4-6 · Splunk MCP · React · Vite · TailwindCSS · ReportLab
