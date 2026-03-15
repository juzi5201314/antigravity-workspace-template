<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# Ai Workspace Template

**Production-grade starter kit for autonomous AI agents.**

*Works with any AI IDE · Any CLI · Any LLM*

Language: **English** | [中文](README_CN.md) | [Español](README_ES.md)

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Claude](https://img.shields.io/badge/Claude-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Qwen](https://img.shields.io/badge/Qwen-5A29E4?style=for-the-badge)](https://qwen.ai/)
[![GLM](https://img.shields.io/badge/GLM-1A73E8?style=for-the-badge)](https://open.bigmodel.cn/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-0A84FF?style=for-the-badge)](https://deepseek.com/)
[![MiniMax](https://img.shields.io/badge/MiniMax-FF6600?style=for-the-badge)](https://minimax.chat/)
[![Llama](https://img.shields.io/badge/Llama-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://llama.meta.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Docs-blue?style=for-the-badge&logo=gitbook&logoColor=white)](https://deepwiki.com/study8677/antigravity-workspace-template)

<br/>

<img src="https://img.shields.io/badge/Google_Antigravity-✓-4285F4?style=flat-square" alt="Antigravity"/>
<img src="https://img.shields.io/badge/Cursor-✓-000000?style=flat-square" alt="Cursor"/>
<img src="https://img.shields.io/badge/Windsurf-✓-06B6D4?style=flat-square" alt="Windsurf"/>
<img src="https://img.shields.io/badge/VS_Code_+_Copilot-✓-007ACC?style=flat-square" alt="VS Code"/>
<img src="https://img.shields.io/badge/Cline-✓-FF6B6B?style=flat-square" alt="Cline"/>
<img src="https://img.shields.io/badge/Aider-✓-8B5CF6?style=flat-square" alt="Aider"/>
<img src="https://img.shields.io/badge/Claude_Code-✓-D97757?style=flat-square" alt="Claude Code"/>
<img src="https://img.shields.io/badge/Gemini_CLI-✓-4285F4?style=flat-square" alt="Gemini CLI"/>
<img src="https://img.shields.io/badge/Codex-✓-412991?style=flat-square" alt="Codex"/>

</div>

<br/>

<div align="center">

### Stop letting Cursor / Windsurf hallucinate in empty folders.
### The **Artifact-First** cognitive architecture for AI IDEs.

<br/>

<img src="docs/assets/before_after.png" alt="Before vs After Antigravity" width="800"/>

<br/>

```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init my-project
```

</div>

<br/>

> **`ag init` → Open IDE → Prompt. That's the workflow.**
>
> **First Principles**: An AI Agent's capability ceiling = the quality of context it can read. Instead of relying on IDE plugins or platform lock-in, go back to basics—**architecture is files**. A carefully designed set of `.cursorrules`, `CONTEXT.md`, `.antigravity/rules.md` *is* the entire cognitive architecture. `ag init` injects this into any empty directory, instantly turning your IDE from an editor into an **industry-savvy architect**—no plugins, no vendor lock-in.

---

## 🌍 Universal Compatibility

This template is **not** tied to any specific IDE. It works everywhere:

| Platform | How It Works |
|:---------|:-------------|
| **Google Antigravity** | Reads `.antigravity/rules.md` for full context awareness |
| **Cursor** | Reads `.cursorrules` for project-level rules |
| **Windsurf / VS Code + Copilot** | Uses `.context/` files for knowledge injection |
| **Claude Code** | Reads `AGENTS.md` + `CONTEXT.md` for project conventions |
| **Gemini CLI** | Reads `AGENTS.md` + `.context/` for knowledge injection |
| **Codex (OpenAI)** | Reads `AGENTS.md` + directory conventions |
| **Cline / Aider** | Leverages `CONTEXT.md` + directory conventions |
| **Any OpenAI-compatible agent** | Auto-discovered tools in `engine/src/tools/`, standard Python entry |

The secret: architecture is encoded in **files**, not in IDE-specific plugins. Any agent that reads project files can benefit.

---

## ⚡ Quick Start

### Option 1: Inject architecture into any project (Recommended)

```bash
# 1. Install the CLI
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# 2. Inject cognitive architecture into your project
ag init my-project

# 3. Open in any AI IDE and start prompting!
```

### Option 2: Run the full Agent Engine

```bash
# 1. Clone the repo
git clone https://github.com/study8677/antigravity-workspace-template.git
cd antigravity-workspace-template

# 2. Install engine dependencies
cd engine
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env && nano .env

# 4. Run the agent on any workspace
python agent.py --workspace /path/to/your/project "Your task here"
```

**That's it!** The IDE auto-loads configuration and you're ready to prompt.

---

## 🎯 What Is This?

This is **not** another LangChain wrapper. It's a minimal, transparent workspace for building AI agents that:

| Feature | Description |
|:--------|:------------|
| 🧠 **Infinite Memory** | Recursive summarization compresses context automatically |
| 🧠 **True Thinking** | "Deep Think" step using Chain-of-Thought before acting |
| 🎓 **Skills System** | Modular capabilities in `engine/src/skills/` with auto-loading |
| 🛠️ **Universal Tools** | Drop Python functions in `engine/src/tools/` → auto-discovered |
| 📚 **Auto Context** | Add files to `.context/` → auto-injected into prompts |
| 🔌 **MCP Support** | Connect GitHub, databases, filesystems, custom servers |
| 🤖 **Swarm Agents** | Multi-agent orchestration with Router-Worker pattern |
| ⚡ **Gemini Native** | Optimized for Gemini 2.0 Flash |
| 🌐 **LLM Agnostic** | Use OpenAI, Azure, Ollama, or any compatible API |
| 📂 **Artifact-First** | Convention-first workflow for plans, logs, and evidence |
| 🔒 **Sandbox** | Configurable code execution (local / microsandbox) |

---

## 🏗️ Project Structure

```
antigravity-workspace-template/
│
├── cli/                          # 🖥️ Lightweight CLI (ag init)
│   ├── pyproject.toml            #    Package config & entry point
│   └── src/ag_cli/
│       ├── cli.py                #    CLI commands (init, start-engine, version)
│       └── templates/            #    Cognitive architecture templates
│           ├── .cursorrules      #    → Injected into target project
│           ├── .antigravity/     #    → Injected into target project
│           └── CONTEXT.md        #    → Injected into target project
│
├── engine/                       # ⚙️ Python Agent Engine
│   ├── agent.py                  #    Entry point (--workspace support)
│   ├── src/
│   │   ├── agent.py              #    Main agent loop (Think-Act-Reflect)
│   │   ├── config.py             #    Settings (workspace-aware)
│   │   ├── memory.py             #    Markdown memory manager
│   │   ├── mcp_client.py         #    MCP integration
│   │   ├── swarm.py              #    Multi-agent orchestration
│   │   ├── tools/                #    Custom tools (auto-discovered)
│   │   ├── agents/               #    Specialist agents
│   │   ├── sandbox/              #    Code execution sandbox
│   │   └── skills/               #    Modular skills (auto-loaded)
│   ├── tests/                    #    Test suite
│   └── requirements.txt          #    Engine dependencies
│
├── docs/                         # 📚 Documentation
├── README.md                     # This file
└── LICENSE                       # MIT
```

---

## 💡 Build a Tool in 30 Seconds

```python
# engine/src/tools/my_tool.py
def analyze_sentiment(text: str) -> str:
    """Analyzes the sentiment of given text."""
    return "positive" if len(text) > 10 else "neutral"
```

**Restart the agent.** Done! The tool is now available to any AI IDE.

---

## 🔌 MCP Integration

Connect to external tools seamlessly:

```json
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

---

## 🤖 Multi-Agent Swarm

Decompose complex tasks automatically:

```python
from engine.src.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("Build and review a calculator")
```

The swarm automatically routes to Coder, Reviewer, and Researcher agents, synthesizes results, and exposes logs via `get_message_log()`.

---

## 🔒 Sandbox Configuration

| Variable | Default | Options |
|:---------|:--------|:--------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | seconds |
| `SANDBOX_MAX_OUTPUT_KB` | `10` | KB |

<details>
<summary><b>Microsandbox extra variables</b></summary>

| Variable | Default |
|:---------|:--------|
| `MSB_SERVER_URL` | `http://127.0.0.1:5555` |
| `MSB_API_KEY` | (optional) |
| `MSB_IMAGE` | `microsandbox/python` |
| `MSB_CPU_LIMIT` | `1.0` |
| `MSB_MEMORY_MB` | `512` |
</details>

---

## 📚 Documentation

| Language | Link |
|:---------|:-----|
| 🇬🇧 English | **[`/docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`/docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`/docs/es/`](docs/es/)** |

---

## ✅ Progress

- ✅ Phase 1-8: Foundation, Memory, Tools, Swarm, MCP
- ✅ Phase 9: V1.0 Monorepo Refactor — decoupled CLI + Engine architecture
- 🚀 Phase 10: Enterprise Core (coming soon)

See [Roadmap](docs/en/ROADMAP.md) for details.

---

## 🤝 Contributing

Ideas are contributions too! Open an [issue](https://github.com/study8677/antigravity-workspace-template/issues) to report bugs, suggest features, or propose architecture.

## 👥 Contributors

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

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**[📚 Explore Full Documentation →](docs/en/)**

*Built with ❤️ for the AI-native development era*

</div>
