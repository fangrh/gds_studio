---
name: gds-collab/replyit
description: Process pending GDS Collab issues - poll, fix, rebuild, resolve
allowed-tools: Bash(gh:*), Bash(git:*), Bash(python:*), Bash(gds-collab-skill:*), Read, Write, Edit, Glob, Grep
---

# /replyit — GDS Collab Agent Skill

You are an AI agent working on the GDS Collab Platform. Your job is to resolve
open issues filed against photonic chip designs.

## Workflow

1. **Register your session:**
   ```bash
   gds-collab-skill register --agent-type claude-code --model <your-model> --skill-version 0.1.0
   ```
   Save the session ID.

2. **Poll for open issues:**
   ```bash
   gds-collab-skill poll
   ```

3. **For each issue:**
   a. Get full context:
      ```bash
      gds-collab-skill context <issue-id>
      ```
   b. Read the issue description, linked elements, and current script
   c. Understand what needs to change in the GDSfactory script
   d. Modify the Python script using GDSfactory API
   e. Test the fix by running the script
   f. Commit the change to git
   g. Resolve the issue:
      ```bash
      gds-collab-skill resolve <issue-id> \
        --session-id <session-id> \
        --body "What was changed and why" \
        --script-id <script-id> \
        --git-commit <commit-sha>
      ```

## Rules

- Every modification must use the GDSfactory API
- Never modify GDS files directly — only the Python source scripts
- Always commit changes before resolving
- If the fix can't be verified, leave a comment instead of resolving
- Mark issues you can't fix with a comment explaining why
