from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IssueElementLink(BaseModel):
    gds_build_id: Optional[int] = None
    cell_name: Optional[str] = None
    element_id: Optional[int] = None
    layer: Optional[str] = None
    bbox: Optional[str] = None
    source_script_line: Optional[int] = None
    deep_link_url: Optional[str] = None

    class Config:
        from_attributes = True


class IssueElementResponse(BaseModel):
    id: int
    issue_id: int
    gds_build_id: Optional[int] = None
    cell_name: Optional[str] = None
    element_id: Optional[int] = None
    layer: Optional[str] = None
    bbox: Optional[str] = None
    source_script_line: Optional[int] = None
    deep_link_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    author_type: str
    author_id: Optional[int] = None
    body: str
    agent_model: Optional[str] = None
    agent_skill_version: Optional[str] = None
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IssueCreate(BaseModel):
    title: str
    body: str = ""
    priority: str = "normal"
    tags: list[str] = []
    script_path: Optional[str] = None
    linked_elements: list[IssueElementLink] = []


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[list[str]] = None


class IssueResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    status: str
    author_type: str
    author_id: Optional[int] = None
    priority: str
    tags: list = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    script_path: Optional[str] = None
    linked_elements: list[IssueElementResponse] = []
    comments: list[CommentResponse] = []

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    target_type: str  # "issue" or "wiki"
    target_id: int
    body: str
    author_type: str = "user"
    author_id: int = 1
    agent_model: Optional[str] = None
    agent_skill_version: Optional[str] = None
