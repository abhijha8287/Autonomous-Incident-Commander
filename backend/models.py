import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    service: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False, default="UNKNOWN")
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    detected_at: Mapped[str] = mapped_column(String, nullable=False, default=_now)
    resolved_at: Mapped[str | None] = mapped_column(String, nullable=True)

    investigations: Mapped[list["Investigation"]] = relationship(back_populates="incident")


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(String, ForeignKey("incidents.id"), nullable=False)
    started_at: Mapped[str] = mapped_column(String, nullable=False, default=_now)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="RUNNING")

    incident: Mapped["Incident"] = relationship(back_populates="investigations")
    agent_outputs: Mapped[list["AgentOutput"]] = relationship(back_populates="investigation")


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(String, ForeignKey("investigations.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now)

    investigation: Mapped["Investigation"] = relationship(back_populates="agent_outputs")
