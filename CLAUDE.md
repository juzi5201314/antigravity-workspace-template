# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## What This Project Is

**Antigravity Workspace Template** — a production-grade starter kit for building autonomous AI agents. Core philosophy: an agent's capability ceiling equals the quality of context it can read. Everything meaningful is encoded in files (not IDE plugins), making agents portable across any AI IDE (Cursor, Claude Code, Gemini CLI, etc.).

Built on Google Gemini (optimized for Gemini 2.0 Flash) but architecturally LLM-agnostic. Python 3.10+.

## Common Commands

### Engine Setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install -e ./cli -e './engine[dev]'
```

### Run Knowledge Hub
```bash
ag refresh --workspace .
ag ask "How does this project work?" --workspace .
ag-refresh --workspace .
ag-ask "How does auth work?"
ag-mcp --workspace .
```

### Tests
```bash
# All tests
pytest engine/tests cli/tests

# Engine tests only
pytest engine/tests/

# CLI tests only
pytest cli/tests/
```

### CLI (ag init)
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init <target_dir>
```

### Docker
```bash
docker-compose up --build
docker build -t antigravity-agent:latest .
docker build -f Dockerfile.sandbox -t antigravity-sandbox:latest .
```

CI installs `engine/` and `cli/` separately, runs both test suites, and verifies the published CLI entrypoints on Python 3.12 (`.github/workflows/test.yml`).

## Architecture

### Two-Package Monorepo

- **`engine/`** — Core agent runtime. The main codebase.
- **`cli/`** — Lightweight `ag init` command (Typer + Rich) that injects cognitive architecture files into target projects. Separate `pyproject.toml` with Hatchling.

### Engine Internals (`engine/antigravity_engine/`)

**Agent core:** `agent.py` contains `GeminiAgent` implementing the Think-Act-Reflect loop. Config in `config.py` (Pydantic Settings, workspace-aware, loads from `.env`).

**Tools** (`tools/`): Public functions are **auto-discovered** at startup and exposed to the LLM. Every tool function requires type hints on all arguments/return and a Google-style docstring with `Args:`, `Returns:`, `Raises:` sections — this is how the agent discovers and understands tools.

**Memory** (`memory.py`): Markdown-first storage (`memory/agent_memory.md` + `memory/agent_summary.md`). Uses recursive summarization to compress history and avoid token limits.

**MCP** (`mcp_client.py`): `MCPClientManager` connects to external MCP servers defined in root `mcp_servers.json`. Supports stdio/http/sse transports. Tool names prefixed with `mcp_`. Enabled via `MCP_ENABLED=true` in `.env`.

**Sandbox** (`sandbox/`): Code execution via `CodeSandbox` protocol. Factory pattern selects Local (direct Python) or Microsandbox (remote HTTP with resource limits) based on `SANDBOX_TYPE` env var.

**Swarm** (`swarm.py`): Multi-agent orchestration using Router-Worker pattern. Specialist agents in `agents/` (BaseAgent → CoderAgent, ReviewerAgent, ResearcherAgent, RouterAgent). Inter-agent communication via `MessageBus`.

**Skills** (`skills/`): Modular capabilities auto-loaded and registered into the agent's tool registry.

### Key Directories Outside Engine

- **`openspec/`** — Spec-driven development. 3-stage workflow: Create proposal → Implement → Archive. See `openspec/AGENTS.md` for details. Skip proposals for bug fixes, typos, non-breaking dep updates.
- **`artifacts/`** — Agent output: plans (`plan_*.md`), logs, error journal (`error_journal.md`), screenshots.
- **`.context/`** — Injected context: `coding_style.md` (Python style guide), `system_prompt.md`.
- **`memory/`** — Persistent markdown memory files.
- **`docs/`** — Multilingual documentation (en, zh, es).

## Code Conventions

- **Type hints mandatory** on all function signatures
- **Google-style docstrings** required on all tool functions (enables agent auto-discovery)
- **Pydantic** for data models and settings
- **Tool isolation:** All external interactions (API calls, I/O) go in `engine/antigravity_engine/tools/`
- **Stateless tools:** Context passed via arguments, not global state
- **Artifact-first:** Tasks produce plans/logs in `artifacts/` before coding begins
- **Error journal:** Mistakes logged to `artifacts/error_journal.md` with prevention rules (self-evolution pattern)

## Environment Variables

Configured via `.env` at project root. Key variables:
- `GOOGLE_API_KEY` — Gemini API key
- `GEMINI_MODEL` — Model name (default: `gemini-2.0-flash-exp`)
- `MCP_ENABLED` — Toggle MCP integration (default: `false`)
- `SANDBOX_TYPE` — `local` or `microsandbox`
- `WORKSPACE_PATH` — Project root (or use `--workspace` flag)
- `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` — OpenAI-compatible fallback (default: local Ollama)
