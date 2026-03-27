<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# AI Workspace Template

### La capa cognitiva que falta en los IDEs de IA.

Un comando. Cada IDE de IA se convierte en experto en tu codebase.

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

La mayoría de los equipos llenan `CLAUDE.md` con miles de líneas de documentación que el agente lee y olvida. Antigravity toma el camino opuesto: en lugar de un volcado estático de conocimiento, le da a tu IDE de IA un **motor de Q&A en vivo** respaldado por un pipeline multi-agente que realmente lee tu código.

```
Enfoque tradicional:                    Enfoque Antigravity:
  CLAUDE.md = 5000 líneas de docs         Claude Code llama ask_project("¿cómo funciona auth?")
  El agente lee todo, olvida la mitad     Router-Worker lee código real, devuelve respuesta exacta
  La tasa de alucinación sigue alta       Fundamentado en código real, rutas de archivo y git
```

| Problema | Sin Antigravity | Con Antigravity |
|:---------|:---------------|:----------------|
| El agente olvida el estilo de código | Repites las mismas correcciones | Lee `.antigravity/conventions.md` — lo hace bien a la primera |
| Incorporar un codebase nuevo | El agente adivina la arquitectura | `ag refresh` escanea y documenta automáticamente |
| Cambiar entre IDEs | Reglas diferentes en cada uno | Una carpeta `.antigravity/` — todos los IDEs la comparten |
| Preguntar "¿cómo funciona X?" | El agente lee archivos al azar | La herramienta MCP `ask_project` devuelve respuestas con números de línea |

La arquitectura son **archivos + un motor Q&A en vivo**, no plugins. Portable entre cualquier IDE, cualquier LLM, cero lock-in.

---

## Inicio Rápido

**Opción A — Solo archivos de contexto (cualquier IDE, sin LLM)**
```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto && cd mi-proyecto
# Tu IDE lee automáticamente .antigravity/rules.md, .cursorrules, CLAUDE.md, AGENTS.md
```

**Opción B — Configuración completa con motor Q&A en vivo (recomendado para Claude Code)**
```bash
# 1. Inyectar archivos de contexto
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto && cd mi-proyecto

# 2. Instalar el motor
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# 3. Configurar .env con tu API key de LLM, luego escanear el proyecto
ag refresh

# 4. Registrar como servidor MCP — Claude Code puede usar ask_project como herramienta
claude mcp add antigravity ag-mcp -- --workspace $(pwd)
```

Ahora cuando Claude Code necesita entender tu codebase, llama `ask_project("...")` en lugar de adivinar.

---

## Características de un Vistazo

```
  ag init           Inyectar archivos de contexto (--force para sobrescribir)
       │
       ▼
  .antigravity/     Base de conocimiento compartida — cada IDE lee de aquí
       │
       ├──► ag refresh     Escaneo multi-agente → conventions.md + structure.md
       ├──► ag ask         Q&A Router-Worker con contexto + evidencia de código
       └──► ag start-engine   Runtime completo Think-Act-Reflect
```

**Knowledge Hub** — Pipeline multi-agente que escanea tu codebase, entiende lenguajes/frameworks/estructura, escribe documentación viva y genera un mapa estructural del proyecto para preguntas posteriores. Basado en OpenAI Agent SDK + LiteLLM, funciona con Gemini, OpenAI, Ollama, o cualquier API compatible.

**Herramientas Zero-Config** — Coloca un archivo `.py` en `tools/`, añade type hints y docstring. El agente lo descubre automáticamente al iniciar.

**Memoria Infinita** — Resumen recursivo comprime el historial de conversación. Ejecuta por horas sin alcanzar límites de tokens.

**Swarm Multi-Agente** — Orquestación Router-Worker delega tareas a agentes especialistas (Coder, Reviewer, Researcher) y sintetiza resultados.

---

## Comandos CLI

| Comando | Qué hace | ¿Necesita LLM? |
|:--------|:---------|:---------------:|
| `ag init <dir>` | Inyectar plantillas de arquitectura cognitiva | No |
| `ag init <dir> --force` | Re-inyectar, sobrescribiendo archivos existentes | No |
| `ag refresh` | Escanear proyecto, generar `.antigravity/conventions.md` y `.antigravity/structure.md` | Sí |
| `ag ask "pregunta"` | Responder preguntas usando contexto compartido y exploración de código acotada | Sí |
| `ag-mcp --workspace <dir>` | **Iniciar servidor MCP** — expone `ask_project` + `refresh_project` a Claude Code | Sí |
| `ag report "mensaje"` | Registrar un hallazgo en `.antigravity/memory/` | No |
| `ag log-decision "qué" "por qué"` | Registrar una decisión arquitectónica | No |
| `ag start-engine` | Lanzar el runtime completo del Agent Engine | Sí |

Todos los comandos aceptan `--workspace <dir>` para apuntar a cualquier directorio.

---

## Dos Paquetes, Un Flujo de Trabajo

```
antigravity-workspace-template/
├── cli/                     # ag CLI — ligero, instalable con pip
│   └── templates/           # .cursorrules, CLAUDE.md, .antigravity/, ...
└── engine/                  # Agent Engine — runtime completo + Knowledge Hub
    └── antigravity_engine/
        ├── agent.py         # Bucle Think-Act-Reflect (Gemini / OpenAI / Ollama)
        ├── hub/             # Knowledge Hub (escáner → agentes → pipeline)
        ├── tools/           # Coloca un .py → auto-descubierto como herramienta
        ├── agents/          # Agentes especialistas (Coder, Reviewer, Researcher)
        ├── swarm.py         # Orquestación multi-agente (Router-Worker)
        └── sandbox/         # Ejecución de código (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Cero deps de LLM. Inyecta plantillas, registra reportes y decisiones offline.

**Engine** (`pip install .../engine`) — Runtime completo. Alimenta `ag ask`, `ag refresh`, `ag start-engine`. Soporta Gemini, OpenAI, Ollama, o cualquier API compatible con OpenAI.

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

### 2. `ag refresh` — Construir inteligencia del proyecto

```bash
ag refresh --workspace mi-proyecto
```

Escanea tu código (lenguajes, frameworks, estructura), alimenta el escaneo a un pipeline multi-agente, escribe `.antigravity/conventions.md` y genera `.antigravity/structure.md` como mapa esquelético del código para preguntas posteriores. La próxima vez que tu IDE abra, lee contexto más rico.

### 3. `ag ask` — Consultar tu proyecto

```bash
ag ask "¿Cómo funciona la autenticación en este proyecto?"
```

Lee `.antigravity/structure.md`, `.antigravity/conventions.md`, documentación del proyecto y logs de memoria, y luego usa un ask swarm Router-Worker con herramientas acotadas de búsqueda de código para devolver una respuesta fundamentada.

### 4. Construir herramientas — Zero config

```python
# engine/antigravity_engine/tools/my_tool.py
def check_api_health(url: str) -> str:
    """Verifica si un endpoint API está respondiendo."""
    import requests
    return "up" if requests.get(url).ok else "down"
```

Coloca el archivo, reinicia. El agente lo descubre automáticamente vía type hints + docstrings.

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

Claude Code no necesita leer cientos de archivos de documentación — puede llamar `ask_project` como herramienta en vivo, respaldada por un enjambre Router-Worker que realmente lee tu código fuente y devuelve respuestas precisas con rutas de archivo y números de línea.

**Configuración:**

```bash
# Instalar motor
pip install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"

# Escanear proyecto primero (construye la base de conocimiento)
ag refresh --workspace /ruta/al/proyecto

# Registrar como servidor MCP en Claude Code
claude mcp add antigravity ag-mcp -- --workspace /ruta/al/proyecto
```

**Herramientas expuestas a Claude Code:**

| Herramienta | Qué hace |
|:------------|:---------|
| `ask_project(pregunta)` | Responde cualquier pregunta sobre el codebase — dónde vive el código, por qué se tomaron decisiones, cómo se conectan los módulos. Devuelve rutas de archivo + números de línea. |
| `refresh_project(quick?)` | Reconstruir la base de conocimiento tras cambios significativos. `quick=true` solo escanea archivos modificados. |

**Sin ag-mcp:** Claude Code adivina, lee archivos aleatorios, a veces se equivoca.
**Con ag-mcp:** Claude Code consulta el motor de conocimiento y obtiene respuestas basadas en evidencia real.

</details>

<details>
<summary><b>Knowledge Hub</b> — Pipeline de inteligencia de proyecto multi-agente</summary>

El Hub escanea tu proyecto, identifica lenguajes/frameworks/estructura, y usa un pipeline multi-agente (OpenAI Agent SDK + LiteLLM) para generar documentación viva y un mapa estructural para el enrutamiento posterior:

```bash
# Generar convenciones y mapa estructural desde el escaneo del código
ag refresh

# Solo escanear archivos cambiados desde el último refresh
ag refresh --quick

# Hacer preguntas fundamentadas en el contexto del proyecto y evidencia viva de código
ag ask "¿Qué patrones de testing usa este proyecto?"

# Registrar hallazgos y decisiones (sin LLM)
ag report "El módulo de auth necesita refactoring"
ag log-decision "Usar PostgreSQL" "El equipo tiene experiencia profunda"
```

Funciona con Gemini, OpenAI, Ollama, o cualquier endpoint compatible con OpenAI.
</details>

<details>
<summary><b>Integración MCP</b> — Conectar herramientas externas (GitHub, bases de datos, filesystems)</summary>

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

Configura `MCP_ENABLED=true` en `.env`. Ver [docs MCP](docs/es/MCP_INTEGRATION.md).
</details>

<details>
<summary><b>Integración GitNexus</b> — Inteligencia profunda de código opcional (herramienta de terceros)</summary>

[GitNexus](https://github.com/abhigyanpatwari/GitNexus) es una **herramienta de terceros** que construye un grafo de conocimiento de código usando Tree-sitter AST. Antigravity proporciona hooks de integración incorporados — cuando instalas GitNexus por separado, `ag ask` lo detecta automáticamente y desbloquea tres herramientas adicionales:

| Herramienta | Función |
|:------------|:--------|
| `gitnexus_query` | Búsqueda híbrida (BM25 + semántica) — superior a grep para consultas semánticas |
| `gitnexus_context` | Vista 360° de un símbolo: llamadores, llamados, referencias, definición |
| `gitnexus_impact` | Análisis de radio de explosión — ¿qué se rompe si cambias un símbolo? |

> **Nota:** GitNexus **NO** viene incluido con Antigravity. Es un proyecto independiente que requiere instalación separada vía npm. Antigravity funciona completamente sin él — GitNexus es una mejora opcional para comprensión más profunda del código.

**Cómo habilitar (3 pasos):**

```bash
# 1. Instalar GitNexus (requiere Node.js)
npm install -g gitnexus

# 2. Indexar tu proyecto (operación única, crea un grafo local)
cd my-project
gitnexus analyze .

# 3. Usar ag ask como siempre — las herramientas GitNexus se detectan automáticamente
ag ask "¿Cómo funciona el flujo de autenticación?"
```

**Cómo funciona la integración:** `ask_tools.py` verifica si el CLI `gitnexus` está disponible en tu sistema. Si lo encuentra, registra `gitnexus_query`/`gitnexus_context`/`gitnexus_impact` como herramientas adicionales. Si no lo encuentra, estas herramientas simplemente no aparecen — cero overhead, sin errores.
</details>

<details>
<summary><b>Swarm Multi-Agente</b> — Orquestación Router-Worker para tareas complejas</summary>

```python
from antigravity_engine.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("Construir y revisar una calculadora")
# Enruta a Coder → Reviewer → Researcher, sintetiza resultados
```

Ver [docs Swarm](docs/es/SWARM_PROTOCOL.md).
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
$ ag refresh --workspace .
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
$ ag ask "¿Qué backends LLM soporta este proyecto?"
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
