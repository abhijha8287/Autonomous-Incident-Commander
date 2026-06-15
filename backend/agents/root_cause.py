import asyncio
import json
import re
import anthropic
from ..agents.schemas import InvestigationOutput, TimelineOutput, RCAOutput, SSEChunk
from .. import config

_SEVERITY_FROM_CONFIDENCE = [
    (85.0, "CRITICAL"),
    (65.0, "HIGH"),
    (45.0, "MEDIUM"),
    (0.0,  "LOW"),
]


def _derive_severity(confidence: float) -> str:
    for threshold, label in _SEVERITY_FROM_CONFIDENCE:
        if confidence >= threshold:
            return label
    return "LOW"


def _build_prompt(investigation: InvestigationOutput, timeline: TimelineOutput) -> str:
    logs_text = "\n".join(
        f"[{e.timestamp[11:19]}] [{e.level}] {e.service}: {e.message}"
        for e in investigation.relevant_logs
    )
    timeline_text = "\n".join(
        f"  {ev.timestamp[11:19]} — {ev.severity.upper()} — {ev.service}: {ev.event}"
        for ev in timeline.events
    )
    return f"""You are a Senior Site Reliability Engineer performing root cause analysis on a production incident.

INCIDENT CONTEXT:
  Affected services: {', '.join(investigation.services_affected)}
  Total events analyzed: {investigation.event_count}

INCIDENT TIMELINE (significant events only):
{timeline_text}

FULL LOG EVIDENCE ({len(investigation.relevant_logs)} events):
{logs_text}

Analyze the logs carefully. Identify:
1. What was the ROOT CAUSE — the first thing that failed that triggered everything else?
2. What is your confidence percentage (0-100)? Be honest about uncertainty.
3. Which specific log lines are the strongest evidence for your conclusion?
4. What contributing factors made this worse?

Return ONLY valid JSON in this exact format, nothing else:
{{
  "root_cause": "concise description of the root cause",
  "confidence_pct": 94.5,
  "evidence": [
    "exact log line 1 that proves root cause",
    "exact log line 2 that proves root cause",
    "exact log line 3 that proves root cause"
  ],
  "contributing_factors": [
    "factor 1",
    "factor 2"
  ]
}}"""


async def run_rca(investigation: InvestigationOutput, timeline: TimelineOutput, queue: asyncio.Queue) -> RCAOutput:
    await queue.put(SSEChunk(
        agent="root_cause",
        type="step",
        content="Starting AI root cause analysis..."
    ).model_dump())

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = _build_prompt(investigation, timeline)

    full_response = ""

    await queue.put(SSEChunk(
        agent="root_cause",
        type="step",
        content="Reasoning over log evidence..."
    ).model_dump())

    async with client.messages.stream(
        model=config.LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put(SSEChunk(
                agent="root_cause",
                type="token",
                content=text,
            ).model_dump())

    # Parse JSON from the response
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?", "", full_response).strip()
        data = json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        # Fallback: extract what we can
        data = {
            "root_cause": full_response[:200],
            "confidence_pct": 50.0,
            "evidence": [],
            "contributing_factors": [],
        }

    confidence = float(data.get("confidence_pct", 50.0))
    output = RCAOutput(
        incident_id=investigation.incident_id,
        root_cause=data.get("root_cause", "Unknown"),
        confidence_pct=confidence,
        evidence=data.get("evidence", []),
        contributing_factors=data.get("contributing_factors", []),
        severity=_derive_severity(confidence),
    )

    await queue.put(SSEChunk(
        agent="root_cause",
        type="step",
        content=f"✓ Root cause identified: {output.root_cause} (confidence: {output.confidence_pct:.0f}%)"
    ).model_dump())

    return output
