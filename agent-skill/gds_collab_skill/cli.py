"""CLI for the GDS Collab Skill. Invoked as `gds-collab-skill <command>`."""
import json
import os

import click
from gds_collab_skill.client import GdsCollabClient
from gds_collab_skill.context import build_issue_context
from gds_collab_skill.post import post_response
from gds_collab_skill.sync import pull as sync_pull, push as sync_push


@click.group()
def cli():
    """GDS Collab Skill - AI agent tool for photonic chip design collaboration."""
    pass


@cli.command()
@click.option("--agent-type", default="claude-code", help="Agent type identifier")
@click.option("--model", default="claude-sonnet-4.6", help="Model name")
@click.option("--skill-version", default="0.1.0", help="Skill package version")
def register(agent_type, model, skill_version):
    """Register a new agent session."""
    client = GdsCollabClient()
    session = client.register_session(agent_type, model, skill_version)
    click.echo(f"Session registered: {session['id']}")
    click.echo(f"Session ID: {session['id']}")


@cli.command()
def poll():
    """Poll for open (unclaimed) issues."""
    client = GdsCollabClient()
    issues = client.poll_issues()
    if not issues:
        click.echo("No open issues.")
        return
    for issue in issues:
        click.echo(f"#{issue['id']}: [{issue['priority']}] {issue['title']}")


@cli.command()
@click.argument("issue_id", type=int)
def context(issue_id):
    """Print the full context for an issue (for the agent to consume)."""
    client = GdsCollabClient()
    ctx = build_issue_context(client, issue_id)
    click.echo(ctx)


@cli.command()
@click.argument("issue_id", type=int)
@click.option("--session-id", type=int, required=True, help="Agent session ID")
@click.option("--body", required=True, help="Resolution description")
@click.option("--script-id", type=int, help="Script ID to trigger rebuild")
@click.option("--git-commit", help="Git commit SHA of the fix")
def resolve(issue_id, session_id, body, script_id, git_commit):
    """Resolve an issue with the agent's response."""
    client = GdsCollabClient()
    result = post_response(client, issue_id, body, session_id, script_id, git_commit)
    click.echo(f"Issue #{issue_id} resolved. Status: {result.get('status')}")


@cli.command()
def unreplied():
    """Find issues with unreplied user comments."""
    client = GdsCollabClient()
    import httpx
    r = client._client.get(f"{client.base_url}/api/agent/unreplied")
    r.raise_for_status()
    items = r.json()
    if not items:
        click.echo("No unreplied comments.")
        return
    for item in items:
        click.echo(f"\nIssue #{item['issue_id']}: [{item['priority']}] {item['issue_title']}")
        click.echo(f"  Status: {item['issue_status']}")
        if item.get('script_path'):
            click.echo(f"  Script: {item['script_path']}")
        for c in item['unreplied_comments']:
            click.echo(f"  Comment #{c['id']}: {c['body'][:80]}")


@cli.command()
@click.option("--name", required=True, help="Project name")
@click.option("--server", default="http://localhost:8000", help="Server URL")
@click.option("--token", required=True, help="Auth token for the project")
@click.option("--dir", "project_dir", default=None, help="Project directory (default: ~/gds-projects/<name>)")
def init(name, server, token, project_dir):
    """Initialize a project work folder with Snakefile and directory structure."""
    if not project_dir:
        project_dir = os.path.join(os.path.expanduser("~"), "gds-projects", name)

    if os.path.exists(project_dir):
        click.echo(f"Directory already exists: {project_dir}")
        click.echo("Use an existing project or choose a different name.")
        return

    os.makedirs(os.path.join(project_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "gds"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "wiki"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "issues"), exist_ok=True)

    snakefile = os.path.join(project_dir, "Snakefile")
    with open(snakefile, "w") as f:
        f.write(SNAKEFILE_TEMPLATE)

    state = {
        "server": server.rstrip("/"),
        "project_name": name,
        "token": token,
        "last_sync": None,
    }
    state_path = os.path.join(project_dir, ".sync-state.json")
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    click.echo(f"Project '{name}' initialized at {project_dir}")
    click.echo(f"Server: {server}")
    click.echo(f"Snakefile: {snakefile}")
    click.echo("")
    click.echo("Checking dependencies...")

    missing = []
    try:
        import gdsfactory  # noqa: F401
        click.echo("  gdsfactory: OK")
    except ImportError:
        missing.append("gdsfactory")
        click.echo("  gdsfactory: MISSING (pip install gdsfactory)")

    try:
        import snakemake  # noqa: F401
        click.echo("  snakemake: OK")
    except ImportError:
        missing.append("snakemake")
        click.echo("  snakemake: MISSING (pip install snakemake)")

    if missing:
        click.echo(f"\nInstall missing: pip install {' '.join(missing)}")

    click.echo("\nPulling initial state from server...")
    try:
        result = sync_pull(project_dir, server, token)
        click.echo(f"  Pulled {result['issues']} issues, {result['wiki']} wiki pages")
    except Exception as e:
        click.echo(f"  Pull failed: {e}")
        click.echo("  Run 'gds-collab-skill pull' manually when server is available.")


@cli.command()
@click.option("--dir", "project_dir", default=None, help="Project directory")
def pull(project_dir):
    """Pull issues and wiki from server to local markdown files."""
    project_dir = _resolve_project_dir(project_dir)
    state = _load_state_or_exit(project_dir)
    result = sync_pull(project_dir, state["server"], state["token"])
    click.echo(f"Pulled {result['issues']} issues, {result['wiki']} wiki pages")
    click.echo(f"Server timestamp: {result['server_timestamp']}")


@cli.command()
@click.option("--dir", "project_dir", default=None, help="Project directory")
@click.option("--commit-sha", default="", help="Git commit SHA")
def push(project_dir, commit_sha):
    """Push local changes (scripts, GDS, replies, wiki) to server."""
    project_dir = _resolve_project_dir(project_dir)
    state = _load_state_or_exit(project_dir)
    result = sync_push(project_dir, state["server"], state["token"], commit_sha)
    click.echo(f"Pushed: {len(result['accepted_scripts'])} scripts, "
               f"{len(result['accepted_gds'])} GDS files, "
               f"{len(result['replied_issues'])} issue replies, "
               f"{len(result['updated_wiki'])} wiki pages")


def _resolve_project_dir(project_dir: str | None) -> str:
    if project_dir:
        return project_dir
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, ".sync-state.json")):
        return cwd
    click.echo("Not in a project directory. Use --dir or cd into the project folder.")
    raise SystemExit(1)


def _load_state_or_exit(project_dir: str) -> dict:
    state_path = os.path.join(project_dir, ".sync-state.json")
    if not os.path.exists(state_path):
        click.echo(f"No .sync-state.json found in {project_dir}")
        click.echo("Run 'gds-collab-skill init' first.")
        raise SystemExit(1)
    with open(state_path) as f:
        return json.load(f)


SNAKEFILE_TEMPLATE = '''"""Snakemake build rules for GDS scripts."""
import glob
import os

rule all:
    input:
        expand("gds/{script}.gds", script=[os.path.basename(f).replace(".py", "") for f in glob.glob("scripts/*.py")])

rule build_gds:
    input:
        "scripts/{script}.py"
    output:
        "gds/{script}.gds"
    shell:
        "python {input}"
'''

if __name__ == "__main__":
    cli()
