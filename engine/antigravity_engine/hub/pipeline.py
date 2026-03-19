"""Hub pipelines - refresh and ask."""
from __future__ import annotations

import subprocess
from pathlib import Path


async def refresh_pipeline(workspace: Path, quick: bool = False) -> None:
    """Scan project and update .antigravity/conventions.md.

    Args:
        workspace: Project root directory.
        quick: If True, only scan files changed since last refresh.
    """
    from antigravity_engine.config import Settings
    from antigravity_engine.hub.agents import build_refresh_agent, create_model
    from antigravity_engine.hub.scanner import full_scan, quick_scan

    settings = Settings()
    model = create_model(settings)

    sha_file = workspace / ".antigravity" / ".last_refresh_sha"

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

    result = await Runner.run(agent, prompt)
    conventions_content = result.final_output

    # Write conventions
    ag_dir = workspace / ".antigravity"
    ag_dir.mkdir(parents=True, exist_ok=True)
    (ag_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

    # Save SHA checkpoint
    current_sha = _get_head_sha(workspace)
    if current_sha:
        sha_file.write_text(current_sha, encoding="utf-8")

    print(f"Updated {ag_dir / 'conventions.md'}")


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
    from antigravity_engine.config import Settings
    from antigravity_engine.hub.agents import build_reviewer_agent, create_model

    settings = Settings()
    model = create_model(settings)

    context = _build_ask_context(workspace)
    prompt = f"Project context:\n{context}\n\nQuestion: {question}"

    agent = build_reviewer_agent(model)
    try:
        from agents import Runner
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None

    result = await Runner.run(agent, prompt)
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
