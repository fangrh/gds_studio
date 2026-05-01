import pytest


@pytest.mark.asyncio
async def test_list_scripts_empty(client):
    response = await client.get("/api/gds/scripts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_script(client):
    response = await client.post("/api/gds/scripts", json={
        "path": "scripts/ring_res.py",
        "name": "ring_resonator",
        "description": "Ring resonator",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ring_resonator"
    assert data["path"] == "scripts/ring_res.py"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_script(client):
    create = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create.json()["id"]

    response = await client.get(f"/api/gds/scripts/{script_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test"


@pytest.mark.asyncio
async def test_create_build(client):
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    response = await client.post("/api/gds/builds", json={
        "script_id": script_id,
        "gds_path": "gds/test.gds",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["script_id"] == script_id


@pytest.mark.asyncio
async def test_list_builds(client):
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    await client.post("/api/gds/builds", json={
        "script_id": script_id, "gds_path": "gds/test.gds",
    })

    response = await client.get(f"/api/gds/scripts/{script_id}/builds")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_build_with_cells(client):
    from sqlalchemy.orm import Session
    from app.models import GdsCell

    # Use the conftest's test engine to ensure same DB
    import tests.conftest as cf

    # Create script via API
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    # Create build via API
    create_build = await client.post("/api/gds/builds", json={
        "script_id": script_id, "gds_path": "gds/test.gds",
    })
    build_id = create_build.json()["id"]

    # Insert cell directly using test engine
    with Session(cf.test_engine) as session:
        cell = GdsCell(
            build_id=build_id, name="test_cell",
            cell_type="cell", bbox="0,0,1000,500",
            layer_count=2, element_count=3,
        )
        session.add(cell)
        session.commit()

    response = await client.get(f"/api/gds/builds/{build_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["cells"]) == 1
    assert data["cells"][0]["name"] == "test_cell"
