import asyncio
from datetime import datetime, timezone, timedelta
from ..agents.schemas import InvestigationOutput, SSEChunk
from ..splunk.mcp_client import query_logs
from ..simulator.log_generator import get_all_scenario_services


async def run_investigation(incident_id: str, service: str, detected_at: str, queue: asyncio.Queue) -> InvestigationOutput:
    await queue.put(SSEChunk(
        agent="investigation",
        type="step",
        content="Initializing investigation..."
    ).model_dump())

    # Query window: 10 minutes before the alert
    try:
        alert_time = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    except ValueError:
        alert_time = datetime.now(timezone.utc)
    start_time = (alert_time - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    await queue.put(SSEChunk(
        agent="investigation",
        type="step",
        content=f"Querying Splunk MCP for service={service} from {start_time}..."
    ).model_dump())

    logs = await query_logs(service, start_time)

    # Also pull logs from related services
    related_services = [s for s in get_all_scenario_services() if s != service]
    for svc in related_services:
        related_logs = await query_logs(svc, start_time)
        logs.extend(related_logs)

    # Deduplicate and sort by timestamp
    seen = set()
    unique_logs = []
    for log in sorted(logs, key=lambda x: x.timestamp):
        key = (log.timestamp, log.service, log.message)
        if key not in seen:
            seen.add(key)
            unique_logs.append(log)

    services_affected = list({log.service for log in unique_logs})

    await queue.put(SSEChunk(
        agent="investigation",
        type="step",
        content=f"✓ Indexed {len(unique_logs)} log events across {len(services_affected)} services: {', '.join(services_affected)}"
    ).model_dump())

    await queue.put(SSEChunk(
        agent="investigation",
        type="step",
        content="Correlating cross-service events..."
    ).model_dump())

    output = InvestigationOutput(
        incident_id=incident_id,
        relevant_logs=unique_logs,
        services_affected=services_affected,
        event_count=len(unique_logs),
    )

    await queue.put(SSEChunk(
        agent="investigation",
        type="step",
        content=f"✓ Investigation complete. {len(unique_logs)} events ready for analysis."
    ).model_dump())

    return output
