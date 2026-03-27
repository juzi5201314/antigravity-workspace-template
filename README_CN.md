<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### AI IDE 缺失的认知层。

一条命令，让每个 AI IDE 都成为你代码库的专家。

语言: [English](README.md) | **中文** | [Español](README_ES.md)

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

## 为什么选择 Antigravity？

> AI Agent 的能力上限 = **它能读到的上下文质量。**

每个 AI IDE 都会读项目文件。但缺乏结构时，Agent 会产生幻觉、忘记规范、生成不一致的代码。Antigravity 解决这些问题：

| 痛点 | 没有 Antigravity | 有 Antigravity |
|:----|:----------------|:--------------|
| Agent 忘记代码风格 | 反复纠正同样的问题 | 读取 `.antigravity/conventions.md` —— 一次到位 |
| 接手新代码库 | Agent 只能猜测架构 | `ag refresh` 自动扫描并文档化 |
| 切换 IDE | 每个 IDE 规则不同 | 一个 `.antigravity/` 目录 —— 所有 IDE 共享 |
| 问"X 怎么实现的？" | Agent 胡乱翻文件 | `ag ask` 基于项目上下文给出准确回答 |

架构即**文件**，而非插件。`.cursorrules`、`CLAUDE.md`、`.antigravity/rules.md` —— 这些就是认知架构本身。跨 IDE、跨 LLM、零平台锁定。

---

## 快速开始

```bash
# 安装 CLI（轻量，无 LLM 依赖）
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# 将认知架构注入任意项目
ag init my-project && cd my-project

# 用 Cursor / Claude Code / Windsurf / 任何 AI IDE 打开 → 开始提示
```

就这么简单。你的 IDE 会自动读取 `.antigravity/rules.md`、`.cursorrules`、`CLAUDE.md`、`AGENTS.md`。

---

## 功能一览

```
  ag init           将上下文文件注入任意项目（--force 可覆盖已有文件）
       │
       ▼
  .antigravity/     共享知识库 —— 所有 IDE 从这里读取
       │
       ├──► ag refresh     多 Agent 扫描 → 生成 conventions.md + structure.md
       ├──► ag ask         Router-Worker 问答，结合上下文与代码证据
       └──► ag start-engine   完整 Think-Act-Reflect Agent 运行时
```

**知识中枢（Knowledge Hub）** —— 多 Agent 管道扫描代码库，理解语言/框架/结构，生成活文档，并额外产出项目结构图供后续问答使用。基于 OpenAI Agent SDK + LiteLLM，支持 Gemini、OpenAI、Ollama 或任何兼容 API。

**零配置工具** —— 将 `.py` 文件放入 `tools/`，添加类型提示和 docstring。Agent 启动时自动发现。

**无限记忆** —— 递归摘要压缩对话历史，长时间运行不受 Token 限制。

**多 Agent Swarm** —— Router-Worker 编排将任务分配给专家 Agent（Coder、Reviewer、Researcher），综合输出结果。

---

## CLI 命令

| 命令 | 功能 | 需要 LLM？ |
|:-----|:-----|:----------:|
| `ag init <dir>` | 注入认知架构模板 | 否 |
| `ag init <dir> --force` | 重新注入，覆盖已有文件 | 否 |
| `ag refresh` | 扫描项目，生成 `.antigravity/conventions.md` 和 `.antigravity/structure.md` | 是 |
| `ag ask "问题"` | 结合共享上下文和受限代码探索能力回答项目问题 | 是 |
| `ag report "内容"` | 记录发现到 `.antigravity/memory/` | 否 |
| `ag log-decision "决策" "原因"` | 记录架构决策 | 否 |
| `ag start-engine` | 启动完整 Agent Engine 运行时 | 是 |

所有命令支持 `--workspace <dir>` 参数指向任意目录。

---

## 两个包，一套工作流

```
antigravity-workspace-template/
├── cli/                     # ag CLI — 轻量，pip 可安装
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # Agent Engine — 完整运行时 + 知识中枢
    └── antigravity_engine/
        ├── agent.py         # Think-Act-Reflect 循环 (Gemini / OpenAI / Ollama)
        ├── hub/             # 知识中枢（扫描器 → Agent → 管道）
        ├── tools/           # 放入 .py 文件 → 自动发现为工具
        ├── agents/          # 专家 Agent（Coder、Reviewer、Researcher）
        ├── swarm.py         # 多 Agent 编排（Router-Worker）
        └── sandbox/         # 代码执行（local / microsandbox）
```

**CLI**（`pip install .../cli`）—— 零 LLM 依赖。注入模板，离线记录报告和决策。

**Engine**（`pip install .../engine`）—— 完整运行时。驱动 `ag ask`、`ag refresh`、`ag start-engine`。支持 Gemini、OpenAI、Ollama 或任何 OpenAI 兼容 API。

```bash
# 安装两者获取完整体验
pip install "git+https://...#subdirectory=cli"
pip install "git+https://...#subdirectory=engine"
```

---

## 工作原理

### 1. `ag init` — 注入上下文文件

```bash
ag init my-project
# 已经初始化过？用 --force 覆盖：
ag init my-project --force
```

创建 `.antigravity/rules.md`、`.cursorrules`、`CLAUDE.md`、`AGENTS.md`、`.windsurfrules` —— 每个 IDE 读取各自的原生配置文件，全部指向同一个 `.antigravity/` 知识库。

### 2. `ag refresh` — 构建项目智能

```bash
ag refresh --workspace my-project
```

扫描代码库（语言、框架、结构），将扫描结果送入多 Agent 管道，生成 `.antigravity/conventions.md`，并额外产出 `.antigravity/structure.md` 作为代码骨架图，供后续问答使用。下次 IDE 打开时读取到更丰富的上下文。

### 3. `ag ask` — 查询项目

```bash
ag ask "这个项目的认证逻辑是怎么实现的？"
```

读取 `.antigravity/structure.md`、`.antigravity/conventions.md`、项目文档和记忆日志，再通过带受限代码搜索工具的 Router-Worker ask swarm 返回有依据的回答。

### 4. 构建工具 — 零配置

```python
# engine/antigravity_engine/tools/my_tool.py
def check_api_health(url: str) -> str:
    """检查 API 端点是否在线。"""
    import requests
    return "up" if requests.get(url).ok else "down"
```

放入文件，重启即可。Agent 通过类型提示 + docstring 自动发现工具。

---

## IDE 兼容性

架构编码在**文件**中 —— 任何能读项目文件的 Agent 都能受益：

| IDE | 配置文件 |
|:----|:---------|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| Windsurf | `.windsurfrules` |
| VS Code + Copilot | `.github/copilot-instructions.md` |
| Gemini CLI / Codex | `AGENTS.md` |
| Cline | `.clinerules` |
| Google Antigravity | `.antigravity/rules.md` |

均由 `ag init` 生成，均指向 `.antigravity/` 共享项目上下文。

---

## 进阶功能

<details>
<summary><b>知识中枢（Knowledge Hub）</b> — 多 Agent 项目智能管道</summary>

Hub 扫描你的项目，识别语言/框架/结构，通过多 Agent 管道（OpenAI Agent SDK + LiteLLM）生成活文档，并额外产出结构图供后续路由问答：

```bash
# 从代码扫描生成规范文档和结构图
ag refresh

# 仅扫描上次刷新后变更的文件
ag refresh --quick

# 基于项目上下文和实时代码证据提问
ag ask "这个项目用了什么测试模式？"

# 记录发现和决策（无需 LLM）
ag report "认证模块需要重构"
ag log-decision "使用 PostgreSQL" "团队有丰富经验"
```

支持 Gemini、OpenAI、Ollama 或任何 OpenAI 兼容端点。
</details>

<details>
<summary><b>MCP 集成</b> — 连接外部工具（GitHub、数据库、文件系统）</summary>

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

在 `.env` 中设置 `MCP_ENABLED=true`。详见 [MCP 文档](docs/zh/MCP_INTEGRATION.md)。
</details>

<details>
<summary><b>GitNexus 集成</b> — 可选的深度代码智能增强（第三方工具）</summary>

[GitNexus](https://github.com/abhigyanpatwari/GitNexus) 是一个**第三方工具**，通过 Tree-sitter AST 解析构建代码知识图谱。Antigravity 提供了内置的集成接口——当你单独安装 GitNexus 后，`ag ask` 会自动检测并解锁三个额外工具：

| 工具 | 功能 |
|:-----|:-----|
| `gitnexus_query` | 混合搜索（BM25 + 语义）— 语义查询远优于 grep |
| `gitnexus_context` | 符号 360° 视图：调用者、被调用者、引用、定义 |
| `gitnexus_impact` | 变更爆炸半径分析 — 修改一个符号会影响什么？ |

> **注意：** GitNexus **不随** Antigravity 一起安装。它是一个独立项目，需要通过 npm 单独安装。Antigravity 无需 GitNexus 即可完整运行——GitNexus 只是一个可选增强，用于更深层的代码理解。

**启用方式（3 步）：**

```bash
# 1. 安装 GitNexus（需要 Node.js）
npm install -g gitnexus

# 2. 索引你的项目（一次性操作，在本地创建知识图谱）
cd my-project
gitnexus analyze .

# 3. 像平常一样使用 ag ask — GitNexus 工具会被自动检测到
ag ask "认证流程是怎么工作的？"
```

**集成原理：** `ask_tools.py` 检查系统中是否有 `gitnexus` CLI。如果找到，就注册 `gitnexus_query`/`gitnexus_context`/`gitnexus_impact` 作为 AreaWorker agent 的额外工具。如果未找到，这些工具不会出现——零开销、无报错。
</details>

<details>
<summary><b>多 Agent Swarm</b> — Router-Worker 编排处理复杂任务</summary>

```python
from antigravity_engine.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("构建并审查一个计算器")
# 自动路由到 Coder → Reviewer → Researcher，综合结果
```

详见 [Swarm 文档](docs/zh/SWARM_PROTOCOL.md)。
</details>

<details>
<summary><b>沙盒执行</b> — 可配置的代码执行环境</summary>

| 变量 | 默认值 | 选项 |
|:-----|:------|:-----|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | 秒 |

详见 [沙盒文档](docs/zh/SANDBOX.md)。
</details>

---

## 实战演示：NVIDIA API + Kimi K2.5

使用 [Moonshot Kimi K2.5](https://build.nvidia.com/moonshotai/kimi-k2-5) 通过 NVIDIA 免费 API 进行端到端测试。任何 OpenAI 兼容端点都可以同样使用。

**1. 配置 `.env`**

```bash
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=nvapi-your-key-here
OPENAI_MODEL=moonshotai/kimi-k2.5
```

**2. 扫描你的项目**

```bash
$ ag refresh --workspace .
Updated .antigravity/conventions.md
Updated .antigravity/structure.md
```

Kimi K2.5 生成的输出：
```markdown
# Project Conventions
## Primary Language & Frameworks
- **Language**: Python (5,135 files, 99%+ of codebase)
- **Infrastructure**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
...
```

**3. 提问**

```bash
$ ag ask "这个项目支持哪些 LLM 后端？"
根据上下文，项目支持通过 NVIDIA API 使用 Kimi K2.5。
架构使用 OpenAI 兼容格式，支持任何端点，
包括通过 LiteLLM 使用的本地 LLM、NVIDIA NIM 模型等。
```

**4. 记录决策（无需 LLM）**

```bash
$ ag report "认证模块需要重构"
Logged report to .antigravity/memory/reports.md

$ ag log-decision "使用 PostgreSQL" "团队有丰富经验"
Logged decision to .antigravity/decisions/log.md
```

> 支持任何 OpenAI 兼容供应商：**NVIDIA**、**OpenAI**、**Ollama**、**vLLM**、**LM Studio**、**Groq** 等。

---

## 文档

| | |
|:--|:--|
| 🇬🇧 English | **[`docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`docs/es/`](docs/es/)** |

---

## 贡献

创意也是贡献！欢迎在 [issue](https://github.com/study8677/antigravity-workspace-template/issues) 中报告 bug、提出建议或提交架构方案。

## 贡献者

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>主要贡献者</b> · 创意建议 · 项目管理员 · 项目构想与反馈</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/devalexanderdaza">
        <img src="https://github.com/devalexanderdaza.png" width="80" /><br/>
        <b>Alexander Daza</b>
      </a><br/>
      <sub>沙盒 MVP · OpenSpec 工作流 · 技术分析文档 · PHILOSOPHY</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/chenyi">
        <img src="https://github.com/chenyi.png" width="80" /><br/>
        <b>Chen Yi</b>
      </a><br/>
      <sub>首个 CLI 原型 · 753 行重构 · DummyClient 提取 · 快速开始文档</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Subham-KRLX">
        <img src="https://github.com/Subham-KRLX.png" width="80" /><br/>
        <b>Subham Sangwan</b>
      </a><br/>
      <sub>动态工具与上下文加载 (#4) · 多 Agent Swarm 协议 (#3)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/shuofengzhang">
        <img src="https://github.com/shuofengzhang.png" width="80" /><br/>
        <b>shuofengzhang</b>
      </a><br/>
      <sub>记忆上下文窗口修复 · MCP 关闭优雅处理 (#28)</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/goodmorning10">
        <img src="https://github.com/goodmorning10.png" width="80" /><br/>
        <b>goodmorning10</b>
      </a><br/>
      <sub>增强 <code>ag ask</code> 上下文加载 — 新增 CONTEXT.md、AGENTS.md 和 memory/*.md 作为上下文来源 (#29)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/abhigyanpatwari">
        <img src="https://github.com/abhigyanpatwari.png" width="80" /><br/>
        <b>Abhigyan Patwari</b>
      </a><br/>
      <sub><a href="https://github.com/abhigyanpatwari/GitNexus">GitNexus</a> — 代码知识图谱原生集成到 <code>ag ask</code>，提供符号搜索、调用图和影响分析</sub>
    </td>
  </tr>
</table>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## 许可证

MIT License. 详见 [LICENSE](LICENSE)。

---

<div align="center">

**[📚 查看完整文档 →](docs/zh/)**

*为 AI 原生开发时代而构建*

</div>
