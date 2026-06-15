# Demo Guide — Autonomous Incident Commander

**Audience:** Hackathon judges, technical evaluators  
**Duration:** 4–5 minutes  
**Tagline:** "This is what happens when the machine becomes the incident commander."

---

## Pre-Demo Checklist (5 minutes before)

Run through this before judges arrive. Do not skip.

- [ ] `.env` has a valid `ANTHROPIC_API_KEY`
- [ ] Backend running: `python -m uvicorn backend.main:app --reload --port 8000`
- [ ] Frontend running: `cd frontend && npm run dev`
- [ ] http://localhost:5173 loads and shows **1 active incident** on the dashboard
- [ ] If no incident shows, click **"Trigger Demo Incident"** to seed one
- [ ] Browser zoom: 90% (fits the three-panel layout without scrolling)
- [ ] Close all other browser tabs
- [ ] Have a PDF from a prior dry run open — instant fallback if generation is slow
- [ ] `SPLUNK_MODE=simulator` in `.env` — no Splunk Enterprise required for the demo

**Dry-run count:** Run the full demo at least 3 times before judges arrive. The RCA confidence score varies per run — confirm it lands above 85% on your hardware.

---

## The Demo Script

### 00:00 — Open the Dashboard

> "This is Autonomous Incident Commander. An AI-powered incident response platform built on Splunk MCP."

Point at the dashboard:
- One active incident: **Critical Error Rate — checkout-service**
- Severity badge: **CRITICAL**
- Status: **ACTIVE**

> "An alert just fired. In a normal SRE workflow, an engineer would now open Splunk, search logs, correlate events across services, write a timeline — that takes 30 to 90 minutes. We're going to let the AI do it instead."

---

### 00:20 — Click the Incident

Click the incident row. The Investigation screen opens.

> "Three panels: live logs on the left, AI reasoning in the center, incident timeline on the right. Nothing has been queried yet. No human has looked at a single log line."

---

### 00:30 — Click "Start AI Investigation"

> "Watch the left panel."

**Left panel — logs appear:**

> "The Investigation Agent is querying Splunk MCP, pulling every log event from the affected services across the incident window — checkout-service, payment-service, the database, the API gateway."

Wait for: `✓ Indexed 24 log events across 5 services`

> "24 events. Five services. Indexed in seconds."

---

### 01:00 — Timeline Builds

Timeline items appear one by one in the right panel.

> "The Timeline Agent is now ordering those logs chronologically."

Point at events as they appear:
- `10:00 — Connection pool: 22/50 — normal`
- `10:01 — WARNING — Pool at 84% utilization`
- `10:02 — CRITICAL — Connection pool exhausted 50/50`
- `10:02 — ERROR — DB timeout after 30s`
- `10:03 — ERROR — Payment processing halted`
- `10:08 — ALERT — Incident fired`

> "You can see the cascade. The database filled up, checkout service couldn't get a connection, payments stopped, and 6 minutes later the alert fired. The AI built this without being asked."

---

### 01:30 — Root Cause Analysis

Center panel — AI reasoning tokens appear token by token (typewriter effect).

> "Now the Root Cause Agent is reasoning over the evidence."

**Let it run. Don't talk over it.** The typewriter is the wow moment.

The result card appears:

```
Root Cause Identified
Database Connection Pool Exhaustion
Confidence: 94%
████████████████████░  94%
```

> "Database Connection Pool Exhaustion. 94% confidence. The AI read the logs, found what failed first, traced the cascade, and produced a finding — in under 90 seconds."

---

### 02:15 — Evidence

> "It didn't just give us a label. It cited its evidence."

Read one aloud:
> *"`[10:02] [CRITICAL] database: Connection pool exhausted: 50/50. New connections queuing`"*

> "These are the actual log lines that led to its conclusion. This is how a senior SRE thinks."

---

### 02:30 — Remediation

> "The platform also tells you what to do."

- `[IMMEDIATE]` Restart the database service to release stale connections
- `[IMMEDIATE]` Increase connection pool size: MAX_POOL_SIZE=100 (current: 50)
- `[SHORT-TERM]` Add monitoring alert at 80% pool utilization
- `[LONG-TERM]` Implement PgBouncer for connection multiplexing

> "Immediate, short-term, long-term. Prioritized."

---

### 02:45 — PDF Report

Click **Download PDF Report**.

Show each section:
1. **Incident Summary** — ID, severity, services, events analyzed
2. **Timeline table** — timestamped, color-coded by severity
3. **Root Cause** — finding + confidence bar
4. **Evidence** — the quoted log lines
5. **Remediation** — prioritized action plan

> "This is ready to send to your VP of Engineering right now. Total time from alert to report: under 3 minutes. A human SRE takes 30 to 90."

---

### 03:30 — Close

> "Existing tools — Splunk AI Assistant, Datadog Bits AI, Dynatrace Davis — are copilots. They answer questions when you ask them. This platform acts. It's the difference between a tool that helps you investigate and a system that investigates for you."

> "This is Autonomous Incident Commander. The machine is the incident commander."

---

## Key Talking Points

**On Splunk MCP:**
> "Splunk MCP is the integration layer that lets AI agents call Splunk as a tool — the same way a human opens a search window, but autonomously and in milliseconds. Each query result flows directly into the next agent."

**On multi-agent architecture:**
> "Each agent has one job. Investigation Agent collects. Timeline Agent orders. Root Cause Agent reasons. Report Agent synthesizes. They pass typed data to each other — no hallucination leaks between steps."

**On the confidence score:**
> "The confidence percentage is a genuine LLM output — the AI reasons through the evidence and decides how certain it is. It's not hardcoded. Different log patterns produce different scores."

**On live streaming:**
> "Every output streams in real time via Server-Sent Events. You're watching the AI think — not a pre-computed result."

**On production readiness:**
> "The simulator generates realistic logs for the demo. In production, flip `SPLUNK_MODE=live` and point it at Splunk Enterprise. The agent pipeline is identical."

---

## Failure Recovery

| Problem | Fix |
|---|---|
| No incident on dashboard | Click **"Trigger Demo Incident"** |
| SSE stream stalls | Refresh Investigation page → Start again |
| AI panel shows error | Check backend terminal — usually missing `ANTHROPIC_API_KEY` |
| PDF button doesn't appear | Wait 10 seconds — report generates after RCA completes |
| Backend crashes | Re-run `uvicorn backend.main:app --port 8000` — SQLite data persists |
| Splunk MCP fails | Set `SPLUNK_MODE=simulator` in `.env`, restart backend |

**Ultimate fallback:** Open the PDF from your last dry run and walk through it. The PDF tells the complete story on its own.

---

## Scoring Alignment

| Judging Criterion | What to Show |
|---|---|
| **Splunk Integration** | Say "Splunk MCP" out loud. Show the `✓ events indexed` step. |
| **Agentic Workflow** | Name each agent as it runs: "That's the Investigation Agent... now Timeline..." |
| **AI Usage** | Let the typewriter RCA run — don't skip it. |
| **Innovation** | The copilot vs. commander framing. Say it explicitly. |
| **Business Value** | "30–90 minutes → under 3 minutes." Say this number twice. |
| **Demo Impact** | Make the judge click the PDF download themselves. |

---

## The One-Sentence Version

If a judge walks up mid-demo:

> "When an incident fires, this AI automatically investigates Splunk logs, builds the timeline, finds the root cause, and generates the incident report — no human in the loop."
