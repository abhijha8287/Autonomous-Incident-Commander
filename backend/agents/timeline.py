import asyncio
from ..agents.schemas import InvestigationOutput, TimelineEvent, TimelineOutput, SSEChunk

_LEVEL_TO_SEVERITY = {
    "INFO": "low",
    "WARNING": "medium",
    "ERROR": "high",
    "CRITICAL": "critical",
    "ALERT": "critical",
}

# Only surface events that represent meaningful state changes
_SIGNIFICANCE_KEYWORDS = [
    "exhausted", "timeout", "failed", "critical", "error", "circuit breaker",
    "halted", "breach", "queue depth", "retrying", "unavailable", "alert",
    "initialized", "started", "removing", "health check",
]


def _is_significant(msg: str) -> bool:
    lower = msg.lower()
    return any(kw in lower for kw in _SIGNIFICANCE_KEYWORDS)


async def run_timeline(investigation: InvestigationOutput, queue: asyncio.Queue) -> TimelineOutput:
    await queue.put(SSEChunk(
        agent="timeline",
        type="step",
        content="Building incident timeline..."
    ).model_dump())

    significant_events = [
        log for log in investigation.relevant_logs
        if log.level in ("WARNING", "ERROR", "CRITICAL", "ALERT") or _is_significant(log.message)
    ]

    timeline_events: list[TimelineEvent] = []
    seen_summaries: set[str] = set()

    for log in sorted(significant_events, key=lambda x: x.timestamp):
        # Produce a short human-readable summary
        msg = log.message
        if len(msg) > 80:
            msg = msg[:77] + "..."

        summary = f"[{log.service}] {msg}"
        if summary in seen_summaries:
            continue
        seen_summaries.add(summary)

        event = TimelineEvent(
            timestamp=log.timestamp,
            service=log.service,
            event=msg,
            severity=_LEVEL_TO_SEVERITY.get(log.level, "low"),
        )
        timeline_events.append(event)

        await queue.put(SSEChunk(
            agent="timeline",
            type="step",
            content=f"● {log.timestamp[11:19]} — {event.severity.upper()} — {log.service}: {msg[:60]}"
        ).model_dump())

        # Small delay so timeline items appear one by one in the UI
        await asyncio.sleep(0.1)

    output = TimelineOutput(incident_id=investigation.incident_id, events=timeline_events)

    await queue.put(SSEChunk(
        agent="timeline",
        type="step",
        content=f"✓ Timeline built: {len(timeline_events)} significant events identified."
    ).model_dump())

    return output
