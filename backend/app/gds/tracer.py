"""AST-based source tracer for gdsfactory scripts.

Analyzes Python scripts to find gf.components.*() and gf.read.*() calls,
records their line numbers and enclosing scope (function/class), then
post-processes the generated GDS to inject source metadata onto shapes.

Uses integer GDS property key 1001 with JSON payload because:
- gdsfactory .info does NOT survive write_gds()
- String-key properties don't survive GDS2 format
- Integer key + JSON string round-trips correctly via klayout
"""
import ast
import json
import os
import tempfile
from dataclasses import dataclass, field

import klayout.db as db


SOURCE_PROP_KEY = 1001


@dataclass
class SourceEntry:
    line: int
    function_name: str | None
    class_name: str | None
    call_text: str


@dataclass
class SourceMap:
    script_path: str
    entries: list[SourceEntry] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps([
            {
                "line": e.line,
                "fn": e.function_name,
                "cls": e.class_name,
                "call": e.call_text,
            }
            for e in self.entries
        ])


def analyze_script(script_path: str) -> SourceMap:
    """Walk AST of a gdsfactory script and extract source entries."""
    with open(script_path) as f:
        source = f.read()

    tree = ast.parse(source, filename=script_path)
    source_map = SourceMap(script_path=script_path)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        call_text = _call_name(source, node)
        if not _is_gdsfactory_call(func):
            continue

        enclosing_fn, enclosing_cls = _enclosing_scope(tree, node)

        source_map.entries.append(SourceEntry(
            line=node.lineno,
            function_name=enclosing_fn,
            class_name=enclosing_cls,
            call_text=call_text,
        ))

    return source_map


def tag_gds(gds_path: str, source_map: SourceMap, script_source: str) -> str:
    """Post-process a GDS file to inject source metadata onto shapes.

    Maps shapes in the GDS back to source entries using heuristics:
    - Cell names containing component identifiers are matched to calls
    - Within top cell, shapes are tagged by group matching
    Writes tagged GDS to a temp file and returns its path.
    """
    layout = db.Layout()
    layout.read(gds_path)

    # gdsfactory writes multiple top cells (one per component).
    # Find the user's top-level cell by matching the Component name from the script.
    top_cells = layout.top_cells()
    top_cell = _find_user_top_cell(top_cells, script_source)
    if top_cell is None:
        return gds_path

    tag_json = source_map.to_json()

    # Tag shapes in the top cell with the full source map
    for li in range(layout.layers()):
        if not layout.is_valid_layer(li):
            continue
        for shape in top_cell.shapes(li).each():
            shape.set_property(SOURCE_PROP_KEY, tag_json)

    # Tag child cells that match specific component calls
    for ci in range(layout.cells()):
        cell = layout.cell(ci)
        if cell is None or cell == top_cell:
            continue
        cell_name = cell.name.lower()
        for entry in source_map.entries:
            if _cell_matches_call(cell_name, entry.call_text):
                entry_json = json.dumps({
                    "line": entry.line,
                    "fn": entry.function_name,
                    "cls": entry.class_name,
                    "call": entry.call_text,
                })
                for li in range(layout.layers()):
                    if not layout.is_valid_layer(li):
                        continue
                    for shape in cell.shapes(li).each():
                        shape.set_property(SOURCE_PROP_KEY, entry_json)
                break  # one match per cell is enough

    tagged_fd, tagged_path = tempfile.mkstemp(suffix=".gds", prefix="tagged_")
    os.close(tagged_fd)
    layout.write(tagged_path)
    return tagged_path


def build_with_trace(script_path: str, gds_output: str) -> SourceMap:
    """Run a gdsfactory script with source tracing.

    1. AST-analyze the script
    2. Run the script (produces GDS)
    3. Post-process the GDS to inject source metadata
    4. Return the source map
    """
    source_map = analyze_script(script_path)

    with open(script_path) as f:
        script_source = f.read()

    # Run the script to produce GDS
    script_dir = os.path.dirname(os.path.abspath(script_path))
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, os.path.basename(script_path)],
        cwd=script_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")

    # Post-process the GDS
    if os.path.isfile(gds_output):
        tagged = tag_gds(gds_output, source_map, script_source)
        import shutil
        shutil.move(tagged, gds_output)

        # Write sidecar source map for the geometry endpoint
        sidecar_path = os.path.splitext(gds_output)[0] + ".source_map.json"
        with open(sidecar_path, "w") as f:
            f.write(source_map.to_json())

    return source_map


def _is_gdsfactory_call(func: ast.expr) -> bool:
    """Check if a call target is a gdsfactory API call."""
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Attribute):
            # gf.components.mzi() → value=Attribute(value=Name('gf'), attr='components')
            return (
                isinstance(func.value.value, ast.Name)
                and func.value.value.id == "gf"
                and func.value.attr in ("components", "read")
            )
        if isinstance(func.value, ast.Name):
            # gf.mzi() (less common but valid)
            return func.value.id == "gf"
    return False


def _call_name(source: str, node: ast.Call) -> str:
    """Extract the readable call text from source."""
    try:
        end = node.end_col_offset or len(source.splitlines()[node.lineno - 1])
        line_start = sum(len(l) + 1 for l in source.splitlines()[:node.lineno - 1])
        return source[line_start:line_start + end].strip()
    except (IndexError, TypeError):
        return "<call>"


def _enclosing_scope(tree: ast.Module, node: ast.Call) -> tuple[str | None, str | None]:
    """Find the enclosing function and class for a node."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is node:
                fn_name = None
                cls_name = None
                if isinstance(parent, ast.FunctionDef):
                    fn_name = parent.name
                elif isinstance(parent, ast.AsyncFunctionDef):
                    fn_name = parent.name
                if isinstance(parent, ast.ClassDef):
                    cls_name = parent.name
                # Walk up further to find class if parent is function
                if fn_name and not cls_name:
                    for grandparent in ast.walk(tree):
                        for gc in ast.iter_child_nodes(grandparent):
                            if gc is parent and isinstance(grandparent, ast.ClassDef):
                                cls_name = grandparent.name
                return fn_name, cls_name
    return None, None


def _cell_matches_call(cell_name: str, call_text: str) -> bool:
    """Heuristic: check if a cell name matches a component call."""
    call_lower = call_text.lower()
    for prefix in ("gf.components.", "gf.read."):
        if prefix in call_lower:
            idx = call_lower.index(prefix) + len(prefix)
            comp_name = call_lower[idx:].split("(")[0].strip()
            if comp_name in cell_name:
                return True
    return False


def _find_user_top_cell(top_cells: list, script_source: str):
    """Find the user's top-level component cell among gdsfactory's multiple top cells.

    gdsfactory creates one top cell per component. The user's top cell is the one
    whose name contains the Component name from `gf.Component("name")`.
    """
    import re
    # Find gf.Component("name") calls in source
    matches = re.findall(r'gf\.Component\(["\'](\w+)["\']\)', script_source)
    if not matches:
        # Fallback: return first top cell
        return top_cells[0] if top_cells else None

    target = matches[0].lower()
    for tc in top_cells:
        if target in tc.name.lower():
            return tc

    return top_cells[0] if top_cells else None
