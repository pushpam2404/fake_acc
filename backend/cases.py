"""
backend/cases.py
================
Central Agency Escalation & Reporting — Case Management Module.

Provides:
  - SQLite persistence via SQLAlchemy (cases.db, auto-created on startup)
  - Case model with status workflow: FLAGGED → UNDER_REVIEW → REPORT_SENT → TAKEDOWN_CONFIRMED
  - FastAPI router with 6 endpoints (list, summary, detail, create, status-update, report)

IT Rules 2021 compliance: escalation simulates intermediary due-diligence takedown
pipeline under Rule 3(1)(d), 72-hour compliance window.
"""

import json
import uuid
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.schemas import CaseCreate, CaseOut, CaseStatusUpdate

# ---------------------------------------------------------------------------
# Database setup — SQLite file lives next to this file (backend/cases.db)
# ---------------------------------------------------------------------------

_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DB_DIR, "cases.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Status transition graph — forward-only, no skipping, no backtracking
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, str] = {
    "FLAGGED": "UNDER_REVIEW",
    "UNDER_REVIEW": "REPORT_SENT",
    "REPORT_SENT": "TAKEDOWN_CONFIRMED",
}

STATUS_ORDER = ["FLAGGED", "UNDER_REVIEW", "REPORT_SENT", "TAKEDOWN_CONFIRMED"]

# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False)        # "twitter" | "meta"
    handle = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    classification = Column(String, nullable=False)  # "FAKE" | "SUSPICIOUS"
    reasons = Column(Text, nullable=False, default="[]")  # JSON-serialised list[str]
    status = Column(String, nullable=False, default="FLAGGED")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reviewed_by = Column(String, nullable=True, default="Unassigned")
    report_generated = Column(Boolean, nullable=False, default=False)


def create_tables() -> None:
    """Create DB tables if they don't exist yet (idempotent)."""
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Dependency — yields a DB session and closes it after the request
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(case: Case) -> dict:
    """Convert ORM Case to a plain dict, safely casting numpy-origin floats."""
    return {
        "id": case.id,
        "platform": case.platform,
        "handle": case.handle,
        "risk_score": float(case.risk_score),          # sanitize numpy float
        "classification": case.classification,
        "reasons": json.loads(case.reasons) if isinstance(case.reasons, str) else case.reasons,
        "status": case.status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "reviewed_by": case.reviewed_by,
        "report_generated": bool(case.report_generated),
    }


def _build_evidence_summary(reasons: list[str]) -> str:
    """Derive a concise evidence summary from the SHAP reasons list."""
    if not reasons:
        return "No specific forensic indicators recorded."
    bullet_lines = "\n".join(f"  • {r}" for r in reasons[:6])
    return (
        f"Automated forensic analysis identified {len(reasons)} behavioural indicator(s):\n"
        f"{bullet_lines}"
        + ("\n  (and additional indicators)" if len(reasons) > 6 else "")
    )


# ---------------------------------------------------------------------------
# Router — NOTE: /cases/summary MUST be declared before /cases/{id}
# to prevent FastAPI treating the literal "summary" as a UUID path parameter.
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseOut)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    """
    Create a new escalation case.
    Only FAKE or SUSPICIOUS classifications are accepted — REAL accounts
    are never escalated (guards the case table from clutter).
    """
    if payload.classification == "REAL":
        raise HTTPException(
            status_code=400,
            detail="Only FAKE or SUSPICIOUS accounts can be escalated."
        )

    case = Case(
        id=str(uuid.uuid4()),
        platform=payload.platform,
        handle=payload.handle,
        risk_score=float(payload.risk_score),   # sanitize numpy origin values
        classification=payload.classification,
        reasons=json.dumps(payload.reasons),
        status="FLAGGED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        reviewed_by="Unassigned",
        report_generated=False,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _serialize(case)


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db)):
    """Return all cases ordered by creation date, newest first."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [_serialize(c) for c in cases]


# CRITICAL: /cases/summary must come before /cases/{id}
@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """
    Dashboard statistics:
      - total_flagged: total cases in the system
      - pending_review: FLAGGED + UNDER_REVIEW
      - reports_sent: REPORT_SENT count
      - takedowns_confirmed: TAKEDOWN_CONFIRMED count
      - avg_time_to_takedown_hours: mean hours from created_at → updated_at
        for TAKEDOWN_CONFIRMED cases only (null if none exist)
    """
    all_cases = db.query(Case).all()

    total_flagged = len(all_cases)
    pending_review = sum(1 for c in all_cases if c.status in ("FLAGGED", "UNDER_REVIEW"))
    reports_sent = sum(1 for c in all_cases if c.status == "REPORT_SENT")
    takedowns_confirmed = sum(1 for c in all_cases if c.status == "TAKEDOWN_CONFIRMED")

    confirmed = [c for c in all_cases if c.status == "TAKEDOWN_CONFIRMED"
                 and c.created_at and c.updated_at]
    if confirmed:
        total_hours = sum(
            (c.updated_at - c.created_at).total_seconds() / 3600
            for c in confirmed
        )
        avg_time = round(total_hours / len(confirmed), 2)
    else:
        avg_time = None

    return {
        "total_flagged": total_flagged,
        "pending_review": pending_review,
        "reports_sent": reports_sent,
        "takedowns_confirmed": takedowns_confirmed,
        "avg_time_to_takedown_hours": avg_time,
    }


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Retrieve a single case by ID."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return _serialize(case)


@router.patch("/{case_id}/status", response_model=CaseOut)
def update_case_status(case_id: str, payload: CaseStatusUpdate, db: Session = Depends(get_db)):
    """
    Advance a case to its next legal status.
    Transition rules (forward-only, no skipping):
      FLAGGED → UNDER_REVIEW → REPORT_SENT → TAKEDOWN_CONFIRMED
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    new_status = payload.status.upper()

    # Validate the requested transition
    expected_next = VALID_TRANSITIONS.get(case.status)
    if expected_next is None:
        raise HTTPException(
            status_code=400,
            detail=f"Case is already at terminal status '{case.status}'."
        )
    if new_status != expected_next:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid transition: '{case.status}' → '{new_status}'. "
                f"Legal next status is '{expected_next}'."
            )
        )

    case.status = new_status
    case.updated_at = datetime.now(timezone.utc)
    if payload.reviewed_by:
        case.reviewed_by = payload.reviewed_by

    db.commit()
    db.refresh(case)
    return _serialize(case)


@router.get("/{case_id}/report")
def get_case_report(case_id: str, db: Session = Depends(get_db)):
    """
    Generate (or re-fetch) the structured JSON report for a case.
    Sets report_generated=True as a side-effect.
    Compliant with IT Rules 2021, Rule 3(1)(d).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    reasons = json.loads(case.reasons) if isinstance(case.reasons, str) else case.reasons

    # Mark as report generated
    case.report_generated = True
    case.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "case_id": case.id,
        "platform": case.platform,
        "handle": case.handle,
        "risk_score": float(case.risk_score),
        "classification": case.classification,
        "reasons": reasons,
        "evidence_summary": _build_evidence_summary(reasons),
        "legal_basis": (
            "IT Rules 2021, Rule 3(1)(d) — Intermediary Due Diligence & Grievance Redressal: "
            "Significant Social Media Intermediaries (SSMIs) are required to acknowledge takedown "
            "notices within 24 hours and act upon them within 72 hours of receiving a government "
            "or competent authority order. Failure to comply exposes the platform to loss of safe "
            "harbour immunity under Section 79 of the Information Technology Act, 2000."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": case.status,
    }
