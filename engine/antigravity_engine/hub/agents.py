"""OpenAI Agent SDK agents for the Knowledge Hub.

Two multi-agent swarms:

Refresh Swarm (ag refresh) — 3 agents:
    ScanAnalyst → ArchitectureReviewer → ConventionWriter

Ask Swarm (ag ask) — 3 agents:
    ContextCurator → DeepAnalyst → AnswerSynthesizer
"""
from __future__ import annotations

from typing import TYPE_CHECKING

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
# Ask Swarm — 3 agents: ContextCurator → DeepAnalyst → AnswerSynthesizer
# ---------------------------------------------------------------------------

_CONTEXT_CURATOR_INSTRUCTIONS = """\
You are a context curator for a software project.

Given project context documents and a user question, your job is to:
- Identify which parts of the context are most relevant to the question
- Extract and organize the key information
- Note any gaps where context is insufficient
- Flag related files, patterns, or decisions that might be relevant

Produce a focused context brief — only the information needed to answer
the question well. Discard irrelevant details.

When your curation is complete, hand off to DeepAnalyst for thorough
analysis of the question.
"""

_DEEP_ANALYST_INSTRUCTIONS = """\
You are a senior software analyst.

Using the curated context from the previous agent, perform deep analysis:
- Answer the core question with specific technical detail
- Reference concrete files, directories, and code patterns
- Consider edge cases, trade-offs, and implications
- Connect related decisions or patterns if relevant

Your analysis should be thorough but structured. Use bullet points for
clarity.

When your analysis is complete, hand off to AnswerSynthesizer for the
final user-facing response.
"""

_ANSWER_SYNTHESIZER_INSTRUCTIONS = """\
You are an expert communicator for technical teams.

Using ALL analysis from the previous agents, produce the final answer:
- Lead with a direct, clear answer to the question
- Support with specific references (files, patterns, decisions)
- Be actionable — if the user should do something, say what
- Be concise — under 200 words unless the question demands more

Output ONLY the final answer. No preamble like "Based on the analysis..."
— just answer directly.
"""


def build_ask_swarm(model: str):
    """Build the Ask Swarm — a 3-agent chain for project Q&A.

    Flow: ContextCurator → DeepAnalyst → AnswerSynthesizer

    Args:
        model: Model identifier string.

    Returns:
        The entry-point Agent (ContextCurator). Pass it to Runner.run().
    """
    Agent = _import_agent()

    answer_synthesizer = Agent(
        name="AnswerSynthesizer",
        instructions=_ANSWER_SYNTHESIZER_INSTRUCTIONS,
        model=model,
    )

    deep_analyst = Agent(
        name="DeepAnalyst",
        instructions=_DEEP_ANALYST_INSTRUCTIONS,
        model=model,
        handoffs=[answer_synthesizer],
    )

    context_curator = Agent(
        name="ContextCurator",
        instructions=_CONTEXT_CURATOR_INSTRUCTIONS,
        model=model,
        handoffs=[deep_analyst],
    )

    return context_curator


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


def build_reviewer_agent(model: str):
    """Build the ask swarm entry-point agent.

    Args:
        model: Model identifier string.

    Returns:
        The entry-point Agent for the Ask Swarm.
    """
    return build_ask_swarm(model)
