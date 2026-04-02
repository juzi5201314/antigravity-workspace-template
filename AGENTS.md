<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Agent Guide

This repo is the Antigravity Workspace Template (Python). Follow the local
rules in `.cursorrules`, `.antigravity/rules.md`, and `CONTEXT.md`.

## Must-Read Files (Before Any Work)
- `mission.md` (required by `.antigravity/rules.md`)
- `.antigravity/rules.md` (core agent behavior + coding standards)
- `CONTEXT.md` (project conventions and architecture)
- `.cursorrules` (points to the Antigravity rules engine)
- `openspec/AGENTS.md` (when planning/spec/change work is requested)

## Artifact-First Workflow
- For non-trivial tasks, create a plan file in `artifacts/plan_[task_id].md`.
- Store test/log output in `artifacts/logs/`.
- If UI is modified, include a screenshot artifact.
- Keep artifacts lightweight and deterministic.

## Build / Lint / Test Commands
### Setup
- `python3 -m venv venv && source venv/bin/activate`
- `pip install -e ./cli -e './engine[dev]'`

### Run Knowledge Hub
- `ag refresh --workspace .`
- `ag ask "How does this project work?" --workspace .`
- Engine-only entrypoints: `ag-refresh`, `ag-ask`, `ag-mcp`

### Docker
- `docker compose up --build`

### Tests
- Run all tests: `pytest engine/tests cli/tests`
- Run engine tests: `pytest engine/tests/`
- Run CLI tests: `pytest cli/tests/`
- Run a single engine test file: `pytest engine/tests/test_hub_pipeline.py -v`
- Run a single CLI test file: `pytest cli/tests/test_hub_discovery.py -v`
- Coverage: `pytest --cov=antigravity_engine engine/tests/`
- Sandbox tests: `pytest engine/tests/test_local_sandbox.py engine/tests/test_microsandbox_sandbox.py engine/tests/test_factory.py -v`

### Lint / Format
- No repo-level linter/formatter configs were found.
- Follow existing style and PEP 8; avoid reformatting unrelated code.
- Optional sanity check for tools: `python -m py_compile antigravity_engine/tools/*.py`

### CI
- GitHub Actions installs `engine/` and `cli/` separately, runs both test suites, and verifies the published CLI entrypoints (`.github/workflows/test.yml`).

## Code Style (Python)
- **Type hints are required** for all function signatures.
- **Docstrings are required** for functions/classes; use Google-style format.
  Include `Args:`, `Returns:`, and `Raises:` where applicable.
- **Use Pydantic** for data models and settings (`pydantic`, `pydantic-settings`).
- **External API calls** must be wrapped in tools under `antigravity_engine/tools/`.
- **Use `<thought>` blocks** for non-trivial logic (see `antigravity_engine/tools/example_tool.py`).
- **Imports**: stdlib → third-party → local (`antigravity_engine.`) with blank lines between.
- **Formatting**: 4-space indent, one statement per line, keep lines readable.
- **Strings**: prefer f-strings for interpolation; keep quote style consistent.

## Architecture & Patterns
- **Tool discovery**: public functions in `antigravity_engine/tools/*.py` are auto-loaded.
  Keep tool functions small, pure when possible, and well-documented.
- **MCP integration**: optional via `mcp_servers.json` and `.env`.
- **Context injection**: `.context/` markdown files are auto-loaded.
- **Memory**: JSON-based memory via `MemoryManager` (`antigravity_engine/memory.py`).

## Testing & Reliability
- Use `pytest` fixtures and `assert` statements (see `tests/`).
- Keep tests deterministic; avoid external network calls.
- Store test logs in `artifacts/logs/` per Antigravity rules.

## Notes for Agents
- The template expects a “Think → Act → Reflect” workflow.
- Avoid destructive commands (`rm -rf`, etc.).
- If a request implies a spec/proposal, follow OpenSpec flow before coding.
