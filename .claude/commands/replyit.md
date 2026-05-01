---
name: replyit
description: Pull issues from server, fix scripts, rebuild GDS, push results. Uses sync API with local project folder.
allowed-tools: Bash(gh:*), Bash(git:*), Bash(python:*), Bash(gds-collab-skill:*), Bash(snakemake:*), Bash(curl:*), Read, Write, Edit, Glob, Grep, Agent
---

# /replyit — GDS Collab Agent Skill (Sync Mode)

You are an AI agent working on the GDS Collab Platform. Your job is to resolve
open issues and reply to user comments on photonic chip designs.

## Setup (first run only)

```bash
cd agent-skill && pip install -e .
```

## Detect project mode

Check if you are in a project directory with `.sync-state.json`:
```bash
cat .sync-state.json
```

If the file exists, use **sync mode** (pull → modify → build → push).
If not, fall back to **direct mode** (register → poll → context → resolve).

---

## Sync Mode Workflow

### Step 1: Pull from server

```bash
gds-collab-skill pull
```

This syncs issues and wiki from the server to local markdown files in `issues/` and `wiki/`.

### Step 2: Read issues

Read all markdown files in `issues/`. Each file has YAML frontmatter with:
- id, title, status, priority, script path, linked elements
- Discussion comments from users and agents

### Step 3: Process each open issue

For each issue with status `open` or `in_progress`:

a. Read the linked script from `scripts/` if it exists

b. Understand what needs to change in the GDSfactory script

c. Modify the Python script using GDSfactory API

d. Rebuild affected GDS files with snakemake:
   ```bash
   snakemake -j1
   ```

e. If build fails, post a comment on the issue in the markdown file:
   Add under ## Comments:
   `- **agent** (<timestamp>): PUSH_REPLY: Build failed: <error>`

f. If build succeeds, add an agent reply in the markdown file:
   Add under ## Comments:
   `- **agent** (<timestamp>): PUSH_REPLY: Fixed <description>`

### Step 4: Commit and push code changes

```bash
git add scripts/ gds/
git commit -m "fix: resolve issues — <short description>"
git push origin main
```

### Step 5: Push to server

```bash
gds-collab-skill push --commit-sha <sha>
```

This syncs updated scripts, GDS files, issue replies, and wiki back to the server.

### Step 6: Summary

Report what was pulled, fixed, and pushed.

---

## Direct Mode Workflow (fallback, no .sync-state.json)

### Step 1: Register session

```bash
gds-collab-skill register --agent-type claude-code --model claude-sonnet-4.6 --skill-version 0.1.0
```

### Step 2: Check for unreplied comments

```bash
gds-collab-skill unreplied
```

For each unreplied comment, dispatch a subagent to handle it.

### Step 3: Poll for open issues

```bash
gds-collab-skill poll
```

### Step 4: For each issue, fix and resolve

```bash
gds-collab-skill context <issue-id>
# Modify script, test, commit
python <script-path>
git add <script-path> && git commit -m "fix: resolve issue #<id>"
git push origin main
gds-collab-skill resolve <issue-id> --session-id <id> --body "..." --git-commit <sha>
```

## Error handling

- If snakemake build fails, post the error as a comment, do not resolve
- If push fails, retry up to 3 times with backoff (1s, 2s, 4s)
- If pull fails (server unreachable), report and stop

## Rules

- Every modification must use the GDSfactory API
- Never modify GDS files directly — only the Python source scripts
- Always commit and push to trigger Argo CI/CD (GitHub Actions → GHCR → Argo CD → k8s)
- If the fix can't be verified, leave a comment instead of resolving
- User comments waiting for a reply take priority over new issues
