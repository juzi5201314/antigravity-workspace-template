# CLAUDE.md

## Project Context
This project uses Antigravity cognitive architecture.
See `.antigravity/rules.md` for behavioral guidelines.
See `.antigravity/conventions.md` for project-specific conventions.
See `.antigravity/decisions/` for architectural decision log.
See `.antigravity/memory/` for past reports, errors, findings, and plans.

## Quick Rules
- **Plan → Trace → Act → Verify** — every non-trivial task follows this loop
- Every code change must have a corresponding `.md` trace in `.antigravity/memory/`
- Verify before claiming — run the command, read the output, then state your claim
- Type hints and docstrings on all public functions
- Never commit secrets or force-push to main
- Check `.antigravity/` for project context before starting work
