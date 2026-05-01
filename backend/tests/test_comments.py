import pytest


@pytest.mark.asyncio
async def test_add_comment_to_issue(client):
    issue = await client.post("/api/issues", json={
        "title": "Need comments", "body": "testing"
    })
    issue_id = issue.json()["id"]

    response = await client.post("/api/comments", json={
        "target_type": "issue",
        "target_id": issue_id,
        "body": "This is a test comment",
        "author_type": "user",
        "author_id": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "This is a test comment"
    assert data["target_type"] == "issue"
    assert data["target_id"] == issue_id


@pytest.mark.asyncio
async def test_add_agent_comment(client):
    issue = await client.post("/api/issues", json={
        "title": "Agent test", "body": "testing"
    })
    issue_id = issue.json()["id"]

    response = await client.post("/api/comments", json={
        "target_type": "issue",
        "target_id": issue_id,
        "body": "Fixed by adjusting bend radius from 5 to 10 um",
        "author_type": "agent",
        "author_id": 99,
        "agent_model": "claude-sonnet-4.6",
        "agent_skill_version": "0.1.0",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["author_type"] == "agent"
    assert data["agent_model"] == "claude-sonnet-4.6"


@pytest.mark.asyncio
async def test_list_comments_for_issue(client):
    issue = await client.post("/api/issues", json={
        "title": "Comment list test", "body": "testing"
    })
    issue_id = issue.json()["id"]

    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "Comment 1"
    })
    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "Comment 2"
    })

    response = await client.get(f"/api/comments/issue/{issue_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_issue_includes_comments(client):
    issue = await client.post("/api/issues", json={
        "title": "With comments", "body": "testing"
    })
    issue_id = issue.json()["id"]

    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "A comment"
    })

    response = await client.get(f"/api/issues/{issue_id}")
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 1
