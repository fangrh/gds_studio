import pytest


@pytest.mark.asyncio
async def test_list_issues_empty(client):
    response = await client.get("/api/issues")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_issue(client):
    response = await client.post("/api/issues", json={
        "title": "Broken waveguide bend",
        "body": "The bend radius at cell ring_cell_1 is too tight.",
        "priority": "high",
        "script_path": "scripts/ring_resonator.py",
        "linked_elements": [
            {
                "gds_build_id": 1,
                "cell_name": "ring_cell_1",
                "element_id": 42,
                "layer": "M1",
                "bbox": "10.5,20,30,40",
                "source_script_line": 15,
                "deep_link_url": "/viewer?gds=ring_resonator&cell=ring_cell_1&elem=42&layer=M1"
            }
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Broken waveguide bend"
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert len(data["linked_elements"]) == 1
    assert data["linked_elements"][0]["cell_name"] == "ring_cell_1"


@pytest.mark.asyncio
async def test_get_issue(client):
    create = await client.post("/api/issues", json={
        "title": "Layer misalignment",
        "body": "M2 shift vs M1 on left side",
    })
    issue_id = create.json()["id"]

    response = await client.get(f"/api/issues/{issue_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Layer misalignment"


@pytest.mark.asyncio
async def test_update_issue_status(client):
    create = await client.post("/api/issues", json={
        "title": "DRC violation", "body": "Min spacing on D1"
    })
    issue_id = create.json()["id"]

    response = await client.patch(f"/api/issues/{issue_id}", json={
        "status": "in_progress"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_list_issues_by_status(client):
    await client.post("/api/issues", json={
        "title": "Open issue 1", "body": "body"
    })
    await client.post("/api/issues", json={
        "title": "Open issue 2", "body": "body"
    })
    done = await client.post("/api/issues", json={
        "title": "Resolved issue", "body": "body"
    })
    done_id = done.json()["id"]
    await client.patch(f"/api/issues/{done_id}", json={"status": "resolved"})

    response = await client.get("/api/issues?status=open")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/issues?status=resolved")
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_issues_by_element_id(client):
    await client.post("/api/issues", json={
        "title": "Bend too tight",
        "body": "Radius is 5um",
        "linked_elements": [
            {"element_id": 42, "cell_name": "ring_cell_1", "layer": "M1"}
        ]
    })
    await client.post("/api/issues", json={
        "title": "Gap too narrow",
        "body": "Spacing violation",
        "linked_elements": [
            {"element_id": 42, "cell_name": "ring_cell_1", "layer": "M1"}
        ]
    })
    await client.post("/api/issues", json={
        "title": "Unrelated issue",
        "body": "Different element",
        "linked_elements": [
            {"element_id": 99, "cell_name": "other_cell", "layer": "D1"}
        ]
    })

    response = await client.get("/api/issues?element_id=42&cell_name=ring_cell_1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(d["title"] in ("Bend too tight", "Gap too narrow") for d in data)


@pytest.mark.asyncio
async def test_list_issues_by_element_id_empty(client):
    response = await client.get("/api/issues?element_id=999&cell_name=nope")
    assert response.status_code == 200
    assert response.json() == []
