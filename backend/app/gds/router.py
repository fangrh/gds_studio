import json
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
from app.gds.tracer import SOURCE_PROP_KEY

router = APIRouter(prefix="/api/gds", tags=["gds"])

GDS_DIR = os.environ.get("GDS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "gds"))
PROJECTS_DIR = os.environ.get("GDS_PROJECTS_DIR", "/data/projects")


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
def get_geometry(gds_name: str, db_session: Session = Depends(get_db)):
    """Parse a GDS file and return polygon geometry for rendering."""
    import klayout.db as kdb

    safe_name = os.path.basename(gds_name)
    gds_path = os.path.realpath(os.path.join(GDS_DIR, safe_name))
    if not gds_path.startswith(os.path.realpath(GDS_DIR)):
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(gds_path):
        raise HTTPException(404, f"GDS file not found: {safe_name}")

    layout = kdb.Layout()
    layout.read(gds_path)

    # Handle multiple top cells (gdsfactory creates one per component)
    top_cells = layout.top_cells()
    top_cell = top_cells[0] if top_cells else None
    if top_cell is None:
        raise HTTPException(400, "No top cell found")

    # Look up build_id from DB by matching gds_path
    build_id = None
    script_path = None
    build = db_session.query(GdsBuild).filter(
        GdsBuild.gds_path.endswith("/" + safe_name)
    ).order_by(GdsBuild.created_at.desc()).first()
    if build:
        build_id = build.id
        script_path = build.script.path if build.script else None

    # Derive script path from GDS filename if no DB record
    if not script_path:
        base_name = os.path.splitext(safe_name)[0]
        candidate = os.path.join(GDS_DIR, "..", "scripts", base_name + ".py")
        if os.path.isfile(candidate):
            script_path = os.path.relpath(candidate, os.path.join(GDS_DIR, ".."))

    # Flatten into a single cell to get all geometry with transforms applied
    flat = layout.create_cell("flat")
    flat.copy_tree(top_cell)
    flat.flatten(False)

    # Read source map from sidecar JSON file if it exists
    source_map = _load_source_map(safe_name)

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

            # Use first source map entry for all elements (whole-file mapping)
            source_line = None
            source_call = None
            if source_map:
                source_line = source_map[0].get("line")
                source_call = source_map[0].get("call")

            if verts:
                el_dict = {
                    "type": "polygon",
                    "layer": layer_key,
                    "vertices": verts,
                }
                if source_line is not None:
                    el_dict["source_line"] = source_line
                    el_dict["source_call"] = source_call
                elements.append(el_dict)

    bbox = flat.dbbox()
    layout.delete_cell(flat.cell_index())

    result = {
        "name": top_cell.name,
        "bbox": {
            "left": bbox.left, "bottom": bbox.bottom,
            "right": bbox.right, "top": bbox.top,
        },
        "layers": layers,
        "elements": elements,
    }
    if build_id is not None:
        result["build_id"] = build_id
    if script_path is not None:
        result["script_path"] = script_path
    return result


@router.get("/source")
def get_source_context(
    script_path: str = "",
    source_line: int = 0,
):
    """Return source code context around a specific line in a script.

    Used by the Code tab to show the Python code that generated a GDS element.
    """
    if not script_path or not source_line:
        return {"error": "script_path and source_line required"}

    safe_name = os.path.basename(script_path)

    # Search locations: local scripts/ dir, then per-project sync dirs
    search_roots = [
        os.path.realpath(os.path.join(GDS_DIR, "..", "scripts")),
    ]
    if os.path.isdir(PROJECTS_DIR):
        for entry in os.listdir(PROJECTS_DIR):
            candidate = os.path.join(PROJECTS_DIR, entry, "scripts")
            if os.path.isdir(candidate):
                search_roots.append(os.path.realpath(candidate))

    full_path = None
    for root in search_roots:
        candidate = os.path.realpath(os.path.join(root, safe_name))
        if candidate.startswith(root) and os.path.isfile(candidate):
            full_path = candidate
            break

    if not full_path:
        return {"error": f"Script not found: {script_path}"}

    with open(full_path) as f:
        lines = f.readlines()

    start = max(0, source_line - 11)  # 10 lines before
    end = min(len(lines), source_line + 10)  # 10 lines after

    snippet_lines = []
    for i in range(start, end):
        snippet_lines.append({
            "num": i + 1,
            "text": lines[i].rstrip("\n"),
            "highlighted": i + 1 == source_line,
        })

    return {
        "script_path": script_path,
        "source_line": source_line,
        "total_lines": len(lines),
        "snippet_start": start + 1,
        "snippet_end": end,
        "snippet": snippet_lines,
    }


def _load_source_map(gds_name: str) -> list[dict] | None:
    """Load source map from sidecar JSON file next to the GDS file.

    The tracer writes a .source_map.json sidecar when building with tracing.
    Format: [{"line": N, "fn": "...", "cls": "...", "call": "..."}, ...]
    """
    base = os.path.splitext(gds_name)[0]
    sidecar = os.path.join(GDS_DIR, base + ".source_map.json")
    if not os.path.isfile(sidecar):
        return None
    try:
        with open(sidecar) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
