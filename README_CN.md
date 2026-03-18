<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity" width="200"/>

# Antigravity

**一条命令，让每个 AI IDE 更聪明。**

`ag init` 将认知架构注入任意项目目录。<br/>
`ag ask` / `ag refresh` 通过多 Agent 分析维护活的项目上下文。

语言: [English](README.md) | **中文** | [Español](README_ES.md)

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
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

> **核心论点**：AI Agent 的能力上限 = 它能读到的上下文质量。
>
> 架构即**文件**，而非插件。`.cursorrules`、`CLAUDE.md`、`.antigravity/rules.md` —— 这些就是认知架构本身。跨 IDE、跨 LLM、零平台锁定。

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

## CLI 命令

| 命令 | 功能 | 需要 LLM？ |
|:-----|:-----|:----------:|
| `ag init <dir>` | 注入认知架构模板 | 否 |
| `ag refresh` | 扫描项目，生成 `.antigravity/conventions.md` | 是 |
| `ag ask "问题"` | 回答关于项目的问题 | 是 |
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
```

创建 `.antigravity/rules.md`、`.cursorrules`、`CLAUDE.md`、`AGENTS.md`、`.windsurfrules` —— 每个 IDE 读取各自的原生配置文件，全部指向同一个 `.antigravity/` 知识库。

### 2. `ag refresh` — 构建项目智能

```bash
ag refresh --workspace my-project
```

扫描代码库（语言、框架、结构），将扫描结果送入多 Agent 管道，生成 `.antigravity/conventions.md`。下次 IDE 打开时读取到更丰富的上下文。

### 3. `ag ask` — 查询项目

```bash
ag ask "这个项目的认证逻辑是怎么实现的？"
```

读取 `.antigravity/` 上下文，送入 Reviewer Agent，返回有依据的回答。

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
