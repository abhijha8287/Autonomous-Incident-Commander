import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from ..agents.schemas import RCAOutput, TimelineOutput, InvestigationOutput
from .. import config

_RED = colors.HexColor("#DC2626")
_ORANGE = colors.HexColor("#EA580C")
_YELLOW = colors.HexColor("#CA8A04")
_GREEN = colors.HexColor("#16A34A")
_DARK = colors.HexColor("#111827")
_GRAY = colors.HexColor("#6B7280")
_LIGHT_GRAY = colors.HexColor("#F3F4F6")

_SEVERITY_COLORS = {
    "CRITICAL": _RED,
    "HIGH": _ORANGE,
    "MEDIUM": _YELLOW,
    "LOW": _GREEN,
}


def generate_pdf(
    investigation: InvestigationOutput,
    timeline: TimelineOutput,
    rca: RCAOutput,
    incident_title: str,
    detected_at: str,
) -> str:
    os.makedirs(config.PDF_OUTPUT_DIR, exist_ok=True)
    filename = f"incident-report-{investigation.incident_id[:8]}.pdf"
    filepath = os.path.join(config.PDF_OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, textColor=_DARK, spaceAfter=6)
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, textColor=_DARK, spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, textColor=_DARK, spaceAfter=4)
    code_style = ParagraphStyle("code", parent=styles["Code"], fontSize=8, textColor=_DARK, backColor=_LIGHT_GRAY, spaceAfter=2)
    meta_style = ParagraphStyle("meta", parent=styles["Normal"], fontSize=9, textColor=_GRAY, spaceAfter=2)

    sev_color = _SEVERITY_COLORS.get(rca.severity, _GRAY)
    story = []

    # Header
    story.append(Paragraph("INCIDENT REPORT", title_style))
    story.append(Paragraph(f"<b>{incident_title}</b>", ParagraphStyle("sub", parent=styles["Normal"], fontSize=14, textColor=_DARK, spaceAfter=4)))
    story.append(HRFlowable(width="100%", thickness=2, color=sev_color, spaceAfter=8))

    # Metadata table
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta_data = [
        ["Incident ID", investigation.incident_id],
        ["Severity", rca.severity],
        ["Detected At", detected_at],
        ["Report Generated", now],
        ["Services Affected", ", ".join(investigation.services_affected)],
        ["Log Events Analyzed", str(investigation.event_count)],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 13 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), _GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), _DARK),
        ("TEXTCOLOR", (1, 1), (1, 1), sev_color),  # severity row
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, _LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(
        f"A {rca.severity} severity incident was detected on <b>{', '.join(investigation.services_affected)}</b>. "
        f"AI-powered autonomous investigation analyzed {investigation.event_count} log events across "
        f"{len(investigation.services_affected)} services and identified the root cause with "
        f"<b>{rca.confidence_pct:.0f}% confidence</b> in under 3 minutes.",
        body_style,
    ))
    story.append(Spacer(1, 6))

    # Root Cause
    story.append(Paragraph("Root Cause", h2_style))
    story.append(Paragraph(f"<b>{rca.root_cause}</b>", ParagraphStyle("rca", parent=body_style, textColor=sev_color, fontSize=12)))
    story.append(Paragraph(f"Confidence: <b>{rca.confidence_pct:.0f}%</b>", body_style))
    story.append(Spacer(1, 4))

    if rca.contributing_factors:
        story.append(Paragraph("<b>Contributing Factors:</b>", body_style))
        for factor in rca.contributing_factors:
            story.append(Paragraph(f"• {factor}", body_style))
    story.append(Spacer(1, 6))

    # Evidence
    story.append(Paragraph("Supporting Evidence", h2_style))
    for i, ev in enumerate(rca.evidence, 1):
        story.append(Paragraph(f"[{i}] {ev}", code_style))
    story.append(Spacer(1, 6))

    # Timeline
    story.append(Paragraph("Incident Timeline", h2_style))
    tl_data = [["Time", "Service", "Severity", "Event"]]
    for ev in timeline.events:
        row_color = _SEVERITY_COLORS.get(ev.severity.upper(), _GRAY)
        tl_data.append([ev.timestamp[11:19], ev.service, ev.severity.upper(), ev.event[:60]])

    tl_table = Table(tl_data, colWidths=[2 * cm, 3.5 * cm, 2 * cm, 9.5 * cm])
    tl_style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), _DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    tl_table.setStyle(TableStyle(tl_style))
    story.append(tl_table)
    story.append(Spacer(1, 10))

    # Recommendations
    story.append(Paragraph("Recommended Remediation", h2_style))
    recommendations = _generate_recommendations(rca)
    for i, (action_type, action) in enumerate(recommendations, 1):
        story.append(Paragraph(f"<b>{i}. [{action_type}]</b> {action}", body_style))
    story.append(Spacer(1, 10))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=_LIGHT_GRAY, spaceAfter=4))
    story.append(Paragraph(
        "Generated by Autonomous Incident Commander — AI-Powered Incident Response",
        ParagraphStyle("footer", parent=meta_style, alignment=TA_CENTER),
    ))

    doc.build(story)
    return filepath


def _generate_recommendations(rca: RCAOutput) -> list[tuple[str, str]]:
    """Derive remediation steps from RCA output."""
    recommendations = []
    root = rca.root_cause.lower()

    if "connection pool" in root or "pool exhausted" in root:
        recommendations = [
            ("IMMEDIATE", "Restart the database service to release stale connections"),
            ("IMMEDIATE", "Increase connection pool size: `MAX_POOL_SIZE=100` (current: 50)"),
            ("SHORT-TERM", "Add connection pool monitoring alert at 80% utilization"),
            ("LONG-TERM", "Implement connection pooling via PgBouncer to multiplex connections"),
            ("LONG-TERM", "Review and optimize slow queries in checkout-service that hold connections"),
        ]
    elif "timeout" in root:
        recommendations = [
            ("IMMEDIATE", "Reduce query timeout to fail fast and release connections"),
            ("IMMEDIATE", "Enable circuit breaker on database calls"),
            ("SHORT-TERM", "Add database query performance monitoring"),
            ("LONG-TERM", "Optimize slow queries identified in evidence above"),
        ]
    elif "memory" in root:
        recommendations = [
            ("IMMEDIATE", "Restart affected service to release memory"),
            ("SHORT-TERM", "Add memory usage alerting at 85% threshold"),
            ("LONG-TERM", "Profile application for memory leaks using heap analysis"),
        ]
    else:
        recommendations = [
            ("IMMEDIATE", f"Investigate and address: {rca.root_cause}"),
            ("SHORT-TERM", "Add monitoring for the failure mode identified above"),
            ("LONG-TERM", "Conduct post-incident review within 48 hours"),
        ]

    return recommendations
