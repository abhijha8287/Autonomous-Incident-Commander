import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import Incident, Investigation
from .agents.orchestrator import run_agent_pipeline

# In-memory queue registry — keyed by investigation_id
_queues: dict[str, asyncio.Queue] = {}

app = FastAPI(title="Autonomous Incident Commander", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    _seed_demo_incident()


def _seed_demo_incident():
    """Pre-seed a realistic incident so the demo starts immediately."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(Incident).count() == 0:
            detected_at = datetime.now(timezone.utc).isoformat()
            incident = Incident(
                id=str(uuid.uuid4()),
                service="checkout-service",
                title="Critical Error Rate — checkout-service",
                severity="CRITICAL",
                status="ACTIVE",
                detected_at=detected_at,
            )
            db.add(incident)
            db.commit()
    finally:
        db.close()


# ─── Incidents ───────────────────────────────────────────────────────────────

@app.get("/api/incidents")
def list_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.detected_at.desc()).all()
    return [
        {
            "id": inc.id,
            "service": inc.service,
            "title": inc.title,
            "severity": inc.severity,
            "status": inc.status,
            "detected_at": inc.detected_at,
            "resolved_at": inc.resolved_at,
        }
        for inc in incidents
    ]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter_by(id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    investigations = [
        {
            "id": inv.id,
            "started_at": inv.started_at,
            "completed_at": inv.completed_at,
            "root_cause": inv.root_cause,
            "confidence": inv.confidence,
            "pdf_path": inv.pdf_path,
            "status": inv.status,
        }
        for inv in inc.investigations
    ]

    return {
        "id": inc.id,
        "service": inc.service,
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "detected_at": inc.detected_at,
        "resolved_at": inc.resolved_at,
        "investigations": investigations,
    }


# ─── Investigation: Start ────────────────────────────────────────────────────

@app.post("/api/investigate/{incident_id}/start")
def start_investigation(
    incident_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter_by(id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Create investigation record
    investigation_id = str(uuid.uuid4())
    investigation = Investigation(
        id=investigation_id,
        incident_id=incident_id,
        status="RUNNING",
    )
    db.add(investigation)
    db.commit()

    # Create queue for this investigation
    q: asyncio.Queue = asyncio.Queue()
    _queues[investigation_id] = q

    background_tasks.add_task(run_agent_pipeline, incident_id, investigation_id, q)

    return {
        "incident_id": incident_id,
        "investigation_id": investigation_id,
        "stream_url": f"/api/investigate/{investigation_id}/stream",
    }


# ─── Investigation: Stream ───────────────────────────────────────────────────

@app.get("/api/investigate/{investigation_id}/stream")
async def stream_investigation(investigation_id: str):
    async def event_generator():
        q = _queues.get(investigation_id)
        if q is None:
            yield 'data: {"agent":"orchestrator","type":"error","content":"Investigation not started or already complete"}\n\n'
            yield 'data: {"type":"done"}\n\n'
            return

        while True:
            try:
                chunk = await asyncio.wait_for(q.get(), timeout=60.0)
            except asyncio.TimeoutError:
                yield 'data: {"agent":"orchestrator","type":"error","content":"Stream timeout"}\n\n'
                break

            yield f"data: {json.dumps(chunk)}\n\n"

            if chunk.get("type") == "done":
                _queues.pop(investigation_id, None)
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── Investigation: Results ──────────────────────────────────────────────────

@app.get("/api/investigate/{investigation_id}/results")
def get_investigation_results(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter_by(id=investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    outputs = {ao.agent_name: json.loads(ao.output_json) for ao in inv.agent_outputs}

    return {
        "investigation_id": inv.id,
        "incident_id": inv.incident_id,
        "status": inv.status,
        "root_cause": inv.root_cause,
        "confidence": inv.confidence,
        "pdf_path": inv.pdf_path,
        "agent_outputs": outputs,
    }


# ─── PDF Download ────────────────────────────────────────────────────────────

@app.get("/api/reports/{investigation_id}/pdf")
def download_pdf(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter_by(id=investigation_id).first()
    if not inv or not inv.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
    if not os.path.exists(inv.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file missing from disk")
    return FileResponse(
        inv.pdf_path,
        media_type="application/pdf",
        filename=f"incident-report-{investigation_id[:8]}.pdf",
    )


# ─── Trigger new incident (demo helper) ──────────────────────────────────────

class TriggerRequest(BaseModel):
    service: str = "checkout-service"
    title: str = "Critical Error Rate — checkout-service"


@app.post("/api/incidents/trigger")
def trigger_incident(req: TriggerRequest, db: Session = Depends(get_db)):
    incident = Incident(
        id=str(uuid.uuid4()),
        service=req.service,
        title=req.title,
        severity="UNKNOWN",
        status="ACTIVE",
        detected_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(incident)
    db.commit()
    return {"id": incident.id, "title": incident.title, "status": "ACTIVE"}
