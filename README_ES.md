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

Cada IDE de IA lee archivos del proyecto. Pero sin estructura, los agentes alucinan, olvidan convenciones y producen código inconsistente. Antigravity resuelve esto:

| Problema | Sin Antigravity | Con Antigravity |
|:---------|:---------------|:----------------|
| El agente olvida el estilo de código | Repites las mismas correcciones | Lee `.antigravity/conventions.md` — lo hace bien a la primera |
| Incorporar un codebase nuevo | El agente adivina la arquitectura | `ag refresh` escanea y documenta automáticamente |
| Cambiar entre IDEs | Reglas diferentes en cada uno | Una carpeta `.antigravity/` — todos los IDEs la comparten |
| Preguntar "¿cómo funciona X?" | El agente lee archivos al azar | `ag ask` da respuestas fundamentadas en el contexto del proyecto |

La arquitectura son **archivos**, no plugins. `.cursorrules`, `CLAUDE.md`, `.antigravity/rules.md` — estos *son* la arquitectura cognitiva. Portable entre cualquier IDE, cualquier LLM, cero lock-in.

---

## Inicio Rápido

```bash
# Instalar CLI (ligero, sin dependencias de LLM)
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# Inyectar arquitectura cognitiva en cualquier proyecto
ag init mi-proyecto && cd mi-proyecto

# Abrir en Cursor / Claude Code / Windsurf / cualquier IDE de IA → empezar a trabajar
```

Eso es todo. Tu IDE ahora lee `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md` automáticamente.

---

## Características de un Vistazo

```
  ag init           Inyectar archivos de contexto (--force para sobrescribir)
       │
       ▼
  .antigravity/     Base de conocimiento compartida — cada IDE lee de aquí
       │
       ├──► ag refresh     Escaneo multi-agente → conventions.md auto-generado
       ├──► ag ask         Q&A fundamentada sobre tu proyecto
       └──► ag start-engine   Runtime completo Think-Act-Reflect
```

**Knowledge Hub** — Pipeline multi-agente que escanea tu codebase, entiende lenguajes/frameworks/estructura, y escribe documentación viva. Basado en OpenAI Agent SDK + LiteLLM, funciona con Gemini, OpenAI, Ollama, o cualquier API compatible.

**Herramientas Zero-Config** — Coloca un archivo `.py` en `tools/`, añade type hints y docstring. El agente lo descubre automáticamente al iniciar.

**Memoria Infinita** — Resumen recursivo comprime el historial de conversación. Ejecuta por horas sin alcanzar límites de tokens.

**Swarm Multi-Agente** — Orquestación Router-Worker delega tareas a agentes especialistas (Coder, Reviewer, Researcher) y sintetiza resultados.

---

## Comandos CLI

| Comando | Qué hace | ¿Necesita LLM? |
|:--------|:---------|:---------------:|
| `ag init <dir>` | Inyectar plantillas de arquitectura cognitiva | No |
| `ag init <dir> --force` | Re-inyectar, sobrescribiendo archivos existentes | No |
| `ag refresh` | Escanear proyecto, generar `.antigravity/conventions.md` | Sí |
| `ag ask "pregunta"` | Responder preguntas sobre el proyecto | Sí |
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

Escanea tu código (lenguajes, frameworks, estructura), alimenta el escaneo a un pipeline multi-agente, escribe `.antigravity/conventions.md`. La próxima vez que tu IDE abra, lee contexto más rico.

### 3. `ag ask` — Consultar tu proyecto

```bash
ag ask "¿Cómo funciona la autenticación en este proyecto?"
```

Lee el contexto de `.antigravity/`, lo alimenta a un agente revisor, devuelve una respuesta fundamentada.

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
<summary><b>Knowledge Hub</b> — Pipeline de inteligencia de proyecto multi-agente</summary>

El Hub escanea tu proyecto, identifica lenguajes/frameworks/estructura, y usa un pipeline multi-agente (OpenAI Agent SDK + LiteLLM) para generar documentación viva:

```bash
# Generar convenciones desde el escaneo del código
ag refresh

# Solo escanear archivos cambiados desde el último refresh
ag refresh --quick

# Hacer preguntas fundamentadas en el contexto del proyecto
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
