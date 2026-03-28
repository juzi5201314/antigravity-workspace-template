<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### La capa cognitiva que falta en los IDEs de IA.

Clúster multi-agente dinámico. Cada IDE de IA se convierte en experto en tu codebase.

Idioma: [English](README.md) | [中文](README_CN.md) | **Español**

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

## ¿Por qué Antigravity?

> El techo de capacidad de un AI Agent = **la calidad del contexto que puede leer.**

> **No le des a tu IDE de IA una enciclopedia. Dale un ChatGPT para tu codebase.**

La mayoría de los equipos llenan `CLAUDE.md` con miles de líneas de documentación que el agente lee y olvida. Antigravity toma el camino opuesto: en lugar de un volcado estático de conocimiento, despliega un **clúster multi-agente dinámico** — cada módulo de código tiene su propio Agent que lee código autónomamente y genera documentos de conocimiento, con un Router que enruta inteligentemente las preguntas al Agent correcto.

```
Enfoque tradicional:                    Enfoque Antigravity:
  CLAUDE.md = 5000 líneas de docs         Claude Code llama ask_project("¿cómo funciona auth?")
  El agente lee todo, olvida la mitad     Router → ModuleAgent lee código real, devuelve respuesta exacta
  La tasa de alucinación sigue alta       Fundamentado en código real, rutas de archivo y git
```

| Problema | Sin Antigravity | Con Antigravity |
|:---------|:---------------|:----------------|
| El agente olvida el estilo de código | Repites las mismas correcciones | Lee `.antigravity/conventions.md` — lo hace bien a la primera |
| Incorporar un codebase nuevo | El agente adivina la arquitectura | `ag-refresh` → ModuleAgents aprenden cada módulo |
| Cambiar entre IDEs | Reglas diferentes en cada uno | Una carpeta `.antigravity/` — todos los IDEs la comparten |
| Preguntar "¿cómo funciona X?" | El agente lee archivos al azar | `ask_project` MCP → Router enruta al ModuleAgent responsable |

La arquitectura son **archivos + un motor Q&A en vivo**, no plugins. Portable entre cualquier IDE, cualquier LLM, cero lock-in.

---

## Inicio Rápido

**Opción A — Solo archivos de contexto (cualquier IDE, sin LLM)**
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto && cd mi-proyecto
# Tu IDE lee automáticamente .antigravity/rules.md, .cursorrules, CLAUDE.md, AGENTS.md
```

**Opción B — Configuración completa con motor multi-agente (recomendado para Claude Code)**
```bash
# 1. Inyectar archivos de contexto
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto && cd mi-proyecto

# 2. Instalar el motor
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 3. Configurar .env con tu API key de LLM, luego refrescar base de conocimiento
ag-refresh

# 4. Registrar como servidor MCP — Claude Code puede usar ask_project como herramienta
claude mcp add antigravity ag-mcp -- --workspace $(pwd)
```

Ahora cuando Claude Code necesita entender tu codebase, llama `ask_project("...")` — Router enruta automáticamente al ModuleAgent correcto.

---

## Características de un Vistazo

```
  ag init             Inyectar archivos de contexto (--force para sobrescribir)
       │
       ▼
  .antigravity/       Base de conocimiento compartida — cada IDE lee de aquí
       │
       ├──► ag-refresh     Aprendizaje multi-agente dinámico → docs de conocimiento + mapa estructural
       ├──► ag-ask         Router → ModuleAgent Q&A con evidencia de código en vivo
       └──► ag-mcp         Servidor MCP → Claude Code llama directamente
```

**Clúster Multi-Agente Dinámico** — Durante `ag-refresh`, cada módulo de código recibe un RefreshModuleAgent que lee código autónomamente y genera un documento de conocimiento profundo. Durante `ag-ask`, Router lee el mapa estructural y enruta preguntas al ModuleAgent correcto. Los agentes pueden hacer handoff entre módulos. Basado en OpenAI Agent SDK + LiteLLM.

**GitAgent** — Un agente dedicado a analizar el historial git — entiende quién cambió qué y por qué.

**Mejora GitNexus (opcional)** — Instala GitNexus para desbloquear búsqueda semántica, grafos de llamadas y análisis de impacto para cada ModuleAgent.

---

## Comandos CLI

| Comando | Qué hace | ¿Necesita LLM? |
|:--------|:---------|:---------------:|
| `ag init <dir>` | Inyectar plantillas de arquitectura cognitiva | No |
| `ag init <dir> --force` | Re-inyectar, sobrescribiendo archivos existentes | No |
| `ag-refresh` | Aprendizaje multi-agente del codebase, genera docs de conocimiento + `conventions.md` + `structure.md` | Sí |
| `ag-ask "pregunta"` | Router → ModuleAgent/GitAgent Q&A enrutado | Sí |
| `ag-mcp --workspace <dir>` | **Iniciar servidor MCP** — expone `ask_project` + `refresh_project` a Claude Code | Sí |
| `ag report "mensaje"` | Registrar un hallazgo en `.antigravity/memory/` | No |
| `ag log-decision "qué" "por qué"` | Registrar una decisión arquitectónica | No |

Todos los comandos aceptan `--workspace <dir>` para apuntar a cualquier directorio.

---

## Dos Paquetes, Un Flujo de Trabajo

```
antigravity-workspace-template/
├── cli/                     # ag CLI — ligero, instalable con pip
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # Motor multi-agente + Knowledge Hub
    └── antigravity_engine/
        ├── _cli_entry.py    # ag-ask / ag-refresh puntos de entrada
        ├── config.py        # Configuración Pydantic
        ├── hub/             # ★ Núcleo: clúster multi-agente
        │   ├── agents.py    #   Router + ModuleAgent + GitAgent
        │   ├── pipeline.py  #   Orquestación refresh / ask
        │   ├── ask_tools.py #   Exploración de código + herramientas GitNexus
        │   ├── scanner.py   #   Escaneo de proyecto + detección de módulos
        │   └── mcp_server.py#   Servidor MCP (ag-mcp)
        ├── mcp_client.py    # Consumidor MCP (conecta herramientas externas)
        ├── memory.py        # Memoria de interacción persistente
        ├── tools/           # Herramientas MCP + extensiones
        ├── skills/          # Cargador de habilidades
        └── sandbox/         # Ejecución de código (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Cero deps de LLM. Inyecta plantillas, registra reportes y decisiones offline.

**Engine** (`pip install .../engine`) — Runtime multi-agente. Alimenta `ag-ask`, `ag-refresh`, `ag-mcp`. Soporta Gemini, OpenAI, Ollama, o cualquier API compatible con OpenAI.

**Nuevas actualizaciones de empaquetado de skills:**
- `engine/antigravity_engine/skills/graph-retrieval/` — herramientas de recuperación orientadas a grafo para razonamiento de estructura y rutas de llamadas.
- `engine/antigravity_engine/skills/knowledge-layer/` — herramientas de capa de conocimiento para consolidación de contexto semántico del proyecto.

```bash
# Instalar ambos para la experiencia completa
pip install "git+https://...#subdirectory=cli"
pip install "git+https://...#subdirectory=engine"
```

---

## Cómo Funciona

### 1. `ag init` — Inyectar archivos de contexto

```bash
ag init mi-proyecto
# ¿Ya inicializado? Usa --force para sobrescribir:
ag init mi-proyecto --force
```

Crea `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md`, `.windsurfrules` — cada IDE lee su archivo de configuración nativo, todos apuntando a la misma base de conocimiento `.antigravity/`.

### 2. `ag-refresh` — Aprendizaje multi-agente

```bash
ag-refresh --workspace mi-proyecto
```

**Pipeline de 5 pasos:**
1. Escanear codebase (lenguajes, frameworks, estructura)
2. Pipeline multi-agente genera `conventions.md`
3. Generar mapa `structure.md`
4. **Crear RefreshModuleAgents dinámicamente** — uno por módulo de código, cada uno lee código autónomamente y escribe un doc de conocimiento en `.antigravity/modules/*.md`
5. **RefreshGitAgent** analiza historial git, genera `_git_insights.md`

### 3. `ag-ask` — Q&A basado en Router

```bash
ag-ask "¿Cómo funciona la autenticación en este proyecto?"
```

Router lee el mapa `structure.md` y enruta preguntas al **ModuleAgent** correcto (pre-cargado con su doc de conocimiento) o **GitAgent** (entiende historial git). Para preguntas cross-módulo, los agentes pueden hacer handoff entre sí.

---

## Compatibilidad de IDEs

La arquitectura está codificada en **archivos** — cualquier agente que lea archivos del proyecto se beneficia:

| IDE | Archivo de configuración |
|:----|:------------------------|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| Windsurf | `.windsurfrules` |
| VS Code + Copilot | `.github/copilot-instructions.md` |
| Gemini CLI / Codex | `AGENTS.md` |
| Cline | `.clinerules` |
| Google Antigravity | `.antigravity/rules.md` |

Todos generados por `ag init`. Todos referencian `.antigravity/` para contexto compartido.

---

## Funciones Avanzadas

<details>
<summary><b>Servidor MCP — Dale a Claude Code un ChatGPT para tu codebase</b></summary>

Claude Code no necesita leer cientos de archivos de documentación — puede llamar `ask_project` como herramienta en vivo, respaldada por un clúster multi-agente dinámico: Router enruta preguntas al ModuleAgent correcto, devuelve respuestas precisas con rutas de archivo y números de línea.

**Configuración:**

```bash
# Instalar motor
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# Refrescar base de conocimiento primero (ModuleAgents aprenden cada módulo)
ag-refresh --workspace /ruta/al/proyecto

# Registrar como servidor MCP en Claude Code
claude mcp add antigravity ag-mcp -- --workspace /ruta/al/proyecto
```

**Herramientas expuestas a Claude Code:**

| Herramienta | Qué hace |
|:------------|:---------|
| `ask_project(pregunta)` | Router → ModuleAgent/GitAgent responde preguntas del codebase. Devuelve rutas + números de línea. |
| `refresh_project(quick?)` | Reconstruir base de conocimiento. ModuleAgents re-aprenden el código. |

</details>

<details>
<summary><b>Clúster Multi-Agente Dinámico</b> — Aprendizaje por módulo + enrutamiento inteligente</summary>

El núcleo del motor es **un clúster de Agents creado dinámicamente por módulo de código**:

```
 ag-refresh:                              ag-ask:

 ┌─ RefreshModule_engine ──→ engine.md    Router (lee mapa structure.md)
 ├─ RefreshModule_cli ────→ cli.md           ├──→ Module_engine (pre-cargado engine.md)
 └─ RefreshGitAgent ──────→ _git.md          ├──→ Module_cli (pre-cargado cli.md)
                                             ├──→ GitAgent (pre-cargado _git.md)
                                             └──→ Agents pueden hacer handoff entre sí
```

```bash
# ModuleAgents aprenden tu codebase
ag-refresh

# Solo escanear archivos cambiados desde el último refresh
ag-refresh --quick

# Router enruta inteligentemente al ModuleAgent correcto
ag-ask "¿Qué patrones de testing usa este proyecto?"

# Registrar hallazgos y decisiones (sin LLM)
ag report "El módulo de auth necesita refactoring"
ag log-decision "Usar PostgreSQL" "El equipo tiene experiencia profunda"
```

Funciona con Gemini, OpenAI, Ollama, o cualquier endpoint compatible con OpenAI. Basado en OpenAI Agent SDK + LiteLLM.
</details>

<details>
<summary><b>Integración MCP (Consumidor)</b> — Permitir a los agentes llamar herramientas externas</summary>

`MCPClientManager` permite a tus agentes conectarse a servidores MCP externos (GitHub, bases de datos, etc.), descubriendo y registrando herramientas automáticamente.

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

Configura `MCP_ENABLED=true` en `.env`.
</details>

<details>
<summary><b>Integración GitNexus</b> — Inteligencia profunda de código opcional</summary>

[GitNexus](https://github.com/abhigyanpatwari/GitNexus) es una **herramienta de terceros** que construye un grafo de conocimiento de código usando Tree-sitter AST. Antigravity proporciona hooks de integración incorporados — cuando instalas GitNexus por separado, `ag-ask` lo detecta automáticamente y desbloquea tres herramientas adicionales:

| Herramienta | Función |
|:------------|:--------|
| `gitnexus_query` | Búsqueda híbrida (BM25 + semántica) — superior a grep para consultas semánticas |
| `gitnexus_context` | Vista 360° de un símbolo: llamadores, llamados, referencias, definición |
| `gitnexus_impact` | Análisis de radio de explosión — ¿qué se rompe si cambias un símbolo? |

> **Nota:** GitNexus **NO** viene incluido con Antigravity. Antigravity funciona completamente sin él — GitNexus es una mejora opcional.

```bash
# 1. Instalar GitNexus (requiere Node.js)
npm install -g gitnexus

# 2. Indexar tu proyecto
cd my-project
gitnexus analyze .

# 3. Usar ag-ask como siempre — las herramientas GitNexus se detectan automáticamente
ag-ask "¿Cómo funciona el flujo de autenticación?"
```

**Cómo funciona:** `ask_tools.py` verifica si el CLI `gitnexus` está. Si lo encuentra, registra las herramientas para cada ModuleAgent. Si no, simplemente no aparecen — cero overhead.
</details>

<details>
<summary><b>Sandbox</b> — Entorno de ejecución de código configurable</summary>

| Variable | Default | Opciones |
|:---------|:--------|:---------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | segundos |

Ver [docs Sandbox](docs/es/SANDBOX.md).
</details>

---

## Demo Real: NVIDIA API + Kimi K2.5

Probado end-to-end con [Moonshot Kimi K2.5](https://build.nvidia.com/moonshotai/kimi-k2-5) via el tier gratuito de NVIDIA. Cualquier endpoint compatible con OpenAI funciona igual.

**1. Configurar `.env`**

```bash
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=nvapi-your-key-here
OPENAI_MODEL=moonshotai/kimi-k2.5
```

**2. Escanear tu proyecto**

```bash
$ ag-refresh --workspace .
Updated .antigravity/conventions.md
Updated .antigravity/structure.md
```

Salida generada por Kimi K2.5:
```markdown
# Project Conventions
## Primary Language & Frameworks
- **Language**: Python (5,135 files, 99%+ of codebase)
- **Infrastructure**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
...
```

**3. Hacer preguntas**

```bash
$ ag-ask "¿Qué backends LLM soporta este proyecto?"
Basado en el contexto, el proyecto soporta NVIDIA API con Kimi K2.5.
La arquitectura usa formato compatible con OpenAI, soportando cualquier
endpoint incluyendo LLMs locales via LiteLLM, modelos NVIDIA NIM, etc.
```

**4. Registrar decisiones (sin LLM)**

```bash
$ ag report "El módulo de auth necesita refactoring"
Logged report to .antigravity/memory/reports.md

$ ag log-decision "Usar PostgreSQL" "El equipo tiene experiencia profunda"
Logged decision to .antigravity/decisions/log.md
```

> Funciona con cualquier proveedor compatible con OpenAI: **NVIDIA**, **OpenAI**, **Ollama**, **vLLM**, **LM Studio**, **Groq**, etc.

---

## Documentación

| | |
|:--|:--|
| 🇬🇧 English | **[`docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`docs/es/`](docs/es/)** |

---

## Contribuyendo

¡Las ideas también son contribuciones! Abre un [issue](https://github.com/study8677/antigravity-workspace-template/issues) para reportar bugs, sugerir funcionalidades o proponer arquitectura.

## Contribuidores

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>Contribuidor Principal</b> · Sugerencias creativas · Administrador del proyecto · Ideación y feedback</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/devalexanderdaza">
        <img src="https://github.com/devalexanderdaza.png" width="80" /><br/>
        <b>Alexander Daza</b>
      </a><br/>
      <sub>Sandbox MVP · Workflows OpenSpec · Docs de análisis técnico · PHILOSOPHY</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/chenyi">
        <img src="https://github.com/chenyi.png" width="80" /><br/>
        <b>Chen Yi</b>
      </a><br/>
      <sub>Primer prototipo CLI · Refactor de 753 líneas · Extracción DummyClient · Docs quick-start</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Subham-KRLX">
        <img src="https://github.com/Subham-KRLX.png" width="80" /><br/>
        <b>Subham Sangwan</b>
      </a><br/>
      <sub>Carga dinámica de herramientas (#4) · Protocolo swarm multi-agente (#3)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/shuofengzhang">
        <img src="https://github.com/shuofengzhang.png" width="80" /><br/>
        <b>shuofengzhang</b>
      </a><br/>
      <sub>Fix ventana de contexto de memoria · Manejo graceful de cierre MCP (#28)</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/goodmorning10">
        <img src="https://github.com/goodmorning10.png" width="80" /><br/>
        <b>goodmorning10</b>
      </a><br/>
      <sub>Mejora de carga de contexto en <code>ag ask</code> — añadió CONTEXT.md, AGENTS.md y memory/*.md como fuentes de contexto (#29)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/abhigyanpatwari">
        <img src="https://github.com/abhigyanpatwari.png" width="80" /><br/>
        <b>Abhigyan Patwari</b>
      </a><br/>
      <sub><a href="https://github.com/abhigyanpatwari/GitNexus">GitNexus</a> — grafo de conocimiento de código integrado nativamente en <code>ag ask</code> para búsqueda de símbolos, grafos de llamadas y análisis de impacto</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/BBear0115">
        <img src="https://github.com/BBear0115.png" width="80" /><br/>
        <b>BBear0115</b>
      </a><br/>
      <sub>Empaquetado de skills y mejoras de recuperación KG · Sincronización README multilingüe (#30)</sub>
    </td>
  </tr>
</table>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## Licencia

Licencia MIT. Ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**[📚 Documentación completa →](docs/es/)**

*Construido para la era del desarrollo AI-nativo*

</div>
