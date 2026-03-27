# Agent Rules

Mandatory workflow for AI agents. Every action leaves a trace.

## 1. Plan → Trace → Act → Verify

Every non-trivial task follows this loop:

1. **Plan** — Write a plan to `.antigravity/memory/plans/` before coding
2. **Act** — Execute the plan, one step at a time
3. **Trace** — Log what you did and why to `.antigravity/memory/`
4. **Verify** — Run the relevant command, read full output, then claim success

Skipping the trace step is not allowed. If you changed code, there must be a corresponding `.md` entry explaining what changed and why.

## 2. Documentation Traces

Every action produces a trace file:

| Action | Trace location | Content |
|:-------|:---------------|:--------|
| Start a task | `.antigravity/memory/plans/<date>-<name>.md` | Goal, affected files, approach |
| Make a decision | `.antigravity/decisions/log.md` | What was decided and why |
| Hit a bug | `.antigravity/memory/errors.md` | Error, root cause, fix |
| Complete a task | `.antigravity/memory/reports.md` | What was done, what to watch |
| Learn something | `.antigravity/memory/findings.md` | Discovery, implications |

Keep each entry short (3-5 lines). Date every entry.

## 3. Verify Before Claiming

Evidence before claims, always:
- Run the command that proves your assertion
- Read the full output and check exit codes
- Only then state your claim with evidence
- "Should work" or "probably fine" = not verified

## 4. Coding Constraints

- Type hints on all function signatures
- Docstrings on public functions
- Prefer explicit over implicit
- No global mutable state

## 5. Permissions

- Never modify files outside the project directory without asking
- Never commit secrets, credentials, or API keys
- Never force-push to main/master
- Never delete data without confirmation

## 6. Context Awareness

Before starting work, check:
- `.antigravity/conventions.md` — project conventions (auto-generated)
- `.antigravity/structure.md` — code skeleton map (auto-generated)
- `.antigravity/decisions/log.md` — past architectural decisions
- `.antigravity/memory/` — past reports, errors, findings, plans
