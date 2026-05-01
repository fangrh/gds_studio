import pytest
from app.gds.parser import parse_gds, GdsParseResult


def test_parse_result_has_cells():
    """Parser should extract cells from a GDS file."""
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("test_cell")
    layer = layout.layer(1, 0)  # layer 1, datatype 0
    cell.shapes(layer).insert(db.Box(0, 0, 1000, 500))
    layout.write("tests/fixtures/test_simple.gds")

    result = parse_gds("tests/fixtures/test_simple.gds")
    assert isinstance(result, GdsParseResult)
    assert len(result.cells) > 0
    assert result.cells[0].name == "test_cell"


def test_parse_extracts_elements():
    """Parser should extract elements (shapes) from cells."""
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("element_test")
    layer1 = layout.layer(1, 0)
    layer2 = layout.layer(2, 0)
    cell.shapes(layer1).insert(db.Box(0, 0, 1000, 500))
    cell.shapes(layer2).insert(db.Polygon([db.Point(0, 0), db.Point(500, 0), db.Point(250, 500)]))
    layout.write("tests/fixtures/test_elements.gds")

    result = parse_gds("tests/fixtures/test_elements.gds")
    cell_data = result.cells[0]
    assert cell_data.element_count >= 2


def test_parse_extracts_layers():
    """Parser should identify which layers are present."""
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("layer_test")
    layout.layer(1, 0)
    layout.layer(2, 0)
    layout.layer(3, 1)
    cell.shapes(layout.layer(1, 0)).insert(db.Box(0, 0, 100, 100))
    cell.shapes(layout.layer(2, 0)).insert(db.Box(0, 0, 100, 100))
    cell.shapes(layout.layer(3, 1)).insert(db.Box(0, 0, 100, 100))
    layout.write("tests/fixtures/test_layers.gds")

    result = parse_gds("tests/fixtures/test_layers.gds")
    assert len(result.layer_map) >= 3
    assert (1, 0) in result.layer_map
    assert (2, 0) in result.layer_map
    assert (3, 1) in result.layer_map
