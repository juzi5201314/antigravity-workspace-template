"""Hub pipelines — refresh and ask."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


async def refresh_pipeline(workspace: Path, quick: bool = False) -> None:
    """Scan project and update .antigravity/conventions.md.

    Args:
        workspace: Project root directory.
        quick: If True, only scan files changed since last refresh.
    """
    from agents import set_tracing_disabled

    set_tracing_disabled(True)

    from antigravity_engine.config import Settings
    from antigravity_engine.hub.agents import build_refresh_agent, create_model
    from antigravity_engine.hub.scanner import extract_structure, full_scan, quick_scan

    settings = Settings()
    model = create_model(settings)

    sha_file = workspace / ".antigravity" / ".last_refresh_sha"

    print("[1/3] Scanning project...", file=sys.stderr)

    if quick and sha_file.exists():
        since_sha = sha_file.read_text(encoding="utf-8").strip()
        report = quick_scan(workspace, since_sha)
    else:
        report = full_scan(workspace)

    # Build prompt from scan report
    prompt = _format_scan_report(report)

    agent = build_refresh_agent(model)
    try:
        from agents import Runner
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None

    print("[2/3] Analyzing with multi-agent swarm...", file=sys.stderr)

    result = await Runner.run(agent, prompt)
    conventions_content = result.final_output

    print("[3/4] Writing conventions.md...", file=sys.stderr)

    # Write conventions
    ag_dir = workspace / ".antigravity"
    ag_dir.mkdir(parents=True, exist_ok=True)
    (ag_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

    # Generate structure map (pure Python, no LLM)
    print("[4/4] Generating structure.md...", file=sys.stderr)
    structure_content = extract_structure(workspace)
    (ag_dir / "structure.md").write_text(structure_content, encoding="utf-8")

    # Save SHA checkpoint
    current_sha = _get_head_sha(workspace)
    if current_sha:
        sha_file.write_text(current_sha, encoding="utf-8")

    print(f"Updated {ag_dir / 'conventions.md'}")
    print(f"Updated {ag_dir / 'structure.md'}")


def _read_context_file(path: Path, label: str) -> str | None:
    """Read a context file and wrap it with a label for prompt injection."""
    if not path.exists() or not path.is_file():
        return None

    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not content:
        return None

    return f"--- {label} ---\n{content}"


def _build_ask_context(workspace: Path) -> str:
    """Collect the most useful project context documents for Q&A."""
    context_parts: list[str] = []

    static_sources = [
        (
            workspace / ".antigravity" / "structure.md",
            ".antigravity/structure.md",
        ),
        (
            workspace / ".antigravity" / "conventions.md",
            ".antigravity/conventions.md",
        ),
        (workspace / ".antigravity" / "rules.md", ".antigravity/rules.md"),
        (
            workspace / ".antigravity" / "decisions" / "log.md",
            ".antigravity/decisions/log.md",
        ),
        (workspace / "CONTEXT.md", "CONTEXT.md"),
        (workspace / "AGENTS.md", "AGENTS.md"),
    ]

    for path, label in static_sources:
        rendered = _read_context_file(path, label)
        if rendered:
            context_parts.append(rendered)

    memory_dir = workspace / ".antigravity" / "memory"
    if memory_dir.exists():
        for memory_file in sorted(memory_dir.glob("*.md")):
            rendered = _read_context_file(
                memory_file,
                f".antigravity/memory/{memory_file.name}",
            )
            if rendered:
                context_parts.append(rendered)

    return "\n\n".join(context_parts) if context_parts else "(no context available)"


async def ask_pipeline(workspace: Path, question: str) -> str:
    """Answer a question about the project.

    Args:
        workspace: Project root directory.
        question: Natural language question.

    Returns:
        Answer string.
    """
    from agents import set_tracing_disabled

    set_tracing_disabled(True)

    from antigravity_engine.config import Settings
    from antigravity_engine.hub.agents import build_reviewer_agent, create_model

    settings = Settings()
    model = create_model(settings)

    print("[1/3] Gathering project context...", file=sys.stderr)

    context = _build_ask_context(workspace)
    prompt = f"Project context:\n{context}\n\nQuestion: {question}"

    agent = build_reviewer_agent(model, workspace=workspace)
    try:
        from agents import Runner
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None

    print("[2/3] Analyzing with multi-agent swarm...", file=sys.stderr)

    result = await Runner.run(agent, prompt, max_turns=25)

    print("[3/3] Synthesizing answer...", file=sys.stderr)

    return result.final_output


def _format_scan_report(report) -> str:
    """Format a ScanReport into a prompt string."""
    lines = [f"Project root: {report.root}"]

    if report.languages:
        lines.append("\nLanguages (file count):")
        for lang, count in list(report.languages.items())[:10]:
            lines.append(f"  - {lang}: {count}")

    if report.frameworks:
        lines.append("\nFrameworks/Tools detected:")
        for fw in report.frameworks:
            lines.append(f"  - {fw}")

    if report.top_dirs:
        lines.append(f"\nTop-level directories: {', '.join(report.top_dirs)}")

    lines.append(f"\nTotal files: {report.file_count}")
    lines.append(f"Has tests: {report.has_tests}")
    lines.append(f"Has CI: {report.has_ci}")
    lines.append(f"Has Docker: {report.has_docker}")

    if report.readme_snippet:
        lines.append(f"\nREADME excerpt:\n{report.readme_snippet}")

    # --- Phase 1: config files, entry points, git history ---
    if getattr(report, "config_contents", None):
        lines.append("\n--- Configuration files (actual content) ---")
        for name, content in report.config_contents.items():
            lines.append(f"\n### {name}\n```\n{content}\n```")

    if getattr(report, "entry_points", None):
        lines.append("\n--- Entry point files (first lines) ---")
        for name, content in report.entry_points.items():
            lines.append(f"\n### {name}\n```\n{content}\n```")

    git_summary = getattr(report, "git_summary", "")
    if git_summary:
        lines.append(f"\n--- Git activity ---\n{git_summary}")

    return "\n".join(lines)


def _get_head_sha(workspace: Path) -> str | None:
    """Get the current HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(workspace),
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None
