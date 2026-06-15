# Architecture Diagram — Autonomous Incident Commander

## System Architecture

```mermaid
graph TB
    subgraph Browser["🖥️ Frontend (React + Vite + TailwindCSS)"]
        DASH[Dashboard Page<br/>Incident List]
        INVP[Investigation Page<br/>Live Incident Theater]
        LP[Live Log Panel<br/>Streaming log events]
        AP[AI Panel<br/>Typewriter RCA reasoning]
        TP[Timeline Panel<br/>Building timeline]
        RP[Report Panel<br/>PDF download]
        INVP --> LP
        INVP --> AP
        INVP --> TP
        INVP --> RP
    end

    subgraph BackendBox["⚙️ Backend (FastAPI + Python + asyncio)"]
        API["REST API<br/>POST /investigate/{id}/start<br/>GET /incidents<br/>GET /reports/{id}/pdf"]
        SSE["SSE Stream Endpoint<br/>GET /investigate/{id}/stream<br/>asyncio.Queue → EventSource"]
        ORCH[Agent Orchestrator<br/>Sequential pipeline]

        subgraph Pipeline["🤖 4-Agent Pipeline"]
            A1["[1] Investigation Agent<br/>Queries Splunk MCP<br/>Collects logs + metrics"]
            A2["[2] Timeline Agent<br/>Chronological ordering<br/>Causation clustering"]
            A3["[3] Root Cause Agent ⭐<br/>LLM streaming reasoning<br/>Confidence scoring"]
            A4["[4] Report Agent<br/>Synthesis + PDF<br/>Executive summary"]
            A1 -->|InvestigationOutput| A2
            A2 -->|TimelineOutput| A3
            A3 -->|RCAOutput| A4
        end

        subgraph Data["💾 Data Layer (SQLite)"]
            DB[(incidents<br/>investigations<br/>agent_outputs)]
            PDF[PDF Generator<br/>ReportLab]
        end

        ORCH --> A1
        A4 --> PDF
        A1 & A2 & A3 & A4 -->|agent_outputs| DB
    end

    subgraph External["🔌 External Services"]
        SMCP["Splunk MCP Server<br/>stdio transport<br/>search tool"]
        SP[(Splunk Enterprise<br/>Log index)]
        SIM["Log Simulator<br/>DB pool exhaustion<br/>24 realistic events"]
        LLM["Anthropic API<br/>claude-sonnet-4-6<br/>Streaming tokens"]
    end

    DASH -->|GET /api/incidents| API
    INVP -->|POST /start| API
    INVP -->|EventSource| SSE
    API -->|start task| ORCH
    SSE -->|read queue| ORCH

    A1 -->|SPLUNK_MODE=live| SMCP
    SMCP --> SP
    A1 -->|SPLUNK_MODE=simulator| SIM

    A3 -->|stream=True| LLM

    LP -. "SSE: step chunks" .-> A1
    AP -. "SSE: LLM tokens" .-> A3
    TP -. "SSE: timeline steps" .-> A2
    RP -. "SSE: done + metadata" .-> A4
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant Judge as Browser (Judge)
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant Q as asyncio.Queue
    participant INV as Investigation Agent
    participant TL as Timeline Agent
    participant RCA as Root Cause Agent
    participant RPT as Report Agent
    participant MCP as Splunk MCP / Simulator
    participant LLM as Anthropic LLM

    Judge->>FE: Click "Start AI Investigation"
    FE->>API: POST /api/investigate/{id}/start
    API->>Q: Create asyncio.Queue
    API->>API: BackgroundTask → run_agent_pipeline()
    API-->>FE: {investigation_id, stream_url}

    FE->>API: GET /api/investigate/{id}/stream (EventSource)
    Note over FE,API: SSE connection open

    API->>INV: run_investigation()
    INV->>MCP: query_logs(service, start_time)
    MCP-->>INV: 24 log events (5 services)
    INV->>Q: SSE step chunks (log progress)
    INV-->>API: InvestigationOutput

    API->>TL: run_timeline()
    TL->>Q: SSE step chunks (timeline events, one by one)
    TL-->>API: TimelineOutput

    API->>RCA: run_rca()
    RCA->>LLM: messages.stream() — reasoning prompt
    LLM-->>RCA: token stream
    RCA->>Q: SSE token chunks (typewriter effect)
    RCA-->>API: RCAOutput {root_cause, confidence_pct, evidence}

    API->>RPT: run_report()
    RPT->>RPT: generate_pdf() via ReportLab
    RPT->>Q: SSE step + metadata {pdf_path}
    RPT-->>API: ReportOutput

    Q->>Q: Push {"type": "done"}
    API-->>FE: SSE stream closes

    FE->>Judge: Show root cause + confidence bar
    Judge->>FE: Click "Download PDF Report"
    FE->>API: GET /api/reports/{id}/pdf
    API-->>Judge: PDF file download
```

---

## Agent Data Contracts

```mermaid
classDiagram
    class InvestigationOutput {
        +str incident_id
        +list~LogEvent~ relevant_logs
        +list~str~ services_affected
        +int event_count
    }

    class TimelineOutput {
        +str incident_id
        +list~TimelineEvent~ events
    }

    class RCAOutput {
        +str incident_id
        +str root_cause
        +float confidence_pct
        +list~str~ evidence
        +list~str~ contributing_factors
        +str severity
    }

    class ReportOutput {
        +str incident_id
        +str summary
        +str severity
        +str pdf_path
        +str markdown
    }

    class LogEvent {
        +str timestamp
        +str service
        +str level
        +str message
    }

    class TimelineEvent {
        +str timestamp
        +str service
        +str event
        +str severity
    }

    InvestigationOutput --> LogEvent : contains
    TimelineOutput --> TimelineEvent : contains
    InvestigationOutput --> TimelineOutput : feeds
    TimelineOutput --> RCAOutput : feeds
    RCAOutput --> ReportOutput : feeds
```

---

## Component Summary

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 18 + Vite + TailwindCSS | Dark SOC-style dashboard, SSE streaming UI |
| Backend | FastAPI + uvicorn | REST API, SSE stream, BackgroundTasks |
| Orchestrator | Python asyncio | Sequential 4-agent pipeline via asyncio.Queue |
| Agent 1 | Python + Splunk MCP SDK | Log collection from Splunk or simulator |
| Agent 2 | Python | Timeline construction from raw logs |
| Agent 3 | Anthropic claude-sonnet-4-6 | Streaming root cause analysis + confidence |
| Agent 4 | Python + ReportLab | PDF report generation |
| Splunk MCP | stdio transport | Tool-based Splunk Enterprise integration |
| Log Simulator | Python | Realistic 24-event DB exhaustion scenario |
| Database | SQLite + SQLAlchemy | Incidents, investigations, agent outputs |
| LLM | claude-sonnet-4-6 | Root cause reasoning with token streaming |

---

## Key Design Decisions

- **SSE over WebSockets** — EventSource is native to browsers, requires no library, and is one-directional (server → client), which is all that's needed for streaming agent progress.
- **asyncio.Queue as handoff** — `POST /start` creates the queue and launches the pipeline as a BackgroundTask. `GET /stream` reads from the same queue. No shared mutable state, no polling.
- **Plain asyncio over LangGraph** — 4 sequential agents with no branching need no graph library. Each agent `await`s the prior one's output and pushes chunks to the queue directly.
- **SQLite over PostgreSQL** — Zero setup, zero ops overhead, sufficient for all demo traffic. Swap to PostgreSQL in production by changing `DATABASE_URL`.
- **Simulator as first-class citizen** — `SPLUNK_MODE=simulator` is the default. The demo works identically whether Splunk Enterprise is present or not. The simulator generates realistic correlated logs that the AI cannot distinguish from real ones.
