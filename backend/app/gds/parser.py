"""Parse GDS files using klayout and extract cells, elements, layers."""
import json
from dataclasses import dataclass, field
from typing import Optional

import klayout.db as db

SOURCE_PROP_KEY = 1001


@dataclass
class ElementData:
    element_type: str  # "polygon", "box", "path", "text", "reference"
    layer: str  # "1/0" format
    bbox: str  # "x1,y1,x2,y2" in DBU
    vertices: list[list[float]] = field(default_factory=list)
    path_data: str = ""
    properties: dict = field(default_factory=dict)
    source_line: Optional[int] = None
    source_function: Optional[str] = None
    source_class: Optional[str] = None
    source_call: Optional[str] = None


@dataclass
class CellData:
    name: str
    cell_type: str = "cell"
    bbox: str = ""
    layer_count: int = 0
    element_count: int = 0
    elements: list[ElementData] = field(default_factory=list)


@dataclass
class GdsParseResult:
    cells: list[CellData] = field(default_factory=list)
    layer_map: dict[tuple[int, int], str] = field(default_factory=dict)


def _layer_key(layer_index: int, layout: db.Layout) -> tuple[int, int]:
    info = layout.get_info(layer_index)
    return (info.layer, info.datatype)


def _layer_str(layer_index: int, layout: db.Layout) -> str:
    info = layout.get_info(layer_index)
    return f"{info.layer}/{info.datatype}"


def _bbox_str(box: db.Box) -> str:
    return f"{box.left},{box.bottom},{box.right},{box.top}"


def parse_gds(gds_path: str) -> GdsParseResult:
    """Parse a GDS file and return structured cell/element data."""
    layout = db.Layout()
    layout.read(gds_path)

    result = GdsParseResult()

    # Build layer map
    for i in range(layout.layers()):
        if layout.is_valid_layer(i):
            result.layer_map[_layer_key(i, layout)] = _layer_str(i, layout)

    # Iterate top cells
    for cell_idx in range(layout.cells()):
        cell = layout.cell(cell_idx)
        if cell is None:
            continue

        cell_data = CellData(
            name=cell.name,
            bbox=_bbox_str(cell.dbbox()) if cell.dbbox() else "",
        )

        layers_in_cell = set()

        # Extract shapes
        for li in range(layout.layers()):
            if not layout.is_valid_layer(li):
                continue
            shapes = cell.shapes(li)
            if shapes.is_empty():
                continue
            layers_in_cell.add(li)

            for shape in shapes.each():
                src = _read_source_meta(shape)
                if shape.is_box():
                    box = shape.dbbox()
                    el = ElementData(
                        element_type="box",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(box),
                        vertices=[
                            [box.left, box.bottom],
                            [box.right, box.bottom],
                            [box.right, box.top],
                            [box.left, box.top],
                        ],
                        **src,
                    )
                    cell_data.elements.append(el)
                elif shape.is_polygon():
                    poly = shape.polygon
                    verts = []
                    for p in poly.each_point_hull():
                        verts.append([p.x * layout.dbu, p.y * layout.dbu])
                    el = ElementData(
                        element_type="polygon",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                        vertices=verts,
                        **src,
                    )
                    cell_data.elements.append(el)
                elif shape.is_path():
                    el = ElementData(
                        element_type="path",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                        **src,
                    )
                    cell_data.elements.append(el)
                elif shape.is_text():
                    el = ElementData(
                        element_type="text",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                        **src,
                    )
                    cell_data.elements.append(el)

        # Extract cell references (instances)
        for inst in cell.each_inst():
            ref = ElementData(
                element_type="reference",
                layer="ref",
                bbox=_bbox_str(inst.dbbox()) if inst.dbbox() else "",
                properties={"cell_name": inst.cell.name},
            )
            cell_data.elements.append(ref)

        cell_data.layer_count = len(layers_in_cell)
        cell_data.element_count = len(cell_data.elements)
        result.cells.append(cell_data)

    return result


def _read_source_meta(shape) -> dict:
    """Read source metadata from a shape's GDS property (key 1001).

    The tracer stores a JSON array of source entries or a single entry object.
    For shapes in child cells, it's a single entry. For top-cell shapes, it's
    the full source map (we use the first entry as the default).
    """
    raw = shape.property(SOURCE_PROP_KEY)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}

    if isinstance(data, list) and data:
        # Full source map on top-cell shape — use first entry
        entry = data[0]
    elif isinstance(data, dict):
        entry = data
    else:
        return {}

    return {
        "source_line": entry.get("line"),
        "source_function": entry.get("fn"),
        "source_class": entry.get("cls"),
        "source_call": entry.get("call"),
    }
