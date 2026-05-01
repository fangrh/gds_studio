import pytest


@pytest.mark.asyncio
async def test_list_wiki_pages_empty(client):
    response = await client.get("/api/wiki")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_wiki_page(client):
    response = await client.post("/api/wiki", json={
        "title": "Design Rules",
        "slug": "design-rules",
        "body": "# Design Rules\n\n## M1 Layer\n- Minimum width: 0.5 um",
        "category": "process",
        "tags": ["design-rules", "M1"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Design Rules"
    assert data["slug"] == "design-rules"
    assert data["version"] == 1
    assert data["category"] == "process"


@pytest.mark.asyncio
async def test_get_wiki_page_by_slug(client):
    await client.post("/api/wiki", json={
        "title": "Process Notes", "slug": "process-notes",
        "body": "Some notes",
    })

    response = await client.get("/api/wiki/process-notes")
    assert response.status_code == 200
    assert response.json()["title"] == "Process Notes"


@pytest.mark.asyncio
async def test_update_wiki_page(client):
    await client.post("/api/wiki", json={
        "title": "Tapeout", "slug": "tapeout-2026",
        "body": "Initial body",
    })

    response = await client.patch("/api/wiki/tapeout-2026", json={
        "body": "Updated body with new rules",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "Updated body with new rules"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_wiki_page_not_found(client):
    response = await client.get("/api/wiki/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_filter_by_category(client):
    await client.post("/api/wiki", json={
        "title": "Design Rule 1", "slug": "dr1",
        "category": "design-rules",
    })
    await client.post("/api/wiki", json={
        "title": "Process Note 1", "slug": "pn1",
        "category": "process",
    })
    await client.post("/api/wiki", json={
        "title": "Design Rule 2", "slug": "dr2",
        "category": "design-rules",
    })

    response = await client.get("/api/wiki?category=design-rules")
    assert response.status_code == 200
    assert len(response.json()) == 2
