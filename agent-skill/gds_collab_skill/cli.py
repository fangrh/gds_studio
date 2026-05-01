"""CLI for the GDS Collab Skill. Invoked as `gds-collab-skill <command>`."""
import click
from gds_collab_skill.client import GdsCollabClient
from gds_collab_skill.context import build_issue_context
from gds_collab_skill.post import post_response


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


if __name__ == "__main__":
    cli()
