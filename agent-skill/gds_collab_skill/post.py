"""Post agent responses back to the platform."""
from gds_collab_skill.client import GdsCollabClient


def post_response(
    client: GdsCollabClient,
    issue_id: int,
    body: str,
    session_id: int,
    script_id: int | None = None,
    git_commit: str | None = None,
):
    """Post a resolution response to an issue, optionally triggering a rebuild."""
    if script_id:
        client.trigger_build(script_id, session_id, git_commit)

    result = client.resolve_issue(issue_id, body)
    return result
