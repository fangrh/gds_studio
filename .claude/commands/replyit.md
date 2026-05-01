---
name: replyit
description: Process pending GDS Collab issues - poll, fix, rebuild, resolve. Auto-detects unreplied user comments and dispatches subagents.
allowed-tools: Bash(gh:*), Bash(git:*), Bash(python:*), Bash(gds-collab-skill:*), Bash(curl:*), Read, Write, Edit, Glob, Grep, Agent
---

# /replyit — GDS Collab Agent Skill

You are an AI agent working on the GDS Collab Platform. Your job is to resolve
open issues and reply to user comments on photonic chip designs.

## Setup (first run only)

```bash
cd agent-skill && pip install -e .
export GDS_COLLAB_API=http://localhost:8000
```

## Main Workflow

### Step 1: Register session

```bash
gds-collab-skill register --agent-type claude-code --model claude-sonnet-4.6 --skill-version 0.1.0
```

Save the returned session ID as `$SESSION_ID` for all subsequent commands.

### Step 2: Check for unreplied user comments FIRST

```bash
gds-collab-skill unreplied
```

This returns issues where users commented but no agent has replied yet. **These take priority** because a human is waiting for a response.

**For each unreplied comment**, dispatch a subagent using the Agent tool:

```
Agent({
  description: "Reply to comment on issue #<id>",
  prompt: `
You are a GDS Collab subagent handling a user comment on issue #<issue-id>.

## Context
Issue: <issue-title> (<issue-status>)
Script: <script-path>
User comment: "<comment-body>"

## Your task
1. Read the issue's script file if it exists: <script-path>
2. Understand what the user is asking for in their comment
3. If the comment requests a code change:
   a. Modify the Python script using GDSfactory API
   b. Test by running: python <script-path>
   c. Commit and push: git add <script-path> && git commit -m "fix: address comment on issue #<issue-id>" && git push origin main
   d. Reply via API: curl -s -X POST $GDS_COLLAB_API/api/agent/comment -H "Content-Type: application/json" -d '{"issue_id": <issue-id>, "body": "<what you changed and why>", "session_id": <session-id>}'
4. If the comment is a question (no code change needed):
   a. Reply with a helpful answer via the same comment API
5. If the comment requires clarification:
   a. Reply asking for clarification

Report back: what you did, whether you made code changes, and the reply you posted.
  `
})
```

Wait for each subagent to complete before moving on. Collect results.

### Step 3: Poll for new open issues

```bash
gds-collab-skill poll
```

If no open issues, report the unreplied comment results (if any) and stop.

### Step 4: For each new open issue (in priority order)

Process each issue that was NOT already handled in Step 2:

a. Get full context:
   ```bash
   gds-collab-skill context <issue-id>
   ```

b. Read the issue description, linked elements, and the current script

c. Understand what needs to change in the GDSfactory script

d. Modify the Python script using GDSfactory API

e. Test the fix:
   ```bash
   python <script-path>
   ```

f. Commit and push to trigger CI/CD:
   ```bash
   git add <script-path>
   git commit -m "fix: resolve issue #<issue-id> — <short description>"
   git push origin main
   ```
   The push triggers GitHub Actions → GHCR → Argo CD auto-deploy.

g. Resolve the issue:
   ```bash
   gds-collab-skill resolve <issue-id> \
     --session-id <session-id> \
     --body "What was changed and why" \
     --script-id <script-id> \
     --git-commit <commit-sha>
   ```

### Step 5: Summary

Report:
- Unreplied comments handled: N (with/without code changes)
- New issues resolved: N
- Issues that couldn't be fixed: N (with reasons)

## Error handling

- If a fix cannot be verified, post a comment instead of resolving
- If a subagent fails, log it and continue to the next item
- If the comment is unclear, reply asking for clarification rather than guessing

## Rules

- Every modification must use the GDSfactory API
- Never modify GDS files directly — only the Python source scripts
- Always commit changes before resolving
- If the fix can't be verified, leave a comment instead of resolving
- User comments waiting for a reply take priority over new issues
- The backend API is at `http://localhost:8000` unless `GDS_COLLAB_API` is set
- Always `git push` after committing to trigger the Argo CI/CD pipeline (GitHub Actions → GHCR → Argo CD → k8s)
