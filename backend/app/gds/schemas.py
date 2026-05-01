from pydantic import BaseModel
from typing import Optional


class ElementResponse(BaseModel):
    id: int
    element_type: str
    layer: str
    bbox: Optional[str] = None
    source_line: Optional[int] = None

    class Config:
        from_attributes = True


class CellResponse(BaseModel):
    id: int
    name: str
    cell_type: str
    bbox: Optional[str] = None
    layer_count: int
    element_count: int
    elements: list[ElementResponse] = []

    class Config:
        from_attributes = True


class BuildResponse(BaseModel):
    id: int
    script_id: int
    gds_path: str
    status: str
    build_log: Optional[str] = None
    git_commit: Optional[str] = None
    cells: list[CellResponse] = []

    class Config:
        from_attributes = True


class ScriptResponse(BaseModel):
    id: int
    path: str
    name: str
    description: Optional[str] = None
    git_commit: Optional[str] = None
    builds: list[BuildResponse] = []

    class Config:
        from_attributes = True


class ScriptCreate(BaseModel):
    path: str
    name: str
    description: str = ""


class BuildCreate(BaseModel):
    script_id: int
    gds_path: str
    git_commit: Optional[str] = None
