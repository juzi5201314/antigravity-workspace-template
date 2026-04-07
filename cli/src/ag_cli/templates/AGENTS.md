# AGENTS.md

This is the authoritative rulebook for AI agents in this repository.

## Mission
- Align work with `mission.md` when present.
- Keep a clear separation between static behavior rules (this file) and dynamic project knowledge (`.antigravity/*`).

## Mandatory Workflow: Plan -> Trace -> Act -> Verify
1. Plan non-trivial work before coding.
2. Execute in small, verifiable steps.
3. Leave a trace for meaningful changes and decisions.
4. Verify claims with real command output before reporting success.

## Coding Constraints
- Use type hints on function signatures.
- Add docstrings for public functions/classes.
- Do not silently swallow exceptions.
- Keep changes scoped; avoid unrelated refactors.

## Safety Rules
- Never commit secrets, credentials, or keys.
- Never force-push to `main`/`master`.
- Never perform destructive actions without confirmation.

## Context Loading Order
1. Read this file first.
2. Read dynamic context from `.antigravity/`:
   - `.antigravity/conventions.md`
   - `.antigravity/structure.md`
   - `.antigravity/knowledge_graph.md` (if present)
   - `.antigravity/decisions/log.md`
   - `.antigravity/memory/`
3. Read `CONTEXT.md` as a quick context index.
4. Read `mission.md` for project-specific intent (if present).

## Notes For IDE Bootstraps
IDE-specific files (`CLAUDE.md`, `.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`) are thin entrypoint shims that should defer to this file.
