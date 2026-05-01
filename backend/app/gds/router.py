import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GdsScript, GdsBuild, GdsCell, GdsElement
from app.gds.schemas import (
    ScriptCreate, ScriptResponse, BuildCreate, BuildResponse,
    CellResponse, ElementResponse,
)
from app.gds.parser import parse_gds

router = APIRouter(prefix="/api/gds", tags=["gds"])

GDS_DIR = os.environ.get("GDS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "gds"))


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


@router.get("/files")
def list_gds_files():
    """List available GDS files in the GDS directory."""
    import glob
    pattern = os.path.join(GDS_DIR, "*.gds")
    files = []
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)
        size = os.path.getsize(path)
        files.append({"name": name, "size": size})
    return files


@router.get("/geometry/{gds_name:path}")
def get_geometry(gds_name: str):
    """Parse a GDS file and return polygon geometry for rendering."""
    import klayout.db as db

    safe_name = os.path.basename(gds_name)
    gds_path = os.path.realpath(os.path.join(GDS_DIR, safe_name))
    if not gds_path.startswith(os.path.realpath(GDS_DIR)):
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(gds_path):
        raise HTTPException(404, f"GDS file not found: {safe_name}")

    layout = db.Layout()
    layout.read(gds_path)

    top_cell = layout.top_cell()
    if top_cell is None:
        raise HTTPException(400, "No top cell found")

    # Flatten into a single cell to get all geometry with transforms applied
    flat = layout.create_cell("flat")
    flat.copy_tree(top_cell)
    flat.flatten(False)

    layers = {}
    for li in range(layout.layers()):
        if layout.is_valid_layer(li) and not flat.shapes(li).is_empty():
            info = layout.get_info(li)
            key = f"{info.layer}/{info.datatype}"
            layers[key] = {"layer": info.layer, "datatype": info.datatype}

    elements = []
    for li in range(layout.layers()):
        if not layout.is_valid_layer(li):
            continue
        info = layout.get_info(li)
        layer_key = f"{info.layer}/{info.datatype}"
        shapes = flat.shapes(li)
        if shapes.is_empty():
            continue
        for shape in shapes.each():
            verts = []
            if shape.is_polygon():
                poly = shape.polygon
                for p in poly.each_point_hull():
                    verts.append([round(p.x * layout.dbu, 6), round(p.y * layout.dbu, 6)])
            elif shape.is_box():
                box = shape.dbbox()
                verts = [
                    [box.left, box.bottom], [box.right, box.bottom],
                    [box.right, box.top], [box.left, box.top],
                ]
            if verts:
                elements.append({
                    "type": "polygon",
                    "layer": layer_key,
                    "vertices": verts,
                })

    bbox = flat.dbbox()
    layout.delete_cell(flat.cell_index())

    return {
        "name": top_cell.name,
        "bbox": {
            "left": bbox.left, "bottom": bbox.bottom,
            "right": bbox.right, "top": bbox.top,
        },
        "layers": layers,
        "elements": elements,
    }
