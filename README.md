<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### The missing cognitive layer for AI-powered IDEs.

One command. Every AI IDE becomes an expert on your codebase.

Language: **English** | [中文](README_CN.md) | [Español](README_ES.md)

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/study8677/antigravity-workspace-template/test.yml?style=for-the-badge&label=CI)](https://github.com/study8677/antigravity-workspace-template/actions)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Docs-blue?style=for-the-badge&logo=gitbook&logoColor=white)](https://deepwiki.com/study8677/antigravity-workspace-template)

<br/>

<img src="https://img.shields.io/badge/Cursor-✓-000000?style=flat-square" alt="Cursor"/>
<img src="https://img.shields.io/badge/Claude_Code-✓-D97757?style=flat-square" alt="Claude Code"/>
<img src="https://img.shields.io/badge/Windsurf-✓-06B6D4?style=flat-square" alt="Windsurf"/>
<img src="https://img.shields.io/badge/Gemini_CLI-✓-4285F4?style=flat-square" alt="Gemini CLI"/>
<img src="https://img.shields.io/badge/VS_Code_+_Copilot-✓-007ACC?style=flat-square" alt="VS Code"/>
<img src="https://img.shields.io/badge/Codex-✓-412991?style=flat-square" alt="Codex"/>
<img src="https://img.shields.io/badge/Cline-✓-FF6B6B?style=flat-square" alt="Cline"/>
<img src="https://img.shields.io/badge/Aider-✓-8B5CF6?style=flat-square" alt="Aider"/>

</div>

<br/>

<div align="center">
<img src="docs/assets/before_after.png" alt="Before vs After Antigravity" width="800"/>
</div>

<br/>

## Why Antigravity?

> An AI Agent's capability ceiling = **the quality of context it can read.**

Every AI IDE reads project files. But without structure, agents hallucinate, forget conventions, and produce inconsistent code. Antigravity solves this:

| Problem | Without Antigravity | With Antigravity |
|:--------|:-------------------|:-----------------|
| Agent forgets coding style | Repeats the same corrections | Reads `.antigravity/conventions.md` — gets it right the first time |
| Onboarding a new codebase | Agent guesses at architecture | `ag refresh` scans & documents it automatically |
| Switching between IDEs | Different rules everywhere | One `.antigravity/` folder — every IDE reads it |
| Asking "how does X work?" | Agent reads random files | `ag ask` gives grounded answers from project context |

Architecture is **files**, not plugins. `.cursorrules`, `CLAUDE.md`, `.antigravity/rules.md` — these *are* the cognitive architecture. Portable across any IDE, any LLM, zero vendor lock-in.

---

## Quick Start

```bash
# Install CLI (lightweight, no LLM dependencies)
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# Inject cognitive architecture into any project
ag init my-project && cd my-project

# Open in Cursor / Claude Code / Windsurf / any AI IDE → start prompting
```

That's it. Your IDE now reads `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md` automatically.

---

## Features at a Glance

```
  ag init           Inject context files into any project (--force to overwrite)
       │
       ▼
  .antigravity/     Shared knowledge base — every IDE reads from here
       │
       ├──► ag refresh     Multi-agent scan → auto-generated conventions.md
       ├──► ag ask         Grounded Q&A about your project
       └──► ag start-engine   Full Think-Act-Reflect agent runtime
```

**Knowledge Hub** — Multi-agent pipeline that scans your codebase, understands languages/frameworks/structure, and writes living documentation. Powered by OpenAI Agent SDK + LiteLLM, works with Gemini, OpenAI, Ollama, or any compatible API.

**Zero-Config Tools** — Drop a `.py` file into `tools/`, add type hints and a docstring. The agent discovers it automatically at startup.

**Infinite Memory** — Recursive summarization compresses conversation history. Run for hours without hitting token limits.

**Multi-Agent Swarm** — Router-Worker orchestration delegates tasks to specialist agents (Coder, Reviewer, Researcher) and synthesizes results.

---

## CLI Commands

| Command | What it does | LLM needed? |
|:--------|:-------------|:-----------:|
| `ag init <dir>` | Inject cognitive architecture templates | No |
| `ag init <dir> --force` | Re-inject, overwriting existing files | No |
| `ag refresh` | Scan project, generate `.antigravity/conventions.md` | Yes |
| `ag ask "question"` | Answer questions about the project | Yes |
| `ag report "message"` | Log a finding to `.antigravity/memory/` | No |
| `ag log-decision "what" "why"` | Log an architectural decision | No |
| `ag start-engine` | Launch the full Agent Engine runtime | Yes |

All commands accept `--workspace <dir>` to target any directory.

---

## Two Packages, One Workflow

```
antigravity-workspace-template/
├── cli/                     # ag CLI — lightweight, pip-installable
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # Agent Engine — full runtime + Knowledge Hub
    └── antigravity_engine/
        ├── agent.py         # Think-Act-Reflect loop (Gemini / OpenAI / Ollama)
        ├── hub/             # Knowledge Hub (scanner → agents → pipeline)
        ├── tools/           # Drop a .py file → auto-discovered as a tool
        ├── agents/          # Specialist agents (Coder, Reviewer, Researcher)
        ├── swarm.py         # Multi-agent orchestration (Router-Worker)
        └── sandbox/         # Code execution (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Zero LLM deps. Injects templates, logs reports & decisions offline.

**Engine** (`pip install .../engine`) — Full runtime. Powers `ag ask`, `ag refresh`, `ag start-engine`. Supports Gemini, OpenAI, Ollama, or any OpenAI-compatible API.

```bash
# Install both for full experience
pip install "git+https://...#subdirectory=cli"
pip install "git+https://...#subdirectory=engine"
```

---

## How It Works

### 1. `ag init` — Inject context files

```bash
ag init my-project
# Already initialized? Use --force to overwrite:
ag init my-project --force
```

Creates `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md`, `.windsurfrules` — each IDE reads its native config file, all pointing to the same `.antigravity/` knowledge base.

### 2. `ag refresh` — Build project intelligence

```bash
ag refresh --workspace my-project
```

Scans your codebase (languages, frameworks, structure), feeds the scan to a multi-agent pipeline, writes `.antigravity/conventions.md`. Next time your IDE opens, it reads richer context.

### 3. `ag ask` — Query your project

```bash
ag ask "How does auth work in this project?"
```

Reads `.antigravity/` context, feeds it to a reviewer agent, returns a grounded answer.

### 4. Build tools — Zero config

```python
# engine/antigravity_engine/tools/my_tool.py
def check_api_health(url: str) -> str:
    """Check if an API endpoint is responding."""
    import requests
    return "up" if requests.get(url).ok else "down"
```

Drop a file, restart. The agent discovers it automatically via type hints + docstrings.

---

## IDE Compatibility

Architecture is encoded in **files** — any agent that reads project files benefits:

| IDE | Config File |
|:----|:------------|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| Windsurf | `.windsurfrules` |
| VS Code + Copilot | `.github/copilot-instructions.md` |
| Gemini CLI / Codex | `AGENTS.md` |
| Cline | `.clinerules` |
| Google Antigravity | `.antigravity/rules.md` |

All generated by `ag init`. All reference `.antigravity/` for shared project context.

---

## Advanced Features

<details>
<summary><b>Knowledge Hub</b> — Multi-agent project intelligence pipeline</summary>

The Hub scans your project, identifies languages/frameworks/structure, and uses a multi-agent pipeline (OpenAI Agent SDK + LiteLLM) to generate living documentation:

```bash
# Generate conventions from codebase scan
ag refresh

# Only scan files changed since last refresh
ag refresh --quick

# Ask questions grounded in project context
ag ask "What testing patterns does this project use?"

# Log findings and decisions (no LLM needed)
ag report "Auth module needs refactoring"
ag log-decision "Use PostgreSQL" "Team has deep expertise"
```

Works with Gemini, OpenAI, Ollama, or any OpenAI-compatible endpoint.
</details>

<details>
<summary><b>MCP Integration</b> — Connect external tools (GitHub, databases, filesystems)</summary>

```json
// mcp_servers.json
{
  "servers": [
    {
      "name": "github",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "enabled": true
    }
  ]
}
```

Set `MCP_ENABLED=true` in `.env`. See [MCP docs](docs/en/MCP_INTEGRATION.md).
</details>

<details>
<summary><b>Multi-Agent Swarm</b> — Router-Worker orchestration for complex tasks</summary>

```python
from antigravity_engine.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("Build and review a calculator")
# Routes to Coder → Reviewer → Researcher, synthesizes results
```

See [Swarm docs](docs/en/SWARM_PROTOCOL.md).
</details>

<details>
<summary><b>Sandbox</b> — Configurable code execution environment</summary>

| Variable | Default | Options |
|:---------|:--------|:--------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | seconds |

See [Sandbox docs](docs/en/SANDBOX.md).
</details>

---

## Documentation

| | |
|:--|:--|
| 🇬🇧 English | **[`docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`docs/es/`](docs/es/)** |

---

## Contributing

Ideas are contributions too! Open an [issue](https://github.com/study8677/antigravity-workspace-template/issues) to report bugs, suggest features, or propose architecture.

## Contributors

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>Major Contributor</b> · Creative suggestions · Project administrator · Project ideation & feedback</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/devalexanderdaza">
        <img src="https://github.com/devalexanderdaza.png" width="80" /><br/>
        <b>Alexander Daza</b>
      </a><br/>
      <sub>Sandbox MVP · OpenSpec workflows · Technical analysis docs · PHILOSOPHY</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/chenyi">
        <img src="https://github.com/chenyi.png" width="80" /><br/>
        <b>Chen Yi</b>
      </a><br/>
      <sub>First CLI prototype · 753-line refactor · DummyClient extraction · Quick-start docs</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Subham-KRLX">
        <img src="https://github.com/Subham-KRLX.png" width="80" /><br/>
        <b>Subham Sangwan</b>
      </a><br/>
      <sub>Dynamic tool & context loading (#4) · Multi-agent swarm protocol (#3)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/shuofengzhang">
        <img src="https://github.com/shuofengzhang.png" width="80" /><br/>
        <b>shuofengzhang</b>
      </a><br/>
      <sub>Memory context window fix · MCP shutdown graceful handling (#28)</sub>
    </td>
  </tr>
</table>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**[📚 Full Documentation →](docs/en/)**

*Built for the AI-native development era*

</div>
