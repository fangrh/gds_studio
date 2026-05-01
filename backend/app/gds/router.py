from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GdsScript, GdsBuild, GdsCell, GdsElement
from app.gds.schemas import (
    ScriptCreate, ScriptResponse, BuildCreate, BuildResponse,
    CellResponse, ElementResponse,
)

router = APIRouter(prefix="/api/gds", tags=["gds"])


@router.get("/scripts", response_model=list[ScriptResponse])
def list_scripts(db: Session = Depends(get_db)):
    return db.query(GdsScript).all()


@router.post("/scripts", response_model=ScriptResponse, status_code=201)
def create_script(data: ScriptCreate, db: Session = Depends(get_db)):
    script = GdsScript(**data.model_dump())
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.get("/scripts/{script_id}", response_model=ScriptResponse)
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(GdsScript).filter(GdsScript.id == script_id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    return script


@router.get("/scripts/{script_id}/builds", response_model=list[BuildResponse])
def list_builds(script_id: int, db: Session = Depends(get_db)):
    return db.query(GdsBuild).filter(GdsBuild.script_id == script_id).all()


@router.post("/builds", response_model=BuildResponse, status_code=201)
def create_build(data: BuildCreate, db: Session = Depends(get_db)):
    script = db.query(GdsScript).filter(GdsScript.id == data.script_id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    build = GdsBuild(**data.model_dump())
    db.add(build)
    db.commit()
    db.refresh(build)
    return build


@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(build_id: int, db: Session = Depends(get_db)):
    build = db.query(GdsBuild).filter(GdsBuild.id == build_id).first()
    if not build:
        raise HTTPException(404, "Build not found")
    return build


@router.get("/builds/{build_id}/cells", response_model=list[CellResponse])
def list_cells(build_id: int, db: Session = Depends(get_db)):
    return db.query(GdsCell).filter(GdsCell.build_id == build_id).all()


@router.get("/cells/{cell_id}/elements", response_model=list[ElementResponse])
def list_elements(cell_id: int, db: Session = Depends(get_db)):
    return db.query(GdsElement).filter(GdsElement.cell_id == cell_id).all()
