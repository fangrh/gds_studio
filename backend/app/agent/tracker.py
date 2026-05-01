"""Agent session lifecycle management."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import AgentSession


def utcnow():
    return datetime.now(timezone.utc)


def create_session(db: Session, agent_type: str, model: str, skill_version: str | None = None) -> AgentSession:
    session = AgentSession(
        agent_type=agent_type,
        model=model,
        skill_version=skill_version,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: Session, session_id: int, status: str = "completed"):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.ended_at = utcnow()
        session.status = status
        db.commit()


def increment_issues(db: Session, session_id: int):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.issues_processed += 1
        db.commit()


def increment_builds(db: Session, session_id: int):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.builds_triggered += 1
        db.commit()
