from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentSessionCreate(BaseModel):
    agent_type: str  # "claude-code", "copilot", etc.
    model: str
    skill_version: Optional[str] = None


class AgentSessionResponse(BaseModel):
    id: int
    agent_type: str
    model: str
    skill_version: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    issues_processed: int
    builds_triggered: int
    status: str

    class Config:
        from_attributes = True


class AgentBuildRequest(BaseModel):
    script_id: int
    git_commit: Optional[str] = None


class AgentResolveRequest(BaseModel):
    body: Optional[str] = None


class PollIssueResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    status: str
    priority: str
    script_path: Optional[str] = None
    created_at: Optional[datetime] = None
    linked_elements: list[dict] = []
    comments: list[dict] = []
