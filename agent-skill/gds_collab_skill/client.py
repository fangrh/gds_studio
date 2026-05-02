"""HTTP client for the GDS Collab Platform API."""
import os
import httpx

API_BASE = os.environ.get("GDS_COLLAB_API", "http://localhost:8000")


class GdsCollabClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def register_session(self, agent_type: str, model: str, skill_version: str | None = None) -> dict:
        r = self._client.post(self._url("/api/agent/session"), json={
            "agent_type": agent_type,
            "model": model,
            "skill_version": skill_version,
        })
        r.raise_for_status()
        return r.json()

    def poll_issues(self) -> list[dict]:
        r = self._client.get(self._url("/api/agent/poll"))
        r.raise_for_status()
        return r.json()

    def get_issue(self, issue_id: int) -> dict:
        r = self._client.get(self._url(f"/api/issues/{issue_id}"))
        r.raise_for_status()
        return r.json()

    def claim_issue(self, issue_id: int, session_id: int) -> dict:
        r = self._client.post(self._url(f"/api/agent/claim/{issue_id}?session_id={session_id}"))
        r.raise_for_status()
        return r.json()

    def trigger_build(self, script_id: int, session_id: int, git_commit: str | None = None) -> dict:
        r = self._client.post(
            self._url(f"/api/agent/build?session_id={session_id}"),
            json={"script_id": script_id, "git_commit": git_commit},
        )
        r.raise_for_status()
        return r.json()

    def post_comment(self, issue_id: int, body: str, session_id: int) -> dict:
        r = self._client.post(self._url("/api/agent/comment"), json={
            "issue_id": issue_id,
            "body": body,
            "session_id": session_id,
        })
        r.raise_for_status()
        return r.json()

    def resolve_issue(self, issue_id: int, body: str | None = None) -> dict:
        r = self._client.post(self._url(f"/api/agent/resolve/{issue_id}"), json={
            "body": body,
        })
        r.raise_for_status()
        return r.json()

    def get_script(self, script_path: str) -> str:
        """Read a script file from the server. Falls back to local filesystem."""
        try:
            r = self._client.get(self._url(f"/api/gds/scripts/by-path?path={script_path}"))
            r.raise_for_status()
            return r.text
        except Exception:
            scripts_dir = os.environ.get("GDS_SCRIPTS_DIR", "/data/scripts")
            with open(os.path.join(scripts_dir, script_path)) as f:
                return f.read()

    def get_source_context(self, script_path: str, source_line: int) -> dict | None:
        """Get source code context around a specific line."""
        try:
            r = self._client.get(self._url(
                f"/api/gds/source?script_path={script_path}&source_line={source_line}"
            ))
            r.raise_for_status()
            data = r.json()
            if data.get("error"):
                return None
            return data
        except Exception:
            return None
