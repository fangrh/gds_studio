"""Build prompt context from platform data."""
from gds_collab_skill.client import GdsCollabClient


def build_issue_context(client: GdsCollabClient, issue_id: int) -> str:
    """Fetch an issue and its context, return a prompt-ready string."""
    issue = client.get_issue(issue_id)

    parts = [
        f"## Issue #{issue['id']}: {issue['title']}",
        f"**Priority:** {issue.get('priority', 'normal')}",
        f"**Script:** {issue.get('script_path', 'unknown')}",
        "",
        f"### Description",
        issue.get("body", ""),
        "",
    ]

    elements = issue.get("linked_elements", [])
    if elements:
        parts.append("### Linked GDS Elements")
        for el in elements:
            parts.append(
                f"- Cell: `{el.get('cell_name')}`, Layer: `{el.get('layer')}`, "
                f"Element: `{el.get('element_id')}`, "
                f"Source line: `{el.get('source_script_line')}`"
            )
            if el.get("deep_link_url"):
                parts.append(f"  Deep link: {el['deep_link_url']}")
        parts.append("")

    comments = issue.get("comments", [])
    if comments:
        parts.append("### Discussion")
        for c in comments:
            author = c.get("author_type", "unknown")
            body = c.get("body", "")
            parts.append(f"**{author}:** {body}")
            parts.append("")
        parts.append("")

    script_path = issue.get("script_path")
    if script_path:
        try:
            script_content = client.get_script(script_path)
            parts.append("### Current Script")
            parts.append("```python")
            parts.append(script_content)
            parts.append("```")
        except Exception as e:
            parts.append(f"(Could not read script: {e})")

    parts.append("")
    parts.append("### Instructions")
    parts.append(
        "Modify the script to fix this issue. Use the GDSfactory API. "
        "After modifying, rebuild the GDS and verify the fix."
    )

    return "\n".join(parts)
