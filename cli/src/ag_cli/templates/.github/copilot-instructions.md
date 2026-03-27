# GitHub Copilot Instructions

This project uses Antigravity cognitive architecture.
See `.antigravity/rules.md` for behavioral guidelines.
See `.antigravity/conventions.md` for project-specific conventions.
See `.antigravity/structure.md` for project code skeleton map.

## Core Workflow: Plan → Trace → Act → Verify
- Every non-trivial task must produce a plan in `.antigravity/memory/plans/`
- Every code change must leave a trace in `.antigravity/memory/`
- Verify before claiming — run the command, read full output, then state
- Type hints and docstrings on all public functions
- Never commit secrets or force-push to main
- Check `.antigravity/` for project context before starting work
