<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### Motor de conocimiento multi-agente para cualquier codebase.

`ag-refresh` construye la base de conocimiento. `ag-ask` responde preguntas. Cualquier LLM, cualquier IDE.

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

El motor es el núcleo: `ag-refresh` despliega un clúster multi-agente que lee tu código autónomamente — cada módulo obtiene su propio Agent que genera documentación de conocimiento. `ag-ask` enruta preguntas al Agent correcto, con respuestas basadas en código real con rutas de archivo y números de línea.

**Evaluado en un proyecto real de 374 archivos con MiniMax2.7 — Q&A básico 9/10, resistencia a alucinaciones 9/10.** [Ver evaluación completa.](#evaluación-real-minimax27-en-opencmo-374-archivos-29k-líneas)

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

**Opción A — Motor: Q&A multi-agente sobre tu codebase (recomendado)**
```bash
# 1. Instalar motor + CLI
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli"
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 2. Configurar .env (cualquier API compatible con OpenAI)
cd mi-proyecto
cat > .env <<EOF
OPENAI_BASE_URL=https://tu-endpoint/v1
OPENAI_API_KEY=tu-key
OPENAI_MODEL=tu-modelo
AG_ASK_TIMEOUT_SECONDS=120
EOF

# 3. Construir base de conocimiento (ModuleAgents aprenden cada módulo)
ag-refresh --workspace .

# 4. Preguntar
ag-ask "¿Cómo funciona la autenticación en este proyecto?"

# 5. (Opcional) Registrar como servidor MCP para Claude Code
claude mcp add antigravity ag-mcp -- --workspace $(pwd)
```

**Opción B — Solo archivos de contexto (cualquier IDE, sin LLM)**
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto && cd mi-proyecto
# Tu IDE lee automáticamente .antigravity/rules.md, .cursorrules, CLAUDE.md, AGENTS.md
```

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

## Evaluación Real: MiniMax2.7 en OpenCMO (374 archivos, 29K líneas)

Evaluado end-to-end contra el codebase [OpenCMO](https://github.com/study8677/OpenCMO) (Python + React/TS, 374 archivos) usando **MiniMax2.7** via un router compatible con OpenAI.

### Resultados de Refresh

```
$ ag-refresh --workspace /path/to/OpenCMO
[1/3] Scanning project... 374 files, 0.02s
[2/3] Analyzing with multi-agent swarm...
      conventions.md  ✅ 289 líneas
      structure.md    ✅ 1384 líneas
      knowledge_graph ✅ 540KB JSON + mermaid
```

### Matriz de evaluación Ask (18 tests)

| Categoría | Pregunta | Resultado | Calidad |
|:----------|:---------|:---------:|:-------:|
| Comprensión básica | "¿Qué es este proyecto?" | **OK** | 5/5 — resumen preciso con detalles técnicos |
| Stack técnico | "¿Qué stack y frameworks usa?" | **OK** | 5/5 — frontend + backend + libs listados |
| Lista de módulos | "Lista todos los módulos principales" | **OK** | 5/5 — formato tabla, preciso |
| Rutas API | "¿Cómo funciona el routing de API?" | **OK** | 5/5 — rutas + endpoints + código cliente |
| Función precisa | "firma de get_model() en llm.py" | **OK** | 5/5 — **100% preciso**: archivo, línea, lógica |
| Test de alucinación | "¿Soporta GraphQL?" | **OK** | 5/5 — correctamente dijo **No** con 4 evidencias |
| Consulta en chino | "社区监控支持哪些平台?" | **OK** | 5/5 — respuesta en chino, tabla de plataformas |
| Flujo de aprobación | "¿Cómo funciona la aprobación?" | **OK** | 5/5 — máquina de estados completa con números de línea |
| Arquitectura compleja | "¿Cómo funciona el sistema multi-agente?" (120s) | **OK** | 5/5 — 20 agentes listados, patrones de comunicación |
| Tracing end-to-end | "Traza el flujo de crear proyecto" | **Timeout** | 1/5 — necesita >45s |
| Análisis de seguridad | "¿Problemas de seguridad?" | **Timeout** | 1/5 — necesita >45s |
| Comparación externa | "Compara con Langchain" | **Timeout** | 1/5 — requiere conocimiento externo |

### Resumen de capacidades

```
 ✅ Fuerte (fiable)                     ⚠️ Condicional                   ❌ Débil
 ─────────────────                      ─────────────                    ──────
 Comprensión a nivel proyecto           Preguntas de arquitectura        Precisión de localización
 Búsqueda precisa de funciones          compleja (fijar TIMEOUT=120)     Inferencia profunda ORM/schema
 Resistencia a alucinaciones                                             Comparación con conocimiento externo
 Multi-idioma (zh/en)
 Manejo de edge-cases
```

### Puntuaciones

| Dimensión | Puntuación | Notas |
|:----------|:----------:|:------|
| Q&A básico | **9/10** | Proyecto, stack, módulos — excelente |
| Localización de código | **7/10** | Consultas precisas excelentes; archivos homónimos pueden confundir |
| Análisis profundo | **4/10** | Limitado por timeout; **7/10 a 120s** |
| Control de alucinaciones | **9/10** | No fabrica; da evidencia negativa |
| Multi-idioma | **9/10** | Q&A en chino excelente |
| Robustez | **9/10** | Inputs vacíos, basura, peticiones de acción — todo manejado |
| **Global** | **7/10** | **Q&A diario: listo para producción. Análisis complejo: ajustar timeout.** |

> Informe de evaluación completo: [`artifacts/plan_20260404_opencmo_ask_boundary_eval.md`](artifacts/plan_20260404_opencmo_ask_boundary_eval.md)

### Configuración óptima

```bash
# .env — configuración recomendada post-evaluación
OPENAI_BASE_URL=https://tu-endpoint-compatible-openai/v1
OPENAI_API_KEY=tu-key
OPENAI_MODEL=tu-modelo

# El ajuste más impactante: subir timeout de ask de 45s a 120s
AG_ASK_TIMEOUT_SECONDS=120
AG_REFRESH_AGENT_TIMEOUT_SECONDS=180
AG_MODULE_AGENT_TIMEOUT_SECONDS=90
```

> Funciona con cualquier proveedor compatible con OpenAI: **NVIDIA**, **OpenAI**, **Ollama**, **vLLM**, **LM Studio**, **Groq**, **MiniMax**, etc.

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
