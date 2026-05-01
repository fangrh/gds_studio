"""Deep link generation and parsing for GDS viewer state."""
from urllib.parse import urlencode, urlparse, parse_qs


def build_deep_link(
    gds: str,
    build: int | None = None,
    cell: str | None = None,
    layers: list[str] | None = None,
    elem: int | None = None,
    elems: list[int] | None = None,
    layer: str | None = None,
    bbox: str | None = None,
) -> str:
    """Build a deep link URL for the GDS viewer."""
    params: dict[str, str] = {"gds": gds}

    if build is not None:
        params["build"] = str(build)
    if cell is not None:
        params["cell"] = cell
    if layers is not None:
        params["layers"] = ",".join(layers)
    if elem is not None:
        params["elem"] = str(elem)
    if elems is not None:
        params["elems"] = ",".join(str(e) for e in elems)
    if layer is not None:
        params["layer"] = layer
    if bbox is not None:
        params["bbox"] = bbox

    return f"/viewer?{urlencode(params, safe=',')}"


def parse_deep_link(url: str) -> dict:
    """Parse a deep link URL into its components."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    result: dict = {}

    if "gds" in qs:
        result["gds"] = qs["gds"][0]
    if "build" in qs:
        result["build"] = int(qs["build"][0])
    if "cell" in qs:
        result["cell"] = qs["cell"][0]
    if "layers" in qs:
        result["layers"] = qs["layers"][0].split(",")
    if "elem" in qs:
        result["elem"] = int(qs["elem"][0])
    if "elems" in qs:
        result["elems"] = [int(x) for x in qs["elems"][0].split(",")]
    if "layer" in qs:
        result["layer"] = qs["layer"][0]
    if "bbox" in qs:
        result["bbox"] = qs["bbox"][0]

    return result
