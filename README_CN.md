<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### 面向任意代码库的多智能体知识引擎。

`ag-refresh` 构建知识库。`ag-ask` 回答问题。任意 LLM，任意 IDE。

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

引擎是核心：`ag-refresh` 部署多智能体集群自主阅读代码——每个模块分配专属 Agent 生成知识文档。`ag-ask` 将问题路由到对应 Agent，答案有据可查，带文件路径和行号。

**已在 [OpenClaw](https://github.com/openclaw/openclaw)（12K 文件，34.8 万 Star）上用 MiniMax2.7 测试——模块问答 10/10，111 个模块 43 分钟自学完成。** [查看完整评估](#大规模评估minimax27--openclaw12k-文件348-万-star)

```
传统做法：                           Antigravity 做法：
  CLAUDE.md = 5000 行文档              Claude Code 调用 ask_project("auth 怎么工作的？")
  Agent 全部读入，大半遗忘              Router → ModuleAgent 读真实源码，返回精准答案
  幻觉率居高不下                       有据可查，带文件路径和行号
```

| 痛点 | 没有 Antigravity | 有 Antigravity |
|:----|:----------------|:--------------|
| Agent 忘记代码风格 | 反复纠正同样的问题 | 读取 `.antigravity/conventions.md` —— 一次到位 |
| 接手新代码库 | Agent 只能猜测架构 | `ag-refresh` → ModuleAgent 自主学习每个模块 |
| 切换 IDE | 每个 IDE 规则不同 | 一个 `.antigravity/` 目录 —— 所有 IDE 共享 |
| 问"X 怎么实现的？" | Agent 胡乱翻文件 | `ask_project` MCP → Router 精准路由到负责模块的 Agent |

架构是**文件 + 实时问答引擎**，而非插件。跨 IDE、跨 LLM、零平台锁定。

---

## 快速开始

**方案 A —— 引擎：多智能体代码问答（推荐）**
```bash
# 1. 安装引擎 + CLI
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli"
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 2. 配置 .env（任意 OpenAI 兼容 API）
cd my-project
cat > .env <<EOF
OPENAI_BASE_URL=https://your-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
AG_ASK_TIMEOUT_SECONDS=120
EOF

# 3. 构建知识库（ModuleAgent 自主学习每个模块）
ag-refresh --workspace .

# 4. 提问
ag-ask "这个项目的认证逻辑是怎么实现的？"

# 5.（可选）注册为 Claude Code 的 MCP 服务器
claude mcp add antigravity ag-mcp -- --workspace $(pwd)
```

**方案 B —— 仅注入上下文文件（任意 IDE，无需 LLM）**
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init my-project && cd my-project
# IDE 自动读取 .antigravity/rules.md、.cursorrules、CLAUDE.md、AGENTS.md
```

---

## 功能一览

```
  ag init             将上下文文件注入任意项目（--force 可覆盖已有文件）
       │
       ▼
  .antigravity/       共享知识库 —— 所有 IDE 从这里读取
       │
       ├──► ag-refresh     动态多智能体自主学习 → 生成模块知识文档 + 结构图
       ├──► ag-ask         Router → ModuleAgent 路由问答，实时代码证据
       └──► ag-mcp         MCP 服务端 → Claude Code 直接调用
```

**动态多智能体集群** —— `ag-refresh` 时，引擎使用**智能功能分组**：基于知识图谱 import 关系、目录共位、文件名前缀将文件聚类。源码直接预加载进 agent 上下文（无需工具调用），构建产物自动过滤。每个 sub-agent 分析约 30K tokens 的聚焦代码，只需 1 次 LLM 调用。**RegistryAgent** 随后汇总所有模块为语义 registry。`ag-ask` 时，Router 根据 registry 理解*每个模块负责什么*，精准路由到对应 ModuleAgent。基于 OpenAI Agent SDK + LiteLLM。

**GitAgent** —— 专门分析 git 历史的 Agent，了解「谁改了什么、为什么改」。

**GitNexus 增强（可选）** —— 安装 GitNexus 后自动检测，为 ModuleAgent 解锁语义搜索、调用图、变更影响分析。

---

## CLI 命令

| 命令 | 功能 | 需要 LLM？ |
|:-----|:-----|:----------:|
| `ag init <dir>` | 注入认知架构模板 | 否 |
| `ag init <dir> --force` | 重新注入，覆盖已有文件 | 否 |
| `ag-refresh` | 多智能体自主学习代码库，生成模块知识文档 + `conventions.md` + `structure.md` | 是 |
| `ag-ask "问题"` | Router → ModuleAgent/GitAgent 路由问答 | 是 |
| `ag-mcp --workspace <dir>` | **启动 MCP 服务器** —— 向 Claude Code 暴露 `ask_project` + `refresh_project` 工具 | 是 |
| `ag report "内容"` | 记录发现到 `.antigravity/memory/` | 否 |
| `ag log-decision "决策" "原因"` | 记录架构决策 | 否 |

所有命令支持 `--workspace <dir>` 参数指向任意目录。

---

## 两个包，一套工作流

```
antigravity-workspace-template/
├── cli/                     # ag CLI — 轻量，pip 可安装
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # 多智能体引擎 + 知识中枢
    └── antigravity_engine/
        ├── _cli_entry.py    # ag-ask / ag-refresh 入口
        ├── config.py        # Pydantic 配置
        ├── hub/             # ★ 核心：多智能体集群
        │   ├── agents.py    #   Router + ModuleAgent + GitAgent
        │   ├── pipeline.py  #   refresh / ask 编排
        │   ├── ask_tools.py #   代码探索 + GitNexus 工具
        │   ├── scanner.py   #   项目扫描 + 模块检测
        │   └── mcp_server.py#   MCP 服务端 (ag-mcp)
        ├── mcp_client.py    # MCP 消费端（连接外部工具）
        ├── memory.py        # 持久交互记忆
        ├── tools/           # MCP 查询工具 + 扩展工具
        ├── skills/          # 技能加载器
        └── sandbox/         # 代码执行（local / microsandbox）
```

**CLI**（`pip install .../cli`）—— 零 LLM 依赖。注入模板，离线记录报告和决策。

**Engine**（`pip install .../engine`）—— 多智能体运行时。驱动 `ag-ask`、`ag-refresh`、`ag-mcp`。支持 Gemini、OpenAI、Ollama 或任何 OpenAI 兼容 API。

**新增 skill 封装更新：**
- `engine/antigravity_engine/skills/graph-retrieval/` —— 面向结构与调用路径推理的图谱检索工具。
- `engine/antigravity_engine/skills/knowledge-layer/` —— 面向项目语义上下文整合的知识层工具。

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

### 2. `ag-refresh` — 多智能体自主学习

```bash
ag-refresh --workspace my-project
```

**8 步流程：**
1. 扫描代码库（语言、框架、结构）
2. 多 Agent 管道生成 `conventions.md`
3. 生成 `structure.md` 结构图
4. 构建知识图谱（`knowledge_graph.json` + mermaid）
5. 写入文档/数据/媒体索引
6. **智能功能分组** —— 基于 import 图 + 目录 + 前缀分组，代码预加载进 context（每组约 30K tokens），自动过滤构建产物（dist、bundle、vendor、编译文件）。每个 sub-agent 用 1 次 LLM 调用完成深度分析。多组模块用 merge agent 合并输出。
7. **RefreshGitAgent** 分析 git 历史，生成 `_git_insights.md`
8. **RegistryAgent** 读取所有知识产物 → 调用 LLM → 生成 `module_registry.md`（每个模块 2-3 句语义描述，供 Router 做智能路由）

### 3. `ag-ask` — Router 路由问答

```bash
ag-ask "这个项目的认证逻辑是怎么实现的？"
```

Router 读取 `structure.md` 地图，将问题路由到对应的 **ModuleAgent**（预加载了该模块的知识文档）或 **GitAgent**（了解 git 历史）。跨模块问题时 Agent 间可互相 handoff 通讯。

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
<summary><b>MCP 服务器 — 给 Claude Code 一个代码库专属 ChatGPT</b></summary>

Claude Code 不再需要读数百个文档文件——它可以直接调用 `ask_project` 工具，背后是动态多智能体集群：Router 将问题路由到对应 ModuleAgent，返回带文件路径和行号的精准答案。

**配置步骤：**

```bash
# 安装引擎
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 先刷新知识库（ModuleAgent 自主学习每个模块）
ag-refresh --workspace /path/to/project

# 注册为 Claude Code 的 MCP 服务器
claude mcp add antigravity ag-mcp -- --workspace /path/to/project
```

**向 Claude Code 暴露的工具：**

| 工具 | 功能 |
|:-----|:-----|
| `ask_project(question)` | Router → ModuleAgent/GitAgent 回答代码库问题。返回文件路径 + 行号。 |
| `refresh_project(quick?)` | 重大改动后重建知识库。ModuleAgent 重新学习代码。 |

</details>

<details>
<summary><b>动态多智能体集群</b> — 模块级自学习 + 智能路由</summary>

引擎的核心是**按代码模块动态创建的 Agent 集群**：

```
 ag-refresh（v2 — 智能分组）：              ag-ask 时：

 对每个模块：                               Router（读 module_registry.md）
 ┌ 按 import 图分组文件                       ├──→ Module_engine（已加载 engine.md）
 ├ 每组预加载约 30K tokens                    ├──→ Module_cli（已加载 cli.md）
 ├ 自动过滤构建产物                           ├──→ GitAgent（已加载 _git.md）
 ├ Sub-agent 各用 1 次 LLM 调用分析           └──→ Agent 间可互相 handoff
 ├ Merge agent 合并输出
 └─ RegistryAgent ────→ registry.md
```

**核心创新：**
- **智能分组**：基于知识图谱 import 关系分组，非机械 token 切割。构建产物（dist/、bundle、vendor、编译文件）自动过滤。
- **预加载上下文**：源码直接注入 agent instructions——零工具调用。之前需要 16 次 LLM 轮次的模块现在只需 1 次。
- **模块 Registry**：RegistryAgent 汇总每个模块的职责描述。Router 知道*每个模块做什么*，实现精准路由（"数据库 schema" → `src_storage`）。

```bash
# 模块 Agent 自主学习代码库
ag-refresh

# 仅扫描上次刷新后变更的文件
ag-refresh --quick

# Router 智能路由到对应模块 Agent
ag-ask "这个项目用了什么测试模式？"

# 记录发现和决策（无需 LLM）
ag report "认证模块需要重构"
ag log-decision "使用 PostgreSQL" "团队有丰富经验"
```

支持 Gemini、OpenAI、Ollama 或任何 OpenAI 兼容端点。基于 OpenAI Agent SDK + LiteLLM。
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

[GitNexus](https://github.com/abhigyanpatwari/GitNexus) 是一个**第三方工具**，通过 Tree-sitter AST 解析构建代码知识图谱。Antigravity 提供了内置的集成接口——当你单独安装 GitNexus 后，`ag-ask` 会自动检测并解锁三个额外工具：

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

# 3. 像平常一样使用 ag-ask — GitNexus 工具会被自动检测到
ag-ask "认证流程是怎么工作的？"
```

**集成原理：** `ask_tools.py` 检查系统中是否有 `gitnexus` CLI。如果找到，就注册 `gitnexus_query`/`gitnexus_context`/`gitnexus_impact` 作为每个 ModuleAgent 的额外工具。如果未找到，这些工具不会出现——零开销、无报错。
</details>

<details>
<summary><b>MCP 集成（消费端）</b> — 让 Agent 调用外部工具</summary>

`MCPClientManager` 让你的 Agent 能连接外部 MCP 服务器（GitHub、数据库等），自动发现并注册工具。

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

在 `.env` 中设置 `MCP_ENABLED=true`。
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

## 大规模评估：MiniMax2.7 + OpenClaw（12K 文件，34.8 万 Star）

在 [OpenClaw](https://github.com/openclaw/openclaw) 上测试 —— 最热门的开源 AI 助手（TypeScript + Swift + Kotlin，12,133 文件）—— 使用 **MiniMax2.7** 免费 API。

### Refresh 结果

```
$ ag-refresh --workspace /path/to/openclaw
[7/8] ▶ 运行 154 个模块（并发=8）...
      自动拆分：extensions/ → 50+ 子模块（slack, telegram, whatsapp, ...）
      自动拆分：src/ → 40+ 子模块（agents, gateway, config, ...）

总耗时：42分52秒 | 111 个模块文档 | 1.5MB 知识库
```

### Ask 评估矩阵（11 项测试）

| 类别 | 问题 | 结果 | 质量 |
|:-----|:-----|:----:|:----:|
| 基础理解 | "What is this project?" | **通过** | 5/5 — sponsors、平台、功能、结构 |
| 模块深度 | "Telegram 集成怎么工作？" | **通过** | **5/5** — 文件表 + 架构图 + 类型 + 常量 |
| 模块深度 | "Discord 语音频道？" | **通过** | **5/5** — 音频管道 + 代码示例 + 设计模式 |
| 模块深度 | "WhatsApp 集成？" | **通过** | **5/5** — 认证流 + 插件架构 + 依赖 |
| 跨模块 | "Gateway 怎么工作？" | 超时 | 2/5 — 有文件列表，无深度分析 |
| 跨模块 | "测试框架？" | 超时 | 2/5 — 列出 vitest 配置 |

### 核心发现：自动拆分释放模块级卓越表现

| 维度 | 得分 | 说明 |
|:-----|:----:|:-----|
| 基础问答 | **9/10** | 项目概述精准 |
| 模块深度分析 | **10/10** | Telegram/Discord/WhatsApp — 架构图、类型、设计模式 |
| 跨模块问题 | **3/10** | Gateway、Testing — 免费 API 超时 |
| **总体** | **6.5/10** | **模块级问答：12K 文件项目也能 production-ready** |

### 性能对比

| 指标 | OpenCMO（374 文件） | OpenClaw（12K 文件） | 改进 |
|:-----|:------------------:|:-------------------:|:----:|
| Refresh 时间 | ~10 分钟 | **43 分钟** | 并行 + 自动拆分 |
| 模块文档 | 9 | **111** | 12x |
| 知识库 | 540KB | **1.5MB** | 2.8x |
| 模块问答质量 | 7/10 | **10/10** | 自动拆分 = 聚焦知识 |

> **关键优化：** 大模块（extensions/ 262 组、src/ 363 组）自动拆分为独立子模块，所有模块 8 并发执行。OpenClaw 的 refresh 从 **5 小时+未完成** 降至 **43 分钟完成**。

### 最佳配置

```bash
# .env — 评估后的推荐配置
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model

AG_ASK_TIMEOUT_SECONDS=120
AG_REFRESH_AGENT_TIMEOUT_SECONDS=180
AG_MODULE_AGENT_TIMEOUT_SECONDS=90
```

> 支持任何 OpenAI 兼容供应商：**NVIDIA**、**OpenAI**、**Ollama**、**vLLM**、**LM Studio**、**Groq**、**MiniMax** 等。

---

<details>
<summary><b>早期评估：MiniMax2.7 + OpenCMO（374 文件，29K 行）</b></summary>

在 [OpenCMO](https://github.com/study8677/OpenCMO) 代码库（Python + React/TS，374 文件）上使用 **MiniMax2.7** 测试。

### Ask 评估矩阵（18 项测试）

| 类别 | 问题 | 结果 | 质量 |
|:-----|:-----|:----:|:----:|
| 基础理解 | "这个项目是什么？" | **通过** | 5/5 — 准确概括 |
| 精确函数 | "llm.py 里 get_model() 的签名" | **通过** | 5/5 — **100% 准确** |
| 幻觉测试 | "支持 GraphQL 吗？" | **通过** | 5/5 — 正确否定，4 维证据链 |
| 数据库 Schema | "列出所有数据库表" | **通过** | 5/5 — 34 张表全列出 |
| 审批流程 | "审批流程怎么工作？" | **通过** | 5/5 — 完整状态机，含行号 |
| 复杂架构 | "多 Agent 系统怎么工作？" | **通过** | 5/5 — 20 个 Agent 详列 |

### 评分

| 维度 | 评分 | 说明 |
|:-----|:----:|:-----|
| 基础问答 | **9/10** | 项目、技术栈、模块——优秀 |
| 幻觉控制 | **9/10** | 不会编造；能给否定证据 |
| **综合** | **7/10** | **日常代码问答：生产就绪** |

> 完整评估报告：[`artifacts/plan_20260404_opencmo_ask_boundary_eval.md`](artifacts/plan_20260404_opencmo_ask_boundary_eval.md)

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
    <td align="center" width="20%">
      <a href="https://github.com/BBear0115">
        <img src="https://github.com/BBear0115.png" width="80" /><br/>
        <b>BBear0115</b>
      </a><br/>
      <sub>技能封装与知识图谱检索增强 · 多语言 README 同步更新 (#30)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/SunkenCost">
        <img src="https://github.com/SunkenCost.png" width="80" /><br/>
        <b>SunkenCost</b>
      </a><br/>
      <sub><code>ag clean</code> 清理命令 · <code>__main__</code> 入口保护 (#37)</sub>
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
