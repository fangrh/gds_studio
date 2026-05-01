"""Schemas for project CRUD endpoints."""
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    token: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    issue_count: int = 0
    wiki_count: int = 0
    script_count: int = 0

    model_config = {"from_attributes": True}
