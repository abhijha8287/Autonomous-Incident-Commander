from pydantic import BaseModel
from typing import Optional


class LogEvent(BaseModel):
    timestamp: str
    service: str
    level: str   # INFO | WARNING | ERROR | CRITICAL | ALERT
    message: str


class InvestigationOutput(BaseModel):
    incident_id: str
    relevant_logs: list[LogEvent]
    services_affected: list[str]
    event_count: int


class TimelineEvent(BaseModel):
    timestamp: str
    service: str
    event: str       # human-readable summary
    severity: str    # low | medium | high | critical


class TimelineOutput(BaseModel):
    incident_id: str
    events: list[TimelineEvent]


class RCAOutput(BaseModel):
    incident_id: str
    root_cause: str
    confidence_pct: float            # 0.0–100.0, genuine LLM output
    evidence: list[str]              # quoted log lines
    contributing_factors: list[str]
    severity: str                    # derived from confidence_pct


class ReportOutput(BaseModel):
    incident_id: str
    summary: str
    severity: str
    pdf_path: str
    markdown: str


class SSEChunk(BaseModel):
    agent: str
    type: str        # "step" | "token" | "error" | "done"
    content: str
    metadata: Optional[dict] = None
