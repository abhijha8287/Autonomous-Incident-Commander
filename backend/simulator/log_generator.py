"""
Generates realistic correlated logs for the DB connection pool exhaustion scenario.
All timestamps are relative to a configurable base time.
"""
from datetime import datetime, timezone, timedelta
from ..agents.schemas import LogEvent

# (offset_seconds, service, level, message)
_SCENARIO: list[tuple[int, str, str, str]] = [
    (0,   "database",         "INFO",     "Connection pool initialized: 0/50 active connections"),
    (30,  "checkout-service", "INFO",     "Service started, DB pool healthy"),
    (45,  "payment-service",  "INFO",     "Payment processor connected to checkout-service"),
    (60,  "database",         "INFO",     "Connection pool: 22/50 active — normal load"),
    (90,  "database",         "WARNING",  "Connection pool: 42/50 active. Utilization at 84%"),
    (105, "checkout-service", "WARNING",  "DB query latency elevated: 620ms (threshold: 500ms)"),
    (110, "database",         "WARNING",  "Connection pool: 46/50 active. High utilization detected"),
    (120, "database",         "CRITICAL", "Connection pool exhausted: 50/50. New connections queuing"),
    (125, "checkout-service", "ERROR",    "Database connection timeout after 30s on query SELECT * FROM orders"),
    (130, "checkout-service", "ERROR",    "Retrying database connection... attempt 1/3"),
    (135, "database",         "CRITICAL", "Connection wait queue depth: 23 pending requests"),
    (140, "checkout-service", "ERROR",    "Retrying database connection... attempt 2/3"),
    (145, "payment-service",  "ERROR",    "Checkout service dependency unavailable. Payment processing halted"),
    (150, "checkout-service", "ERROR",    "Retrying database connection... attempt 3/3. All retries exhausted"),
    (155, "api-gateway",      "ERROR",    "5xx rate: 18% on /api/checkout endpoint (threshold: 5%)"),
    (160, "payment-service",  "ERROR",    "Transaction ID tx-88291 failed: upstream checkout-service timeout"),
    (165, "checkout-service", "CRITICAL", "Circuit breaker OPEN on database connection pool"),
    (170, "api-gateway",      "ERROR",    "5xx rate: 31% on /api/checkout endpoint — escalating"),
    (180, "payment-service",  "CRITICAL", "Payment processing HALTED. 47 transactions failed in last 60s"),
    (190, "api-gateway",      "ERROR",    "5xx rate: 38% on /api/checkout endpoint"),
    (210, "api-gateway",      "CRITICAL", "SLA breach: /api/checkout p99 latency 47,200ms (SLA: 1,000ms)"),
    (240, "database",         "CRITICAL", "Connection wait queue depth: 67 pending requests. System degraded"),
    (270, "checkout-service", "CRITICAL", "Health check FAILING. Removing from load balancer rotation"),
    (480, "alerting",         "ALERT",    "INCIDENT FIRED: checkout-service critical error rate >30% for 5 minutes"),
]


def get_scenario_logs(service: str = "checkout-service", start_time: str | None = None) -> list[LogEvent]:
    if start_time:
        base = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    else:
        base = datetime.now(timezone.utc) - timedelta(seconds=480)

    events = []
    for offset, svc, level, msg in _SCENARIO:
        ts = (base + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
        events.append(LogEvent(timestamp=ts, service=svc, level=level, message=msg))
    return events


def get_all_scenario_services() -> list[str]:
    return list({svc for _, svc, _, _ in _SCENARIO})
