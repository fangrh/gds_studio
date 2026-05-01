"""Bearer token authentication for project-scoped API access."""
import hashlib

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Project


def verify_token(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> Project:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization[7:]
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    project = db.query(Project).filter(Project.token_hash == token_hash).first()
    if not project:
        raise HTTPException(401, "Invalid token")
    return project
