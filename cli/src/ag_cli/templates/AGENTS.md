# AGENTS.md

## Project Context
This project uses Antigravity cognitive architecture.

## For AI Agents
1. Read `.antigravity/rules.md` for behavioral guidelines
2. Read `.antigravity/conventions.md` for project-specific conventions
3. Read `.antigravity/structure.md` for project code skeleton map
4. Check `.antigravity/decisions/` for architectural decisions
5. Check `.antigravity/memory/` for past reports, errors, findings, and plans

## Core Workflow: Plan → Trace → Act → Verify
- Every non-trivial task must produce a plan in `.antigravity/memory/plans/`
- Every code change must leave a trace in `.antigravity/memory/`
- Verify before claiming — run the command, read full output, then state
- Type hints and docstrings on all public functions
- Never commit secrets or force-push to main
