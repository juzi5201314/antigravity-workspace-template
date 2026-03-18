<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity" width="200"/>

# Antigravity

**Haz que cualquier IDE de IA sea mas inteligente — en un comando.**

`ag init` inyecta una arquitectura cognitiva en cualquier directorio de proyecto.<br/>
`ag ask` / `ag refresh` mantienen contexto vivo del proyecto mediante analisis multi-agente.

Idioma: [English](README.md) | [中文](README_CN.md) | **Espanol**

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

> **Tesis central**: El techo de capacidad de un AI Agent = la calidad del contexto que puede leer.
>
> La arquitectura son **archivos**, no plugins. `.cursorrules`, `CLAUDE.md`, `.antigravity/rules.md` — estos *son* la arquitectura cognitiva. Portable entre cualquier IDE, cualquier LLM, cero lock-in.

---

## Inicio Rapido

```bash
# Instalar CLI (ligero, sin dependencias de LLM)
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# Inyectar arquitectura cognitiva en cualquier proyecto
ag init mi-proyecto && cd mi-proyecto

# Abrir en Cursor / Claude Code / Windsurf / cualquier IDE de IA → empezar a pedir
```

Eso es todo. Tu IDE ahora lee `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md` automaticamente.

---

## Comandos CLI

| Comando | Que hace | Necesita LLM? |
|:--------|:--------|:-------------:|
| `ag init <dir>` | Inyectar plantillas de arquitectura cognitiva | No |
| `ag refresh` | Escanear proyecto, generar `.antigravity/conventions.md` | Si |
| `ag ask "pregunta"` | Responder preguntas sobre el proyecto | Si |
| `ag report "mensaje"` | Registrar un hallazgo en `.antigravity/memory/` | No |
| `ag log-decision "que" "por que"` | Registrar una decision arquitectonica | No |
| `ag start-engine` | Lanzar el runtime completo del Agent Engine | Si |

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
        ├── hub/             # Knowledge Hub (escaner → agentes → pipeline)
        ├── tools/           # Coloca un .py → auto-descubierto como herramienta
        ├── agents/          # Agentes especialistas (Coder, Reviewer, Researcher)
        ├── swarm.py         # Orquestacion multi-agente (Router-Worker)
        └── sandbox/         # Ejecucion de codigo (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Cero deps de LLM. Inyecta plantillas, registra reportes y decisiones offline.

**Engine** (`pip install .../engine`) — Runtime completo. Alimenta `ag ask`, `ag refresh`, `ag start-engine`. Soporta Gemini, OpenAI, Ollama, o cualquier API compatible con OpenAI.

```bash
# Instalar ambos para la experiencia completa
pip install "git+https://...#subdirectory=cli"
pip install "git+https://...#subdirectory=engine"
```

---

## Como Funciona

### 1. `ag init` — Inyectar archivos de contexto

```bash
ag init mi-proyecto
```

Crea `.antigravity/rules.md`, `.cursorrules`, `CLAUDE.md`, `AGENTS.md`, `.windsurfrules` — cada IDE lee su archivo de configuracion nativo, todos apuntando a la misma base de conocimiento `.antigravity/`.

### 2. `ag refresh` — Construir inteligencia del proyecto

```bash
ag refresh --workspace mi-proyecto
```

Escanea tu codigo (lenguajes, frameworks, estructura), alimenta el escaneo a un pipeline multi-agente, escribe `.antigravity/conventions.md`. La proxima vez que tu IDE abra, lee contexto mas rico.

### 3. `ag ask` — Consultar tu proyecto

```bash
ag ask "Como funciona la autenticacion en este proyecto?"
```

Lee el contexto de `.antigravity/`, lo alimenta a un agente revisor, devuelve una respuesta fundamentada.

### 4. Construir herramientas — Zero config

```python
# engine/antigravity_engine/tools/my_tool.py
def check_api_health(url: str) -> str:
    """Verifica si un endpoint API esta respondiendo."""
    import requests
    return "up" if requests.get(url).ok else "down"
```

Coloca el archivo, reinicia. El agente lo descubre automaticamente via type hints + docstrings.

---

## Compatibilidad de IDEs

La arquitectura esta codificada en **archivos** — cualquier agente que lea archivos del proyecto se beneficia:

| IDE | Archivo de configuracion |
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
<summary><b>Integracion MCP</b> — Conectar herramientas externas (GitHub, bases de datos, filesystems)</summary>

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
<summary><b>Swarm Multi-Agente</b> — Orquestacion Router-Worker para tareas complejas</summary>

```python
from antigravity_engine.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("Construir y revisar una calculadora")
# Enruta a Coder → Reviewer → Researcher, sintetiza resultados
```

Ver [docs Swarm](docs/es/SWARM_PROTOCOL.md).
</details>

<details>
<summary><b>Sandbox</b> — Entorno de ejecucion de codigo configurable</summary>

| Variable | Default | Opciones |
|:---------|:--------|:---------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | segundos |

Ver [docs Sandbox](docs/es/SANDBOX.md).
</details>

---

## Documentacion

| | |
|:--|:--|
| 🇬🇧 English | **[`docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`docs/zh/`](docs/zh/)** |
| 🇪🇸 Espanol | **[`docs/es/`](docs/es/)** |

---

## Contribuyendo

Las ideas tambien son contribuciones! Abre un [issue](https://github.com/study8677/antigravity-workspace-template/issues) para reportar bugs, sugerir funcionalidades o proponer arquitectura.

## Contribuidores

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>Contribuidor Principal</b> · Sugerencias creativas · Administrador del proyecto · Ideacion y feedback</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/devalexanderdaza">
        <img src="https://github.com/devalexanderdaza.png" width="80" /><br/>
        <b>Alexander Daza</b>
      </a><br/>
      <sub>Sandbox MVP · Workflows OpenSpec · Docs de analisis tecnico · PHILOSOPHY</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/chenyi">
        <img src="https://github.com/chenyi.png" width="80" /><br/>
        <b>Chen Yi</b>
      </a><br/>
      <sub>Primer prototipo CLI · Refactor de 753 lineas · Extraccion DummyClient · Docs quick-start</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/Subham-KRLX">
        <img src="https://github.com/Subham-KRLX.png" width="80" /><br/>
        <b>Subham Sangwan</b>
      </a><br/>
      <sub>Carga dinamica de herramientas (#4) · Protocolo swarm multi-agente (#3)</sub>
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

**[📚 Documentacion completa →](docs/es/)**

*Construido para la era del desarrollo AI-nativo*

</div>
