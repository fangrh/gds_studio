# GDS Collab Platform

A web-based collaboration platform for photonic chip design teams.

## Setup

```bash
# Backend
cd backend && pip install -r requirements.txt
# Frontend
cd frontend && npm install
# Agent skill
cd agent-skill && pip install -e .
```

## Running locally

```bash
make dev-backend   # http://localhost:8000
make dev-frontend  # http://localhost:3000
```

## Using the GDS Collab Skill

You are an AI agent co-working with the GDS Collab dashboard. When a user asks you to work on issues, follow this workflow:

### 1. Install the skill (first time only)

```bash
cd agent-skill && pip install -e .
```

Set the API URL if not running locally:

```bash
export GDS_COLLAB_API=http://localhost:8000
```

### 2. Register your session

```bash
gds-collab-skill register --agent-type claude-code --model claude-sonnet-4.6 --skill-version 0.1.0
```

Save the returned session ID for all subsequent commands.

### 3. Poll for open issues

```bash
gds-collab-skill poll
```

### 4. Work an issue

```bash
# Get full context
gds-collab-skill context <issue-id>
```

Read the issue, understand the required change to the GDSfactory Python script, and modify it.

### 5. Resolve an issue

```bash
gds-collab-skill resolve <issue-id> \
  --session-id <session-id> \
  --body "Description of what was changed and why" \
  --script-id <script-id> \
  --git-commit <commit-sha>
```

## Rules

- Every modification must use the GDSfactory API — never edit `.gds` files directly
- Always commit changes before resolving an issue
- If a fix can't be verified, post a comment instead of resolving
- The backend API is at `http://localhost:8000` unless `GDS_COLLAB_API` is set
