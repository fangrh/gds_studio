"""Schemas for sync API endpoints."""
from datetime import datetime

from pydantic import BaseModel


class SyncPullResponse(BaseModel):
    issues: list[dict]
    wiki_updates: list[dict]
    server_timestamp: str


class SyncPushResponse(BaseModel):
    accepted_scripts: list[str]
    accepted_gds: list[str]
    replied_issues: list[int]
    updated_wiki: list[str]
    server_timestamp: str
