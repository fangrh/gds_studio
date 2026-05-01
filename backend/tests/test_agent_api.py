import pytest


@pytest.mark.asyncio
async def test_register_agent_session(client):
    response = await client.post("/api/agent/session", json={
        "agent_type": "claude-code",
        "model": "claude-sonnet-4.6",
        "skill_version": "0.1.0",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == "claude-code"
    assert data["status"] == "active"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_poll_open_issues(client):
    await client.post("/api/issues", json={"title": "Issue 1", "body": "test"})
    await client.post("/api/issues", json={"title": "Issue 2", "body": "test"})

    response = await client.get("/api/agent/poll")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(i["status"] == "open" for i in data)


@pytest.mark.asyncio
async def test_poll_respects_claimed_issues(client):
    await client.post("/api/issues", json={"title": "Open issue", "body": "test"})
    claimed = await client.post("/api/issues", json={"title": "Claimed issue", "body": "test"})
    claimed_id = claimed.json()["id"]
    await client.patch(f"/api/issues/{claimed_id}", json={"status": "in_progress"})

    response = await client.get("/api/agent/poll")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_agent_claim_issue(client):
    sess = await client.post("/api/agent/session", json={
        "agent_type": "claude-code", "model": "claude-sonnet-4.6",
    })
    session_id = sess.json()["id"]

    issue = await client.post("/api/issues", json={"title": "Fix me", "body": "test"})
    issue_id = issue.json()["id"]

    response = await client.post(f"/api/agent/claim/{issue_id}?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["resolved_by"] == "agent"


@pytest.mark.asyncio
async def test_agent_resolve_issue(client):
    sess = await client.post("/api/agent/session", json={
        "agent_type": "claude-code", "model": "claude-sonnet-4.6",
    })
    session_id = sess.json()["id"]

    issue = await client.post("/api/issues", json={"title": "Resolvable", "body": "test"})
    issue_id = issue.json()["id"]
    await client.post(f"/api/agent/claim/{issue_id}?session_id={session_id}")

    response = await client.post(f"/api/agent/resolve/{issue_id}", json={
        "body": "Fixed by adjusting the bend radius parameter"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert len(data["comments"]) >= 1
