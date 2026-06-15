"""
Sequential agent pipeline: Investigation → Timeline → RCA → Report.
Pushes SSEChunk dicts to the provided asyncio.Queue throughout.
Ends with {"type": "done"} sentinel.
"""
import asyncio
import json
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .investigation import run_investigation
from .timeline import run_timeline
from .root_cause import run_rca
from .report import run_report
from .schemas import SSEChunk
from ..models import Investigation, AgentOutput
from ..database import SessionLocal


async def run_agent_pipeline(incident_id: str, investigation_id: str, queue: asyncio.Queue) -> None:
    db: Session = SessionLocal()
    try:
        investigation_row = db.query(Investigation).filter_by(id=investigation_id).first()
        if not investigation_row:
            await queue.put(SSEChunk(agent="orchestrator", type="error", content="Investigation record not found").model_dump())
            await queue.put({"type": "done"})
            return

        incident = investigation_row.incident
        service = incident.service
        detected_at = incident.detected_at
        title = incident.title

        # Agent 1: Investigation
        try:
            investigation_output = await run_investigation(incident_id, service, detected_at, queue)
            _save_output(db, investigation_id, "investigation", investigation_output.model_dump_json())
        except Exception as exc:
            await queue.put(SSEChunk(agent="investigation", type="error", content=str(exc)).model_dump())
            _fail_investigation(db, investigation_id)
            await queue.put({"type": "done"})
            return

        # Agent 2: Timeline
        try:
            timeline_output = await run_timeline(investigation_output, queue)
            _save_output(db, investigation_id, "timeline", timeline_output.model_dump_json())
        except Exception as exc:
            await queue.put(SSEChunk(agent="timeline", type="error", content=str(exc)).model_dump())
            _fail_investigation(db, investigation_id)
            await queue.put({"type": "done"})
            return

        # Agent 3: Root Cause Analysis
        try:
            rca_output = await run_rca(investigation_output, timeline_output, queue)
            _save_output(db, investigation_id, "root_cause", rca_output.model_dump_json())
        except Exception as exc:
            await queue.put(SSEChunk(agent="root_cause", type="error", content=str(exc)).model_dump())
            _fail_investigation(db, investigation_id)
            await queue.put({"type": "done"})
            return

        # Agent 4: Report
        try:
            report_output = await run_report(investigation_output, timeline_output, rca_output, title, detected_at, queue)
            _save_output(db, investigation_id, "report", report_output.model_dump_json())
        except Exception as exc:
            await queue.put(SSEChunk(agent="report", type="error", content=str(exc)).model_dump())
            _fail_investigation(db, investigation_id)
            await queue.put({"type": "done"})
            return

        # Update investigation row with results
        investigation_row.completed_at = datetime.now(timezone.utc).isoformat()
        investigation_row.root_cause = rca_output.root_cause
        investigation_row.confidence = rca_output.confidence_pct
        investigation_row.pdf_path = report_output.pdf_path
        investigation_row.status = "COMPLETE"

        # Update incident severity
        incident.severity = rca_output.severity
        incident.status = "INVESTIGATING"

        db.commit()

        await queue.put(SSEChunk(
            agent="orchestrator",
            type="step",
            content="All agents completed successfully.",
            metadata={
                "root_cause": rca_output.root_cause,
                "confidence_pct": rca_output.confidence_pct,
                "severity": rca_output.severity,
                "pdf_path": report_output.pdf_path,
                "investigation_id": investigation_id,
            }
        ).model_dump())

    finally:
        db.close()
        await queue.put({"type": "done"})


def _save_output(db: Session, investigation_id: str, agent_name: str, output_json: str) -> None:
    row = AgentOutput(
        investigation_id=investigation_id,
        agent_name=agent_name,
        output_json=output_json,
    )
    db.add(row)
    db.commit()


def _fail_investigation(db: Session, investigation_id: str) -> None:
    row = db.query(Investigation).filter_by(id=investigation_id).first()
    if row:
        row.status = "FAILED"
        row.completed_at = datetime.now(timezone.utc).isoformat()
        db.commit()
