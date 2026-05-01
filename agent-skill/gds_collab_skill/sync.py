"""Sync operations — pull/push between agent local folder and server."""
import json
import os
import re
from datetime import datetime, timezone

import httpx


def _load_state(project_dir: str) -> dict:
    state_path = os.path.join(project_dir, ".sync-state.json")
    if os.path.exists(state_path):
        with open(state_path) as f:
            return json.load(f)
    return {}


def _save_state(project_dir: str, state: dict):
    state_path = os.path.join(project_dir, ".sync-state.json")
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].rstrip("-")


def pull(project_dir: str, server: str, token: str) -> dict:
    """Pull issues and wiki from server to local markdown files."""
    state = _load_state(project_dir)
    since = state.get("last_sync")

    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if since:
        params["since"] = since

    client = httpx.Client(timeout=30.0)
    r = client.get(f"{server}/api/sync/pull", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()

    issues_dir = os.path.join(project_dir, "issues")
    wiki_dir = os.path.join(project_dir, "wiki")
    os.makedirs(issues_dir, exist_ok=True)
    os.makedirs(wiki_dir, exist_ok=True)

    pulled_issues = 0
    for issue in data.get("issues", []):
        slug = _slugify(issue["title"])
        filename = f"{issue['id']:03d}-{slug}.md"
        filepath = os.path.join(issues_dir, filename)

        frontmatter = {
            "id": issue["id"],
            "title": issue["title"],
            "status": issue["status"],
            "priority": issue.get("priority", "normal"),
            "script": issue.get("script_path", ""),
            "synced_at": data["server_timestamp"],
        }
        if issue.get("linked_elements"):
            frontmatter["linked_elements"] = [
                f"cell: {le.get('cell_name')}, elem: {le.get('element_id')}, layer: {le.get('layer')}"
                for le in issue["linked_elements"]
            ]

        lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f'{key}: "{value}"' if isinstance(value, str) and ("\"" in str(value) or ":" in str(value)) else f"{key}: {value}")
        lines.append("---")
        lines.append("")
        lines.append(issue.get("body", ""))

        comments = issue.get("comments", [])
        if comments:
            lines.append("")
            lines.append("## Comments")
            for c in comments:
                author = c.get("author_type", "unknown")
                body = c.get("body", "")
                ts = c.get("created_at", "")
                lines.append(f"- **{author}** ({ts}): {body}")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        pulled_issues += 1

    pulled_wiki = 0
    for page in data.get("wiki_updates", []):
        filename = f"{page.get('slug', _slugify(page['title']))}.md"
        filepath = os.path.join(wiki_dir, filename)
        with open(filepath, "w") as f:
            f.write(f"# {page['title']}\n\n{page.get('body', '')}")
        pulled_wiki += 1

    state["last_sync"] = data["server_timestamp"]
    _save_state(project_dir, state)

    return {
        "issues": pulled_issues,
        "wiki": pulled_wiki,
        "server_timestamp": data["server_timestamp"],
    }


def push(project_dir: str, server: str, token: str, commit_sha: str = "") -> dict:
    """Push local changes (scripts, GDS, issue replies, wiki) to server."""
    headers = {"Authorization": f"Bearer {token}"}
    client = httpx.Client(timeout=60.0)

    scripts_dir = os.path.join(project_dir, "scripts")
    gds_dir = os.path.join(project_dir, "gds")
    issues_dir = os.path.join(project_dir, "issues")
    wiki_dir = os.path.join(project_dir, "wiki")

    files = {}
    file_handles = []
    file_idx = 0

    if os.path.isdir(scripts_dir):
        for fname in os.listdir(scripts_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(scripts_dir, fname)
                fh = open(fpath, "rb")
                file_handles.append(fh)
                files[f"scripts_{file_idx}"] = (fname, fh, "text/x-python")
                file_idx += 1

    if os.path.isdir(gds_dir):
        for fname in os.listdir(gds_dir):
            if fname.endswith(".gds"):
                fpath = os.path.join(gds_dir, fname)
                fh = open(fpath, "rb")
                file_handles.append(fh)
                files[f"gds_files_{file_idx}"] = (fname, fh, "application/octet-stream")
                file_idx += 1

    try:
        issue_replies = []
        if os.path.isdir(issues_dir):
            for fname in os.listdir(issues_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(issues_dir, fname)
                with open(fpath) as f:
                    content = f.read()

                frontmatter = _parse_frontmatter(content)
                agent_replies = _extract_agent_replies(content)
                if agent_replies and frontmatter.get("id"):
                    for reply in agent_replies:
                        issue_replies.append({
                            "issue_id": frontmatter["id"],
                            "body": reply,
                        })

        wiki_updates = []
        if os.path.isdir(wiki_dir):
            for fname in os.listdir(wiki_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(wiki_dir, fname)
                with open(fpath) as f:
                    content = f.read()
                title_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else os.path.splitext(fname)[0]
                body = re.sub(r"^#\s+.+?\n+", "", content, count=1)
                slug = os.path.splitext(fname)[0]
                wiki_updates.append({"title": title, "slug": slug, "body": body.strip()})

        data = {
            "issue_replies": json.dumps(issue_replies),
            "wiki_updates": json.dumps(wiki_updates),
            "commit_sha": commit_sha,
        }

        r = client.post(f"{server}/api/sync/push", headers=headers, data=data, files=files)
        r.raise_for_status()
        result = r.json()

        state = _load_state(project_dir)
        state["last_sync"] = result["server_timestamp"]
        _save_state(project_dir, state)

        return result
    finally:
        for fh in file_handles:
            fh.close()


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    yaml_str = content[3:end].strip()
    result = {}
    for line in yaml_str.split("\n"):
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            value = value.strip().strip('"').strip("'")
            if value.isdigit():
                value = int(value)
            result[key.strip()] = value
    return result


def _extract_agent_replies(content: str) -> list[str]:
    """Extract new agent replies from issue markdown comments section."""
    replies = []
    in_comments = False
    for line in content.split("\n"):
        if line.startswith("## Comments"):
            in_comments = True
            continue
        if in_comments and line.startswith("## "):
            in_comments = False
            continue
        if in_comments and line.strip().startswith("- **agent**"):
            body = line.strip()
            body = re.sub(r"^- \*\*agent\*\* \([^)]*\):\s*", "", body)
            if body.startswith("PUSH_REPLY:"):
                replies.append(body[len("PUSH_REPLY:"):].strip())
    return replies
