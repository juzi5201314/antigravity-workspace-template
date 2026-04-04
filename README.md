<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### Multi-agent knowledge engine for any codebase.

`ag-refresh` builds a knowledge base. `ag-ask` answers questions. Any LLM, any IDE.

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

The engine is the core: `ag-refresh` deploys a multi-agent cluster that autonomously reads your code — each module gets its own Agent that generates a knowledge doc. `ag-ask` routes questions to the right Agent, grounded in real code with file paths and line numbers.

**Tested on a real 374-file project with MiniMax2.7 — scored 9/10 on basic Q&A, 9/10 on hallucination resistance.** [See full eval below.](#real-world-eval-minimax27-on-opencmo-374-files-29k-lines)

```
Traditional approach:              Antigravity approach:
  CLAUDE.md = 5000 lines of docs     Claude Code calls ask_project("how does auth work?")
  Agent reads it all, forgets most   Router → ModuleAgent reads actual source, returns exact answer
  Hallucination rate stays high      Grounded in real code, file paths, and git history
```

| Problem | Without Antigravity | With Antigravity |
|:--------|:-------------------|:-----------------|
| Agent forgets coding style | Repeats the same corrections | Reads `.antigravity/conventions.md` — gets it right the first time |
| Onboarding a new codebase | Agent guesses at architecture | `ag-refresh` → ModuleAgents self-learn each module |
| Switching between IDEs | Different rules everywhere | One `.antigravity/` folder — every IDE reads it |
| Asking "how does X work?" | Agent reads random files | `ask_project` MCP → Router routes to the responsible ModuleAgent |

Architecture is **files + a live Q&A engine**, not plugins. Portable across any IDE, any LLM, zero vendor lock-in.

---

## Quick Start

**Option A — Engine: multi-agent Q&A on your codebase (recommended)**
```bash
# 1. Install engine + CLI
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli"
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 2. Configure .env with any OpenAI-compatible API key
cd my-project
cat > .env <<EOF
OPENAI_BASE_URL=https://your-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
AG_ASK_TIMEOUT_SECONDS=120
EOF

# 3. Build knowledge base (ModuleAgents self-learn each module)
ag-refresh --workspace .

# 4. Ask anything
ag-ask "How does auth work in this project?"

# 5. (Optional) Register as MCP server for Claude Code
claude mcp add antigravity ag-mcp -- --workspace $(pwd)
```

**Option B — Context files only (any IDE, no LLM needed)**
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init my-project && cd my-project
# IDE reads .antigravity/rules.md, .cursorrules, CLAUDE.md, AGENTS.md automatically
```

---

## Features at a Glance

```
  ag init             Inject context files into any project (--force to overwrite)
       │
       ▼
  .antigravity/       Shared knowledge base — every IDE reads from here
       │
       ├──► ag-refresh     Dynamic multi-agent self-learning → module knowledge docs + structure map
       ├──► ag-ask         Router → ModuleAgent Q&A with live code evidence
       └──► ag-mcp         MCP server → Claude Code calls directly
```

**Dynamic Multi-Agent Cluster** — During `ag-refresh`, each code module gets a RefreshModuleAgent that autonomously reads the code and generates a deep knowledge doc. A **RegistryAgent** then summarizes all modules into a semantic registry. During `ag-ask`, Router reads the registry to understand *what each module is responsible for* and routes questions to the right ModuleAgent. Agents can handoff across modules. Powered by OpenAI Agent SDK + LiteLLM.

**GitAgent** — A dedicated agent for analyzing git history — understands who changed what and why.

**GitNexus Enhancement (optional)** — Install GitNexus to auto-unlock semantic search, call graphs, and impact analysis for every ModuleAgent.

---

## CLI Commands

| Command | What it does | LLM needed? |
|:--------|:-------------|:-----------:|
| `ag init <dir>` | Inject cognitive architecture templates | No |
| `ag init <dir> --force` | Re-inject, overwriting existing files | No |
| `ag refresh --workspace <dir>` | CLI convenience wrapper around the knowledge-hub refresh pipeline | Yes |
| `ag ask "question" --workspace <dir>` | CLI convenience wrapper around the routed project Q&A flow | Yes |
| `ag-refresh` | Multi-agent self-learning of codebase, generates module knowledge docs + `conventions.md` + `structure.md` | Yes |
| `ag-ask "question"` | Router → ModuleAgent/GitAgent routed Q&A | Yes |
| `ag-mcp --workspace <dir>` | **Start MCP server** — exposes `ask_project` + `refresh_project` to Claude Code | Yes |
| `ag report "message"` | Log a finding to `.antigravity/memory/` | No |
| `ag log-decision "what" "why"` | Log an architectural decision | No |

`ag ask` / `ag refresh` are available when both `cli/` and `engine/` are installed. `ag-ask` / `ag-refresh` are the engine-only entrypoints.

---

## Two Packages, One Workflow

```
antigravity-workspace-template/
├── cli/                     # ag CLI — lightweight, pip-installable
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # Multi-agent engine + Knowledge Hub
    └── antigravity_engine/
        ├── _cli_entry.py    # ag-ask / ag-refresh / ag-mcp + python -m dispatch
        ├── config.py        # Pydantic configuration
        ├── hub/             # ★ Core: multi-agent cluster
        │   ├── agents.py    #   Router + ModuleAgent + GitAgent
        │   ├── ask_pipeline.py
        │   ├── refresh_pipeline.py
        │   ├── ask_tools.py
        │   ├── scanner.py
        │   ├── structure.py
        │   ├── knowledge_graph.py
        │   ├── retrieval_graph.py
        │   ├── pipeline.py  #   compatibility re-export shim
        │   └── mcp_server.py
        ├── mcp_client.py    # MCP consumer (connects external tools)
        ├── memory.py        # Persistent interaction memory
        ├── tools/           # MCP query tools + extensions
        ├── skills/          # Skill loader
        └── sandbox/         # Code execution (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Zero LLM deps. Injects templates, logs reports & decisions offline.

**Engine** (`pip install .../engine`) — Multi-agent runtime. Powers `ag-ask`, `ag-refresh`, `ag-mcp`. Supports Gemini, OpenAI, Ollama, or any OpenAI-compatible API.

**New skill packaging updates:**
- `engine/antigravity_engine/skills/graph-retrieval/` — graph-oriented retrieval tools for structure and call-path reasoning.
- `engine/antigravity_engine/skills/knowledge-layer/` — project knowledge-layer tools for semantic context consolidation.

```bash
# Install both for full experience
pip install "git+https://...#subdirectory=cli"
pip install "git+https://...#subdirectory=engine"
```

For local work on this repository itself:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ./cli -e './engine[dev]'
pytest engine/tests cli/tests
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

### 2. `ag-refresh` — Multi-agent self-learning

```bash
ag-refresh --workspace my-project
```

**8-step pipeline:**
1. Scan codebase (languages, frameworks, structure)
2. Multi-agent pipeline generates `conventions.md`
3. Generate `structure.md` structure map
4. Build knowledge graph (`knowledge_graph.json` + mermaid)
5. Write document/data/media indexes
6. **Dynamically create RefreshModuleAgents** — one per code module, each autonomously reads code and writes a deep knowledge doc to `.antigravity/modules/*.md`
7. **RefreshGitAgent** analyzes git history, generates `_git_insights.md`
8. **RegistryAgent** reads all knowledge artifacts → calls LLM → generates `module_registry.md` (2-3 sentence semantic description per module, used by Router for intelligent routing)

### 3. `ag-ask` — Router-based Q&A

```bash
ag-ask "How does auth work in this project?"
```

Router reads the `structure.md` map and routes questions to the right **ModuleAgent** (pre-loaded with that module's knowledge doc) or **GitAgent** (understands git history). For cross-module questions, agents can handoff to each other.

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
<summary><b>MCP Server — Give Claude Code a ChatGPT for your codebase</b></summary>

Instead of reading hundreds of documentation files, Claude Code can call `ask_project` as a live tool — backed by a dynamic multi-agent cluster: Router routes questions to the right ModuleAgent, returning grounded answers with file paths and line numbers.

**Setup:**

```bash
# Install engine
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# Refresh knowledge base first (ModuleAgents self-learn each module)
ag-refresh --workspace /path/to/project

# Register as MCP server in Claude Code
claude mcp add antigravity ag-mcp -- --workspace /path/to/project
```

**Tools exposed to Claude Code:**

| Tool | What it does |
|:-----|:-------------|
| `ask_project(question)` | Router → ModuleAgent/GitAgent answers codebase questions. Returns file paths + line numbers. |
| `refresh_project(quick?)` | Rebuild knowledge base after significant changes. ModuleAgents re-learn the code. |

</details>

<details>
<summary><b>Dynamic Multi-Agent Cluster</b> — Module-level self-learning + intelligent routing</summary>

The engine's core is **a dynamically created Agent cluster per code module**:

```
 ag-refresh:                              ag-ask:

 ┌─ RefreshModule_engine ──→ engine.md    Router (reads module_registry.md)
 ├─ RefreshModule_cli ────→ cli.md           ├──→ Module_engine (pre-loaded engine.md)
 ├─ RefreshGitAgent ──────→ _git.md          ├──→ Module_cli (pre-loaded cli.md)
 └─ RegistryAgent ────────→ registry.md      ├──→ GitAgent (pre-loaded _git.md)
                                             └──→ Agents can handoff to each other
```

**Key: `module_registry.md`** — During refresh, a RegistryAgent reads all module knowledge and generates a concise semantic description per module. The Router reads this registry to make routing decisions — it knows *what each module is responsible for*, not just what files it contains. This is what enables the Router to correctly route "database schema" → `src_storage` instead of guessing from file names.

```bash
# ModuleAgents self-learn your codebase
ag-refresh

# Only scan files changed since last refresh
ag-refresh --quick

# Router intelligently routes to the right ModuleAgent
ag-ask "What testing patterns does this project use?"

# Log findings and decisions (no LLM needed)
ag report "Auth module needs refactoring"
ag log-decision "Use PostgreSQL" "Team has deep expertise"
```

Works with Gemini, OpenAI, Ollama, or any OpenAI-compatible endpoint. Powered by OpenAI Agent SDK + LiteLLM.
</details>

<details>
<summary><b>MCP Integration (Consumer)</b> — Let agents call external tools</summary>

`MCPClientManager` lets your agents connect to external MCP servers (GitHub, databases, etc.), auto-discovering and registering tools.

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

Set `MCP_ENABLED=true` in `.env`.
</details>

<details>
<summary><b>GitNexus Integration</b> — Optional deep code intelligence via knowledge graph</summary>

[GitNexus](https://github.com/abhigyanpatwari/GitNexus) is a **third-party tool** that builds a code knowledge graph using Tree-sitter AST parsing. Antigravity provides built-in integration hooks — when you install GitNexus separately, `ag-ask` automatically detects it and unlocks three additional tools:

| Tool | What it does |
|:-----|:-------------|
| `gitnexus_query` | Hybrid search (BM25 + semantic) — better than grep for "how does auth work?" |
| `gitnexus_context` | 360-degree symbol view: callers, callees, references, definition |
| `gitnexus_impact` | Blast radius analysis — what breaks if you change a symbol? |

> **Note:** GitNexus is NOT bundled with Antigravity. It is an independent project that requires separate installation via npm. Antigravity works fully without it — GitNexus is an optional enhancement for deeper code understanding.

**How to enable (3 steps):**

```bash
# 1. Install GitNexus (requires Node.js)
npm install -g gitnexus

# 2. Index your project (one-time, creates a local knowledge graph)
cd my-project
gitnexus analyze .

# 3. Use ag-ask as usual — GitNexus tools are auto-detected
ag-ask "How does the authentication flow work?"
```

**How the integration works:** `ask_tools.py` checks if the `gitnexus` CLI is available on your system. If found, it registers `gitnexus_query`, `gitnexus_context`, and `gitnexus_impact` as additional tools for every ModuleAgent. If not found, these tools are simply absent — zero overhead, no errors.
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

## Real-World Eval: MiniMax2.7 on OpenCMO (374 files, 29K lines)

Tested end-to-end against the [OpenCMO](https://github.com/study8677/OpenCMO) codebase (Python + React/TS, 374 files) using **MiniMax2.7** via an OpenAI-compatible router.

### Refresh results

```
$ ag-refresh --workspace /path/to/OpenCMO
[1/3] Scanning project... 374 files, 0.02s
[2/3] Analyzing with multi-agent swarm...
      conventions.md    ✅ 289 lines
      structure.md      ✅ 1384 lines
      knowledge_graph   ✅ 540KB JSON + mermaid
[8/8] Generating module registry...
      module_registry   ✅ 9 modules with semantic descriptions
```

### Ask evaluation matrix (18 tests)

| Category | Question | Result | Quality |
|:---------|:---------|:------:|:-------:|
| Basic understanding | "What is this project?" | **Pass** | 5/5 — accurate summary with tech details |
| Tech stack | "What tech stack and frameworks?" | **Pass** | 5/5 — frontend + backend + libs listed |
| Module listing | "List all main modules" | **Pass** | 5/5 — table format, accurate |
| API routing | "How does API routing work?" | **Pass** | 5/5 — routes + endpoints + client code |
| Precise function | "get_model() in llm.py signature" | **Pass** | 5/5 — **100% accurate** file, line, logic |
| Hallucination test | "Does this support GraphQL?" | **Pass** | 5/5 — correctly said **No** with 4-point evidence |
| Chinese query | "社区监控支持哪些平台?" | **Pass** | 5/5 — Chinese answer, platform style table |
| Database schema | "List all database tables" | **Pass** | 5/5 — 34 tables listed with source file (registry-routed to src_storage) |
| Approval workflow | "How does approval work?" | **Pass** | 5/5 — full state machine with line numbers |
| Empty/garbage input | "" / "AAAA...×5000" | **Pass** | 4/5 — graceful handling |
| Complex architecture | "How does multi-agent work?" (120s) | **Pass** | 5/5 — 20 agents listed, comm patterns, diagrams |
| End-to-end tracing | "Trace create project flow" | **Timeout** | 1/5 — needs >45s |
| Security analysis | "Security concerns?" | **Timeout** | 1/5 — needs >45s |
| External comparison | "Compare with Langchain" | **Timeout** | 1/5 — external knowledge required |

### Capability boundary summary

```
 ✅ Strong (reliable)                    ⚠️ Conditional                     ❌ Weak
 ─────────────────────                   ──────────────                     ────────
 Project-level understanding             Complex arch questions             File retrieval accuracy
 Precise function lookup                 (set TIMEOUT=120 to fix)           Deep ORM/schema inference
 Hallucination resistance                                                   External knowledge comparison
 Multi-language (zh/en)                                                     Timeout fallback quality
 Edge-case handling
```

### Scores

| Dimension | Score | Notes |
|:----------|:-----:|:------|
| Basic Q&A | **9/10** | Project, tech stack, modules — excellent |
| Code location | **7/10** | Precise queries great; same-name files can confuse |
| Deep analysis | **4/10** | Timeout-bound; **7/10 at 120s** |
| Hallucination control | **9/10** | Won't fabricate; gives negative evidence |
| Multi-language | **9/10** | Chinese Q&A excellent |
| Robustness | **9/10** | Empty, garbage, action requests all handled |
| **Overall** | **7/10** | **Daily code Q&A: production-ready. Complex analysis: tune timeout.** |

> Full evaluation report: [`artifacts/plan_20260404_opencmo_ask_boundary_eval.md`](artifacts/plan_20260404_opencmo_ask_boundary_eval.md)

### Quick config for best results

```bash
# .env — recommended settings after eval
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model

# The single most impactful tuning: raise ask timeout from 45s to 120s
AG_ASK_TIMEOUT_SECONDS=120
AG_REFRESH_AGENT_TIMEOUT_SECONDS=180
AG_MODULE_AGENT_TIMEOUT_SECONDS=90
```

> Works with any OpenAI-compatible provider: **NVIDIA**, **OpenAI**, **Ollama**, **vLLM**, **LM Studio**, **Groq**, **MiniMax**, etc.

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
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/goodmorning10">
        <img src="https://github.com/goodmorning10.png" width="80" /><br/>
        <b>goodmorning10</b>
      </a><br/>
      <sub>Enhanced <code>ag ask</code> context loading — added CONTEXT.md, AGENTS.md, and memory/*.md as context sources (#29)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/abhigyanpatwari">
        <img src="https://github.com/abhigyanpatwari.png" width="80" /><br/>
        <b>Abhigyan Patwari</b>
      </a><br/>
      <sub><a href="https://github.com/abhigyanpatwari/GitNexus">GitNexus</a> — code knowledge graph natively integrated into <code>ag ask</code> for symbol search, call graphs, and impact analysis</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/BBear0115">
        <img src="https://github.com/BBear0115.png" width="80" /><br/>
        <b>BBear0115</b>
      </a><br/>
      <sub>Skill packaging & KG retrieval enhancements · Multi-language README sync (#30)</sub>
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
