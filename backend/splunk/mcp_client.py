"""
Splunk MCP client with transparent simulator fallback.

Set SPLUNK_MODE=live to use real Splunk Enterprise via MCP.
Set SPLUNK_MODE=simulator (default) to use the built-in log generator.

Day 0 checklist before switching to "live":
  - Confirm Splunk MCP Server version
  - Run session.list_tools() and verify tool name (likely "search" or "splunk_search")
  - Confirm auth method: username/password vs. token
"""
from ..agents.schemas import LogEvent
from .. import config


async def query_logs(service: str, start_time: str) -> list[LogEvent]:
    if config.SPLUNK_MODE == "simulator":
        return _simulator_fallback(service, start_time)
    try:
        return await _query_splunk_mcp(service, start_time)
    except Exception as exc:
        print(f"[splunk] MCP query failed ({exc}), falling back to simulator")
        return _simulator_fallback(service, start_time)


async def _query_splunk_mcp(service: str, start_time: str) -> list[LogEvent]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command="splunk-mcp",
        args=[
            "--host", config.SPLUNK_HOST,
            "--port", str(config.SPLUNK_PORT),
            "--username", config.SPLUNK_USERNAME,
            "--password", config.SPLUNK_PASSWORD,
        ],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Confirm available tools on Day 0: session.list_tools()
            result = await session.call_tool(
                "search",
                arguments={
                    "query": f"search index=main service={service} earliest={start_time} | head 200",
                    "max_results": 200,
                },
            )

    return _parse_mcp_result(result)


def _parse_mcp_result(result) -> list[LogEvent]:
    events = []
    raw = result.content if hasattr(result, "content") else []
    for item in raw:
        text = item.text if hasattr(item, "text") else str(item)
        parts = text.split(" ", 3)
        if len(parts) >= 4:
            events.append(LogEvent(
                timestamp=parts[0],
                service=parts[1],
                level=parts[2],
                message=parts[3],
            ))
    return events


def _simulator_fallback(service: str, start_time: str) -> list[LogEvent]:
    from ..simulator.log_generator import get_scenario_logs
    return get_scenario_logs(service, start_time)
