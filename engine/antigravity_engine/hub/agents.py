"""OpenAI Agent SDK agents for the Knowledge Hub.

Two multi-agent swarms:

Refresh Swarm (ag refresh) — 3 agents:
    ScanAnalyst → ArchitectureReviewer → ConventionWriter

Ask Swarm (ag ask) — 3 agents:
    ContextCurator → DeepAnalyst → AnswerSynthesizer
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from antigravity_engine.config import Settings


def create_model(settings: "Settings") -> str:
    """Resolve an LLM model identifier from settings.

    Priority:
    1. GOOGLE_API_KEY              → litellm/gemini/<model_name>
    2. OPENAI_BASE_URL (any key)   → litellm/openai/<model> (custom endpoint)
    3. OPENAI_API_KEY (no base)    → <OPENAI_MODEL> (standard OpenAI)
    4. None                        → raise ValueError

    When a custom OPENAI_BASE_URL is provided (e.g. NVIDIA, Ollama), the
    model is routed through litellm so that the Agent SDK can reach the
    non-standard endpoint.  The function also exports OPENAI_API_BASE for
    litellm discovery.

    Args:
        settings: Application settings.

    Returns:
        A model string suitable for openai-agents[litellm].

    Raises:
        ValueError: When no LLM backend is configured.
    """
    import os

    if settings.GOOGLE_API_KEY:
        return f"litellm/gemini/{settings.GEMINI_MODEL_NAME}"

    # Custom endpoint (NVIDIA, Ollama, etc.) — route through litellm
    if settings.OPENAI_BASE_URL:
        os.environ.setdefault("OPENAI_API_BASE", settings.OPENAI_BASE_URL)
        if settings.OPENAI_API_KEY:
            os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        return f"litellm/openai/{settings.OPENAI_MODEL}"

    # Standard OpenAI (no custom base URL)
    if settings.OPENAI_API_KEY:
        return settings.OPENAI_MODEL

    raise ValueError(
        "No LLM configured. Set GOOGLE_API_KEY, OPENAI_API_KEY, "
        "or OPENAI_BASE_URL in .env"
    )


def _import_agent():
    """Import Agent class with a helpful error message."""
    try:
        from agents import Agent
        return Agent
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None


# ---------------------------------------------------------------------------
# Refresh Swarm — 3 agents: ScanAnalyst → ArchitectureReviewer → ConventionWriter
# ---------------------------------------------------------------------------

_SCAN_ANALYST_INSTRUCTIONS = """\
You are a code analyst specializing in language and framework detection.

Given a project scan report, perform deep analysis of:
- Programming languages and their distribution (primary vs secondary)
- Frameworks and libraries detected (web, data, ML, etc.)
- Code patterns and style observations (naming, structure, idioms)
- Dependency management approach

Produce a structured analysis in bullet points. Be specific — cite file
counts and concrete patterns, not vague observations.

When your analysis is complete, hand off to ArchitectureReviewer for
structural and DevOps analysis.
"""

_ARCHITECTURE_REVIEWER_INSTRUCTIONS = """\
You are a software architecture reviewer.

Building on the previous code analysis, focus on:
- Project directory structure and organization patterns
- Testing approach, framework, and coverage indicators
- CI/CD pipeline setup and automation
- Docker/container configuration
- Build system and packaging approach
- Configuration management patterns

Add your structural findings to the analysis chain. Be specific — name
directories, config files, and tools you observe.

When your review is complete, hand off to ConventionWriter to produce the
final conventions document.
"""

_CONVENTION_WRITER_INSTRUCTIONS = """\
You are a technical writer specializing in developer documentation.

Using ALL analysis from the previous agents (code analysis + architecture
review), produce a concise conventions document in Markdown. The document
must cover:
- Primary language(s) and framework(s)
- Project structure overview
- Code style observations
- Testing approach
- CI/CD setup

Keep it under 300 words. Output ONLY the Markdown content, no preamble,
no commentary. Start directly with a heading.
"""


def build_refresh_swarm(model: str):
    """Build the Refresh Swarm — a 3-agent chain for project analysis.

    Flow: ScanAnalyst → ArchitectureReviewer → ConventionWriter

    Args:
        model: Model identifier string.

    Returns:
        The entry-point Agent (ScanAnalyst). Pass it to Runner.run().
    """
    Agent = _import_agent()

    convention_writer = Agent(
        name="ConventionWriter",
        instructions=_CONVENTION_WRITER_INSTRUCTIONS,
        model=model,
    )

    architecture_reviewer = Agent(
        name="ArchitectureReviewer",
        instructions=_ARCHITECTURE_REVIEWER_INSTRUCTIONS,
        model=model,
        handoffs=[convention_writer],
    )

    scan_analyst = Agent(
        name="ScanAnalyst",
        instructions=_SCAN_ANALYST_INSTRUCTIONS,
        model=model,
        handoffs=[architecture_reviewer],
    )

    return scan_analyst


# ---------------------------------------------------------------------------
# Ask Swarm — Router-Worker pattern with scoped area agents
# ---------------------------------------------------------------------------

_ROUTER_INSTRUCTIONS = """\
You are the Router agent for a software project Q&A system.

You have access to the project's **structure map** (provided in the prompt)
which tells you what code areas exist, what modules/classes/functions are
in each area, and their purpose.

Your job:
1. Read the user's question carefully.
2. Based on the structure map, identify which project area(s) are most
   likely to contain the answer (e.g. "engine/antigravity_engine/hub/"
   for a question about the Knowledge Hub).
3. Hand off to the appropriate **AreaWorker** agent.  Each worker is
   scoped to a specific directory and has tools to search/read code
   and check git history **only within that area**.
4. If the question spans multiple areas, hand off to the worker for
   the most relevant area first — it will hand back to you if needed.

When workers return findings, synthesize them into a final answer:
- Lead with a direct answer to the question
- **Cite specific file paths, line numbers, and function names**
- Include commit history when it explains "why"
- Be concise — under 200 words unless the question demands more

Output ONLY the final answer.  No preamble.
"""

_AREA_WORKER_INSTRUCTIONS_TEMPLATE = """\
You are an AreaWorker agent responsible for the **{area}** directory.

You have tools to search code, read files, list directories, and check
git history — all scoped to your area.  Use them to find concrete
evidence that answers the Router's question.

Steps:
1. Use ``search_code`` to find relevant code within your area.
2. Use ``read_file`` to inspect the actual source of promising files.
3. Use ``list_directory`` to explore sub-directories if needed.
4. Use ``git_file_history`` to check when/why key files were changed.

Return your findings with:
- Exact file paths and line numbers
- Function/class signatures
- Relevant code snippets (keep them short)
- Git commit messages that explain intent

Be thorough but concise.  Hand off back to Router when done.
"""


def _wrap_tools(tool_dict: dict) -> list:
    """Wrap plain functions with the Agent SDK ``function_tool`` decorator.

    Args:
        tool_dict: Mapping of tool name to callable (from create_ask_tools).

    Returns:
        List of decorated tool functions.
    """
    try:
        from agents import function_tool
    except ImportError:
        return []

    wrapped: list = []
    for fn in tool_dict.values():
        wrapped.append(function_tool(fn))
    return wrapped


def _detect_areas(workspace: Path) -> list[str]:
    """Detect the top-level code areas in a project.

    An "area" is a top-level directory that contains source code files.
    Directories like .git, node_modules, etc. are excluded.

    Args:
        workspace: Project root directory.

    Returns:
        List of relative directory paths (e.g. ["engine", "cli", "docs"]).
    """
    skip = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
        ".next", ".nuxt", "target", "vendor", ".antigravity", ".context",
        "artifacts", ".github",
    }
    areas: list[str] = []
    try:
        for item in sorted(workspace.iterdir()):
            if not item.is_dir():
                continue
            if item.name.startswith(".") or item.name in skip:
                continue
            if item.name.endswith(".egg-info"):
                continue
            # Only count directories that contain at least one source file
            has_source = any(
                f.is_file() and not f.name.startswith(".")
                for f in item.rglob("*")
                if f.is_file()
            )
            if has_source:
                areas.append(item.name)
    except OSError:
        pass

    # Always include root-level source files as a pseudo-area
    root_files = [
        f for f in workspace.iterdir()
        if f.is_file() and f.suffix in (".py", ".js", ".ts", ".go", ".rs")
    ]
    if root_files:
        areas.insert(0, ".")

    return areas


def build_ask_swarm(model: str, workspace: Optional[Path] = None):
    """Build the Ask Swarm using a Router-Worker pattern.

    The Router reads the project structure map and dispatches questions
    to scoped AreaWorker agents.  Each worker has code exploration tools
    limited to its directory area.

    Args:
        model: Model identifier string.
        workspace: Project root directory.  When ``None`` the swarm
            falls back to a single agent without tools.

    Returns:
        The entry-point Agent (Router). Pass it to Runner.run().
    """
    Agent = _import_agent()

    if workspace is None:
        # Fallback: single agent, no tools (backward-compatible)
        return Agent(
            name="AskAgent",
            instructions=(
                "Answer the user's question about the project based on "
                "the provided context.  Be concise and cite file paths."
            ),
            model=model,
        )

    from antigravity_engine.hub.ask_tools import create_ask_tools

    # Detect project areas and create a scoped worker for each.
    areas = _detect_areas(workspace)
    workers: list = []

    for area in areas:
        area_path = workspace if area == "." else workspace / area
        area_tools = create_ask_tools(area_path)
        wrapped = _wrap_tools(area_tools)

        display_name = "(root)" if area == "." else area
        worker = Agent(
            name=f"Worker_{area.replace('/', '_').replace('.', 'root')}",
            instructions=_AREA_WORKER_INSTRUCTIONS_TEMPLATE.format(area=display_name),
            model=model,
            tools=wrapped,
        )
        workers.append(worker)

    # Also create a "full project" worker as fallback when no area matches.
    full_tools = create_ask_tools(workspace)
    full_worker = Agent(
        name="Worker_full_project",
        instructions=_AREA_WORKER_INSTRUCTIONS_TEMPLATE.format(area="entire project"),
        model=model,
        tools=_wrap_tools(full_tools),
    )
    workers.append(full_worker)

    # Router can hand off to any worker; workers hand back to Router.
    router = Agent(
        name="Router",
        instructions=_ROUTER_INSTRUCTIONS,
        model=model,
        handoffs=workers,
    )

    # Workers hand back to Router after completing their investigation.
    for worker in workers:
        worker.handoffs = [router]

    return router


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by existing tests)
# ---------------------------------------------------------------------------

def build_refresh_agent(model: str):
    """Build the refresh swarm entry-point agent.

    Args:
        model: Model identifier string.

    Returns:
        The entry-point Agent for the Refresh Swarm.
    """
    return build_refresh_swarm(model)


def build_reviewer_agent(model: str, workspace: Optional[Path] = None):
    """Build the ask swarm entry-point agent.

    Args:
        model: Model identifier string.
        workspace: Project root directory (passed to build_ask_swarm).

    Returns:
        The entry-point Agent for the Ask Swarm.
    """
    return build_ask_swarm(model, workspace=workspace)
