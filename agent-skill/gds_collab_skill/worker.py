"""Autonomous agent worker — polls issues, calls Claude API, applies fixes.

Runs as a long-lived process (or k8s Deployment). Each tick:
1. Checks for unreplied user comments
2. Polls for open issues
3. For each item, builds context, asks Claude for a fix, applies it, resolves.
"""
import json
import os
import re
import subprocess
import sys
import time
import traceback

import anthropic

from gds_collab_skill.client import GdsCollabClient
from gds_collab_skill.context import build_issue_context
from gds_collab_skill.post import post_response

API_BASE = os.environ.get("GDS_COLLAB_API", "http://backend:8000")
CLAUDE_MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-4-6")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SCRIPTS_DIR = os.environ.get("GDS_SCRIPTS_DIR", "/data/scripts")
GDS_DIR = os.environ.get("GDS_GDS_DIR", "/data/gds")


def call_claude(system_prompt: str, user_prompt: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return resp.content[0].text


SYSTEM_PROMPT = """You are a photonic chip design engineer. You fix GDSfactory Python scripts.

Rules:
- Only output the modified Python script inside a ```python ... ``` code block.
- Use the GDSfactory API (import gdsfactory as gf).
- Explain your changes in plain text before the code block.
- If you cannot fix the issue, say "CANNOT_FIX:" followed by the reason."""


def extract_code(text: str) -> str | None:
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else None


def write_script(path: str, content: str):
    full = os.path.join(SCRIPTS_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)


def run_script(path: str) -> tuple[bool, str]:
    full = os.path.join(SCRIPTS_DIR, path)
    try:
        result = subprocess.run(
            [sys.executable, full],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "GDS_OUTPUT_DIR": GDS_DIR},
        )
        return result.returncode == 0, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return False, "Script timed out after 60s"


def git_commit_and_push(script_path: str, message: str):
    subprocess.run(["git", "add", script_path], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)


def get_commit_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip()[:12]


def process_issue(client: GdsCollabClient, session_id: int, issue: dict):
    issue_id = issue["issue_id"] if "issue_id" in issue else issue["id"]
    title = issue.get("issue_title") or issue.get("title", "")
    script_path = issue.get("script_path")

    print(f"  Processing issue #{issue_id}: {title}")

    context = build_issue_context(client, issue_id)
    reply = call_claude(SYSTEM_PROMPT, context)
    new_code = extract_code(reply)

    if new_code is None:
        if "CANNOT_FIX:" in reply:
            reason = reply.split("CANNOT_FIX:")[1].strip().split("\n")[0]
        else:
            reason = "Agent could not generate a valid fix."
        client.post_comment(issue_id, reason, session_id)
        print(f"  #{issue_id}: Cannot fix — {reason}")
        return

    if not script_path:
        client.post_comment(issue_id, "No script_path on this issue; cannot apply fix.", session_id)
        return

    write_script(script_path, new_code)
    print(f"  #{issue_id}: Wrote updated script")

    ok, output = run_script(script_path)
    if not ok:
        client.post_comment(
            issue_id,
            f"Script failed after fix attempt:\n```\n{output[:500]}\n```\nReverting.",
            session_id,
        )
        print(f"  #{issue_id}: Script failed — {output[:200]}")
        return

    commit_msg = f"fix: resolve issue #{issue_id} — {title}"
    try:
        git_commit_and_push(script_path, commit_msg)
        sha = get_commit_sha()
    except Exception as e:
        sha = None
        print(f"  #{issue_id}: git push failed — {e}")

    explanation = reply.split("```python")[0].strip() if "```python" in reply else reply[:300]
    resolve_body = f"{explanation}\n\nChanges pushed to main ({sha}). Argo CI/CD will auto-deploy."

    post_response(client, issue_id, resolve_body, session_id, git_commit=sha)
    print(f"  #{issue_id}: Resolved.")


def process_unreplied(client: GdsCollabClient, session_id: int, item: dict):
    issue_id = item["issue_id"]
    comments = item.get("unreplied_comments", [])
    script_path = item.get("script_path")

    print(f"  Unreplied on issue #{issue_id}: {len(comments)} comment(s)")

    if not script_path:
        for c in comments:
            reply = call_claude(
                SYSTEM_PROMPT,
                f"User commented on issue #{issue_id} '{item.get('issue_title')}':\n"
                f'"{c["body"]}"\n\n'
                f"Reply helpfully. No code change needed (no script on this issue).",
            )
        client.post_comment(issue_id, reply, session_id)
        return

    context = build_issue_context(client, issue_id)
    reply = call_claude(SYSTEM_PROMPT, context)
    new_code = extract_code(reply)

    if new_code:
        write_script(script_path, new_code)
        ok, output = run_script(script_path)
        if ok:
            try:
                git_commit_and_push(script_path, f"fix: address comment on issue #{issue_id}")
                sha = get_commit_sha()
            except Exception:
                sha = None
            explanation = reply.split("```python")[0].strip() if "```python" in reply else reply[:300]
            client.post_comment(
                issue_id,
                f"{explanation}\n\nPushed to main ({sha}). Argo CI/CD will auto-deploy.",
                session_id,
            )
            print(f"  #{issue_id}: Fixed and replied.")
        else:
            client.post_comment(issue_id, f"Fix attempt failed:\n```\n{output[:500]}\n```", session_id)
    else:
        text_reply = call_claude(
            SYSTEM_PROMPT,
            f"User commented on issue #{issue_id}:\n"
            + "\n".join(f'"{c["body"]}"' for c in comments)
            + "\nReply helpfully. No code change needed.",
        )
        client.post_comment(issue_id, text_reply, session_id)
        print(f"  #{issue_id}: Replied (no code change).")


def tick(client: GdsCollabClient, session_id: int):
    try:
        r = client._client.get(f"{client.base_url}/api/agent/unreplied")
        unreplied = r.json() if r.status_code == 200 else []
    except Exception:
        unreplied = []

    if unreplied:
        print(f"Found {len(unreplied)} issue(s) with unreplied comments")
        for item in unreplied:
            try:
                process_unreplied(client, session_id, item)
            except Exception:
                traceback.print_exc()

    try:
        issues = client.poll_issues()
    except Exception:
        issues = []

    if issues:
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        issues.sort(key=lambda i: priority_order.get(i.get("priority", "normal"), 2))
        print(f"Found {len(issues)} open issue(s)")
        for issue in issues:
            try:
                process_issue(client, session_id, issue)
            except Exception:
                traceback.print_exc()

    if not unreplied and not issues:
        print("Nothing to do.")


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print(f"Agent worker starting — model={CLAUDE_MODEL}, interval={POLL_INTERVAL}s")
    print(f"Backend: {API_BASE}")

    client = GdsCollabClient(base_url=API_BASE)

    while True:
        try:
            session = client.register_session(
                agent_type="k8s-worker",
                model=CLAUDE_MODEL,
                skill_version="0.1.0",
            )
            session_id = session["id"]
            tick(client, session_id)
        except Exception:
            traceback.print_exc()

        print(f"Sleeping {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
