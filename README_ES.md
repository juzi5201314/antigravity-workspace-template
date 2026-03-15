<div align="center">

<img src="docs/assets/logo.png" alt="Antigravity Workspace" width="200"/>

# Plantilla de Workspace de Antigravity

**Kit inicial de nivel producción para agentes autónomos de IA.**

*Compatible con cualquier IDE de IA · Cualquier CLI · Cualquier LLM*

Idioma: [English](README.md) | [中文](README_CN.md) | **Español**

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

### Deja de dejar que Cursor / Windsurf alucine en carpetas vacías.
### La arquitectura cognitiva **Artifact-First** para IDEs de IA.

<br/>

<img src="docs/assets/before_after.png" alt="Before vs After Antigravity" width="800"/>

<br/>

```bash
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli
ag init mi-proyecto
```

</div>

<br/>

> **`ag init` → Abre tu IDE → Pide. Ese es el flujo de trabajo.**
>
> **Principios Fundamentales**: El techo de capacidad de un AI Agent = la calidad del contexto que puede leer. En vez de depender de plugins de IDE o lock-in de plataforma, volvamos a lo esencial—**la arquitectura son archivos**. Un conjunto cuidadosamente diseñado de `.cursorrules`, `CONTEXT.md`, `.antigravity/rules.md` *es* toda la arquitectura cognitiva. `ag init` la inyecta en cualquier directorio vacío, convirtiendo tu IDE de un editor en un **arquitecto que entiende el negocio**—sin plugins, sin dependencia de proveedor.

---

## 🌍 Compatibilidad Universal

Esta plantilla **no** está atada a ningún IDE específico. Funciona en todas partes:

| Plataforma | Cómo funciona |
|:-----------|:-------------|
| **Google Antigravity** | Lee `.antigravity/rules.md` para conciencia de contexto completa |
| **Cursor** | Lee `.cursorrules` para reglas a nivel de proyecto |
| **Windsurf / VS Code + Copilot** | Usa archivos `.context/` para inyección de conocimiento |
| **Claude Code** | Lee `AGENTS.md` + `CONTEXT.md` para convenciones del proyecto |
| **Gemini CLI** | Lee `AGENTS.md` + `.context/` para inyección de conocimiento |
| **Codex (OpenAI)** | Lee `AGENTS.md` + convenciones de directorio |
| **Cline / Aider** | Aprovecha `CONTEXT.md` + convenciones de directorio |
| **Cualquier agente compatible con OpenAI** | Herramientas auto-descubiertas en `engine/src/tools/`, entrada Python estándar |

El secreto: la arquitectura está codificada en **archivos**, no en plugins específicos del IDE. Cualquier agente que lea archivos del proyecto se beneficia.

---

## ⚡ Inicio Rápido

### Opción 1: Inyecta la arquitectura en cualquier proyecto (Recomendado)

```bash
# 1. Instala el CLI
pip install git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=cli

# 2. Inyecta la arquitectura cognitiva en tu proyecto
ag init mi-proyecto

# 3. ¡Abre en cualquier IDE de IA y empieza a pedir!
```

### Opción 2: Ejecuta el Motor de Agente completo

```bash
# 1. Clona el repositorio
git clone https://github.com/study8677/antigravity-workspace-template.git
cd antigravity-workspace-template

# 2. Instala las dependencias del motor
cd engine
pip install -r requirements.txt

# 3. Configura las claves API
cp .env.example .env && nano .env

# 4. Ejecuta el agente apuntando a cualquier workspace
python agent.py --workspace /ruta/a/tu/proyecto "Tu tarea aquí"
```

**¡Eso es todo!** El IDE carga la configuración automáticamente y estás listo para pedir.

---

## 🎯 ¿Qué es esto?

Esto **no** es otro wrapper de LangChain. Es un workspace mínimo y transparente para construir agentes de IA:

| Característica | Descripción |
|:---------------|:------------|
| 🧠 **Memoria infinita** | Resumización recursiva que comprime contexto automáticamente |
| 🧠 **Pensamiento Real** | Paso de "Deep Think" (Chain-of-Thought) antes de actuar |
| 🎓 **Sistema de Habilidades** | Capacidades modulares en `engine/src/skills/` con carga automática |
| 🛠️ **Herramientas universales** | Funciones Python en `engine/src/tools/` → se descubren solas |
| 📚 **Contexto automático** | Archivos en `.context/` → se inyectan en los prompts |
| 🔌 **Soporte MCP** | Conecta GitHub, bases de datos, sistemas de archivos |
| 🤖 **Agentes Swarm** | Orquestación multiagente con patrón Router-Worker |
| ⚡ **Nativo de Gemini** | Optimizado para Gemini 2.0 Flash |
| 🌐 **Independiente del LLM** | Usa OpenAI, Azure, Ollama o cualquier API compatible |
| 📂 **Artifact-First** | Flujo por convención para planes, logs y evidencia |
| 🔒 **Sandbox** | Ejecución configurable (local / microsandbox) |

---

## 🏗️ Estructura del Proyecto

```
antigravity-workspace-template/
│
├── cli/                          # 🖥️ CLI ligero (ag init)
│   ├── pyproject.toml            #    Config del paquete & punto de entrada
│   └── src/ag_cli/
│       ├── cli.py                #    Comandos CLI (init, start-engine, version)
│       └── templates/            #    Plantillas de arquitectura cognitiva
│           ├── .cursorrules      #    → Inyectado en el proyecto destino
│           ├── .antigravity/     #    → Inyectado en el proyecto destino
│           └── CONTEXT.md        #    → Inyectado en el proyecto destino
│
├── engine/                       # ⚙️ Motor de Agente Python
│   ├── agent.py                  #    Punto de entrada (soporte --workspace)
│   ├── src/
│   │   ├── agent.py              #    Bucle principal (Think-Act-Reflect)
│   │   ├── config.py             #    Configuración (aware del workspace)
│   │   ├── memory.py             #    Gestor de memoria Markdown
│   │   ├── mcp_client.py         #    Integración MCP
│   │   ├── swarm.py              #    Orquestación multiagente
│   │   ├── tools/                #    Herramientas personalizadas (auto-descubiertas)
│   │   ├── agents/               #    Agentes especialistas
│   │   ├── sandbox/              #    Sandbox de ejecución de código
│   │   └── skills/               #    Habilidades modulares (auto-cargadas)
│   ├── tests/                    #    Suite de pruebas
│   └── requirements.txt          #    Dependencias del motor
│
├── docs/                         # 📚 Documentación
├── README.md                     # Este archivo
└── LICENSE                       # MIT
```

---

## 💡 Construye una herramienta en 30 segundos

```python
# engine/src/tools/my_tool.py
def analyze_sentiment(text: str) -> str:
    """Analiza el sentimiento del texto dado."""
    return "positive" if len(text) > 10 else "neutral"
```

**Reinicia el agente.** ¡Listo! La herramienta ya está disponible para cualquier IDE de IA.

---

## 🔌 Integración de MCP

Conecta herramientas externas:

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

## 🤖 Swarm Multiagente

Descompón tareas complejas:

```python
from engine.src.swarm import SwarmOrchestrator

swarm = SwarmOrchestrator()
result = swarm.execute("Construir y revisar una calculadora")
```

El swarm enruta automáticamente a los agentes Coder, Reviewer y Researcher, sintetiza resultados y expone logs.

---

## 🔒 Configuración de Sandbox

| Variable | Default | Opciones |
|:---------|:--------|:---------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | segundos |
| `SANDBOX_MAX_OUTPUT_KB` | `10` | KB |

<details>
<summary><b>Variables extra de Microsandbox</b></summary>

| Variable | Default |
|:---------|:--------|
| `MSB_SERVER_URL` | `http://127.0.0.1:5555` |
| `MSB_API_KEY` | (opcional) |
| `MSB_IMAGE` | `microsandbox/python` |
| `MSB_CPU_LIMIT` | `1.0` |
| `MSB_MEMORY_MB` | `512` |
</details>

---

## 📚 Documentación

| Idioma | Enlace |
|:-------|:-------|
| 🇬🇧 English | **[`/docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`/docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`/docs/es/`](docs/es/)** |

---

## ✅ Progreso

- ✅ Fases 1-8: Foundation, Memory, Tools, Swarm, MCP
- ✅ Fase 9: Refactorización Monorepo V1.0 — Arquitectura desacoplada CLI + Engine
- 🚀 Fase 10: Enterprise Core (próximamente)

Consulta la [Hoja de Ruta](docs/es/ROADMAP.md) para detalles.

---

## 🤝 Contribuyendo

¡Las ideas también cuentan como contribuciones! Abre un [issue](https://github.com/study8677/antigravity-workspace-template/issues) para reportar bugs, sugerir funcionalidades o proponer arquitectura.

## 👥 Contribuidores

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>Contribuidor Principal</b> · Sugerencias creativas · Administrador del proyecto · Ideación y feedback del proyecto</sub>
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
      <sub>Carga dinámica de herramientas (#4) · Protocolo swarm multiagente (#3)</sub>
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

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/antigravity-workspace-template&type=Date)](https://star-history.com/#study8677/antigravity-workspace-template&Date)

## 📄 Licencia

Licencia MIT. Ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**[📚 Explorar documentación completa →](docs/es/)**

*Construido con ❤️ para la era del desarrollo AI-nativo*

</div>
