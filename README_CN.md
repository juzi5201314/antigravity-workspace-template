<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# Antigravity Workspace Template

**用于构建自主 AI 代理的生产级入门套件。**

*适用于任何 AI IDE · 任何 CLI · 任何 LLM*

语言: [English](README.md) | **中文** | [Español](README_ES.md)

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

### 别让 Cursor / Windsurf 在空目录里瞎编了。
### 给 AI IDE 注入 **Artifact-First** 认知架构。

<br/>

<img src="docs/assets/before_after.png" alt="Before vs After Antigravity" width="800"/>

<br/>

```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init my-project
```

</div>

<br/>

> **`ag init` → 打开 IDE → 开始提示。即是工作流。**
>
> **第一性原理**：AI Agent 的能力上限 = 它能读到的上下文质量。与其依赖 IDE 插件或平台锁定，不如回归本质——**架构即文件**。一组精心设计的 `.cursorrules`、`CONTEXT.md`、`.antigravity/rules.md` 就是全部认知架构。`ag init` 将这套架构注入任何空目录，让你的 IDE 瞬间从编辑器变成**懂行的架构师**——不依赖任何插件，不绑定任何平台。

---

## 🌍 全平台兼容

本模板**不绑定**任何特定 IDE，开箱即用于所有主流 AI 开发环境：

| 平台 | 工作方式 |
|:-----|:---------|
| **Google Antigravity** | 读取 `.antigravity/rules.md` 实现完整上下文感知 |
| **Cursor** | 读取 `.cursorrules` 获取项目级规则 |
| **Windsurf / VS Code + Copilot** | 利用 `.context/` 文件注入知识 |
| **Claude Code** | 读取 `AGENTS.md` + `CONTEXT.md` 获取项目规范 |
| **Gemini CLI** | 读取 `AGENTS.md` + `.context/` 注入知识 |
| **Codex (OpenAI)** | 读取 `AGENTS.md` + 目录约定 |
| **Cline / Aider** | 借助 `CONTEXT.md` 和目录约定 |
| **任何 OpenAI 兼容 Agent** | `engine/src/tools/` 自动发现工具，标准 Python 入口 |

秘诀：架构编码在**文件**中，而不是 IDE 插件里。任何能读取项目文件的 Agent 都能受益。

---

## ⚡ 快速开始

### 方式一：将认知架构注入任意项目（推荐）

```bash
# 1. 安装 CLI
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# 2. 将认知架构注入你的项目
ag init my-project

# 3. 用任何 AI IDE 打开，开始提示！
```

### 方式二：运行完整 Agent 引擎

```bash
# 1. 克隆仓库
git clone https://github.com/study8677/antigravity-workspace-template.git
cd antigravity-workspace-template

# 2. 安装引擎依赖
cd engine
pip install -r requirements.txt

# 3. 配置 API 密钥
cp .env.example .env && nano .env

# 4. 指向任何工作区运行 Agent
python agent.py --workspace /path/to/your/project "你的任务"
```

**就这么简单！** IDE 会自动加载配置，你可以直接开始提示。

---

## 🎯 这是什么？

这并**不**是另一个 LangChain 封装。它是一个极简、透明的工作区，用于构建 AI Agent：

| 特性 | 描述 |
|:-----|:-----|
| 🧠 **无限记忆** | 递归摘要自动压缩上下文 |
| 🧠 **真实思考** | 行动前使用思维链 (CoT) 进行"深度思考" |
| 🎓 **技能系统** | `engine/src/skills/` 下的模块化能力，自动加载 |
| 🛠️ **通用工具** | Python 函数放入 `engine/src/tools/` 即可自动发现 |
| 📚 **自动上下文** | 向 `.context/` 添加文件即自动注入提示 |
| 🔌 **MCP 支持** | 连接 GitHub、数据库、文件系统、自定义服务器 |
| 🤖 **Swarm Agent** | Router-Worker 模式的多 Agent 编排 |
| ⚡ **Gemini 原生** | 为 Gemini 2.0 Flash 做了优化 |
| 🌐 **LLM 无关** | 支持 OpenAI、Azure、Ollama 或任何兼容 API |
| 📂 **Artifact-First** | 约定优先的计划、日志、证据工作流 |
| 🔒 **沙盒执行** | 可选 local / microsandbox 执行环境 |

---

## 🏗️ 项目结构

```
antigravity-workspace-template/
│
├── cli/                          # 🖥️ 轻量级 CLI (ag init)
│   ├── pyproject.toml            #    包配置 & 入口点
│   └── src/ag_cli/
│       ├── cli.py                #    CLI 命令 (init, start-engine, version)
│       └── templates/            #    认知架构模板
│           ├── .cursorrules      #    → 注入到目标项目
│           ├── .antigravity/     #    → 注入到目标项目
│           └── CONTEXT.md        #    → 注入到目标项目
│
├── engine/                       # ⚙️ Python Agent 引擎
│   ├── agent.py                  #    入口（支持 --workspace）
│   ├── src/
│   │   ├── agent.py              #    Agent 主循环 (Think-Act-Reflect)
│   │   ├── config.py             #    配置（工作区感知）
│   │   ├── memory.py             #    Markdown 记忆管理
│   │   ├── mcp_client.py         #    MCP 集成
│   │   ├── swarm.py              #    多 Agent 编排
│   │   ├── tools/                #    自定义工具（自动发现）
│   │   ├── agents/               #    专家型 Agent
│   │   ├── sandbox/              #    代码执行沙盒
│   │   └── skills/               #    模块化技能（自动加载）
│   ├── tests/                    #    测试套件
│   └── requirements.txt          #    引擎依赖
│
├── docs/                         # 📚 文档
├── README.md                     # 本文件
└── LICENSE                       # MIT
```

---

## 💡 30 秒创建一个工具

```python
# engine/src/tools/my_tool.py
def analyze_sentiment(text: str) -> str:
    """Analyzes the sentiment of given text."""
    return "positive" if len(text) > 10 else "neutral"
```

**重启 Agent。** 完成！工具已可用于任何 AI IDE。

---

## 🔌 MCP 集成

连接外部工具：

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

## 🤖 多 Agent Swarm

分解复杂任务：

```python
from engine.src.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("构建并审查一个计算器")
```

Swarm 自动路由到 Coder、Reviewer、Researcher Agent，综合结果并提供可检查的消息日志。

---

## 🔒 沙盒配置

| 变量 | 默认值 | 选项 |
|:-----|:------|:-----|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | 秒 |
| `SANDBOX_MAX_OUTPUT_KB` | `10` | KB |

<details>
<summary><b>Microsandbox 额外变量</b></summary>

| 变量 | 默认值 |
|:-----|:------|
| `MSB_SERVER_URL` | `http://127.0.0.1:5555` |
| `MSB_API_KEY` | （可选） |
| `MSB_IMAGE` | `microsandbox/python` |
| `MSB_CPU_LIMIT` | `1.0` |
| `MSB_MEMORY_MB` | `512` |
</details>

---

## 📚 文档

| 语言 | 链接 |
|:-----|:-----|
| 🇬🇧 English | **[`/docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`/docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`/docs/es/`](docs/es/)** |

---

## ✅ 项目进度

- ✅ 阶段 1-8：基础、记忆、工具、Swarm、MCP
- ✅ 阶段 9：V1.0 Monorepo 重构 — CLI + Engine 解耦架构
- 🚀 阶段 10：企业核心（即将到来）

详见 [Roadmap](docs/zh/ROADMAP.md)。

---

## 🤝 贡献

创意也是贡献！欢迎在 [issue](https://github.com/study8677/antigravity-workspace-template/issues) 中报告 bug、提出建议或提交架构方案。

## 👥 贡献者

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

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## 📄 许可证

MIT License. 详见 [LICENSE](LICENSE)。

---

<div align="center">

**[📚 查看完整文档 →](docs/zh/)**

*为 AI 原生开发时代而构建 ❤️*

</div>
