from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WikiPageCreate(BaseModel):
    title: str
    slug: str
    body: str = ""
    category: str = "general"
    tags: list[str] = []
    project_id: Optional[int] = None


class WikiPageUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None


class WikiPageResponse(BaseModel):
    id: int
    title: str
    slug: str
    body: Optional[str] = None
    category: str
    tags: list = []
    version: int
    last_editor_type: str
    last_editor_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WikiPageListResponse(BaseModel):
    id: int
    title: str
    slug: str
    category: str
    tags: list = []
    version: int
    project_id: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
