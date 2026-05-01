from app.gds.addressing import build_deep_link, parse_deep_link


def test_design_level_link():
    url = build_deep_link(gds="ring_resonator", build=42)
    assert url == "/viewer?gds=ring_resonator&build=42"


def test_cell_level_link():
    url = build_deep_link(gds="ring_resonator", cell="ring_cell_1", layers=["M1", "D1"])
    assert "gds=ring_resonator" in url
    assert "cell=ring_cell_1" in url
    assert "layers=M1,D1" in url


def test_element_level_link():
    url = build_deep_link(
        gds="ring_resonator", cell="ring_cell_1",
        elem=342, layer="M1", bbox="10.5,20,30,40",
    )
    assert "elem=342" in url
    assert "layer=M1" in url
    assert "bbox=10.5,20,30,40" in url


def test_multi_element_link():
    url = build_deep_link(gds="ring_resonator", elems=[342, 343, 345], layer="M1")
    assert "elems=342,343,345" in url


def test_parse_design_link():
    params = parse_deep_link("/viewer?gds=ring_resonator&build=42")
    assert params["gds"] == "ring_resonator"
    assert params["build"] == 42


def test_parse_element_link():
    params = parse_deep_link(
        "/viewer?gds=ring_resonator&cell=ring_cell_1&elem=342&layer=M1&bbox=10.5,20,30,40"
    )
    assert params["gds"] == "ring_resonator"
    assert params["cell"] == "ring_cell_1"
    assert params["elem"] == 342
    assert params["layer"] == "M1"
    assert params["bbox"] == "10.5,20,30,40"


def test_parse_multi_element_link():
    params = parse_deep_link("/viewer?gds=ring_resonator&elems=342,343,345&layer=M1")
    assert params["elems"] == [342, 343, 345]


def test_roundtrip():
    url = build_deep_link(gds="test", cell="c1", elem=10, layer="D1")
    params = parse_deep_link(url)
    assert params["gds"] == "test"
    assert params["cell"] == "c1"
    assert params["elem"] == 10
    assert params["layer"] == "D1"
