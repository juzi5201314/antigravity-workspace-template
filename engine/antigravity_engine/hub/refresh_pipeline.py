"""Refresh pipeline — scan the project and generate knowledge artifacts.

Extracted from ``pipeline.py`` to separate the refresh and ask
workflows into dedicated modules.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


async def refresh_pipeline(workspace: Path, quick: bool = False) -> None:
    """Scan project and update .antigravity/conventions.md.

    Args:
        workspace: Project root directory.
        quick: If True, only scan files changed since last refresh.
    """
    from agents import set_tracing_disabled

    set_tracing_disabled(True)

    from antigravity_engine.config import get_settings
    from antigravity_engine.hub.agents import build_refresh_agent, create_model
    from antigravity_engine.hub.scanner import (
        build_knowledge_graph,
        extract_structure,
        full_scan,
        quick_scan,
        render_knowledge_graph_markdown,
        render_knowledge_graph_mermaid,
    )

    settings = get_settings()
    model = create_model(settings)

    sha_file = workspace / ".antigravity" / ".last_refresh_sha"

    scan_timeout = os.environ.get("AG_SCAN_TIMEOUT_SECONDS", "(default)")
    scan_max_files = os.environ.get("AG_SCAN_MAX_FILES", "(default)")
    scan_sample_files = os.environ.get("AG_SCAN_SAMPLE_FILES", "(default)")
    scan_verbose = os.environ.get("AG_SCAN_VERBOSE", "1")
    print(
        (
            "[1/3] Scan config: "
            f"timeout={scan_timeout}, "
            f"max_files={scan_max_files}, "
            f"sample_files={scan_sample_files}, "
            f"verbose={scan_verbose}, "
            f"quick={quick}"
        ),
        file=sys.stderr,
    )

    print("[1/3] Scanning project...", file=sys.stderr)

    if quick and sha_file.exists():
        since_sha = sha_file.read_text(encoding="utf-8").strip()
        report = quick_scan(workspace, since_sha)
    else:
        report = full_scan(workspace)

    print("[1/3] Scan stage finished; preparing scan report...", file=sys.stderr)

    ag_dir = workspace / ".antigravity"
    ag_dir.mkdir(parents=True, exist_ok=True)
    scan_report_path = ag_dir / "scan_report.json"
    scan_payload = _build_scan_payload(report)
    print("[1/3] Scan payload built; writing scan_report.json...", file=sys.stderr)
    scan_report_path.write_text(
        json.dumps(scan_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        (
            "[1/3] Scan summary: "
            f"files={report.file_count}, "
            f"walked={getattr(report, 'walked_file_count', 0)}, "
            f"elapsed={getattr(report, 'scan_elapsed_seconds', 0.0):.2f}s, "
            f"timed_out={getattr(report, 'timed_out', False)}, "
            f"reason={getattr(report, 'scan_stopped_reason', '') or 'completed'}"
        ),
        file=sys.stderr,
    )
    samples = getattr(report, "scanned_file_samples", [])
    if samples:
        print("[1/3] Retrieved file samples:", file=sys.stderr)
        for rel in samples[:20]:
            print(f"  - {rel}", file=sys.stderr)
    print(f"[1/3] Scan report: {scan_report_path}", file=sys.stderr)

    refresh_scan_only = os.environ.get("AG_REFRESH_SCAN_ONLY", "0").strip() in {"1", "true", "yes"}
    conventions_content = ""

    if not refresh_scan_only:
        prompt = _format_scan_report(report)

        agent = build_refresh_agent(model)
        try:
            from agents import Runner
        except ImportError:
            raise ImportError(
                "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
            ) from None

        print("[2/3] Analyzing with multi-agent swarm...", file=sys.stderr)

        refresh_timeout = float(os.environ.get("AG_REFRESH_AGENT_TIMEOUT_SECONDS", "90"))
        if refresh_timeout > 0:
            result = await asyncio.wait_for(Runner.run(agent, prompt), timeout=refresh_timeout)
        else:
            result = await Runner.run(agent, prompt)
        conventions_content = result.final_output
    else:
        print("[2/3] Scan-only mode enabled; skipping LLM analysis.", file=sys.stderr)
        conventions_content = _build_fallback_conventions(report)

    print("[3/7] Writing conventions.md...", file=sys.stderr)

    (ag_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

    # In quick mode the ScanReport only contains changed files, so
    # rebuilding structure / knowledge-graph / non-code indexes from it
    # would overwrite the full artifacts with near-empty content.
    # Skip these stages and keep the previous full-refresh output.
    if not quick:
        print("[4/7] Generating structure.md...", file=sys.stderr)
        structure_content = extract_structure(workspace)
        (ag_dir / "structure.md").write_text(structure_content, encoding="utf-8")

        print("[5/7] Building knowledge graph artifacts...", file=sys.stderr)
        graph = build_knowledge_graph(workspace, report)
        (ag_dir / "knowledge_graph.json").write_text(
            json.dumps(graph, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (ag_dir / "knowledge_graph.md").write_text(
            render_knowledge_graph_markdown(graph),
            encoding="utf-8",
        )
        (ag_dir / "knowledge_graph.mmd").write_text(
            render_knowledge_graph_mermaid(graph),
            encoding="utf-8",
        )

        print("[6/7] Writing document/data/media indexes...", file=sys.stderr)
        doc_index, data_overview, media_manifest = _build_non_code_indexes(report)
        (ag_dir / "document_index.md").write_text(doc_index, encoding="utf-8")
        (ag_dir / "data_overview.md").write_text(data_overview, encoding="utf-8")
        (ag_dir / "media_manifest.md").write_text(media_manifest, encoding="utf-8")
    else:
        print("[4-6/7] Quick mode: keeping existing structure/graph/index artifacts.", file=sys.stderr)

    if not refresh_scan_only:
        print("[7/7] Module agents learning codebase...", file=sys.stderr)
        from antigravity_engine.hub.agents import (
            build_refresh_module_swarm,
            build_refresh_git_agent,
        )

        try:
            from agents import Runner
        except ImportError:
            raise ImportError(
                "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
            ) from None

        module_agents = build_refresh_module_swarm(model, workspace)
        module_timeout = float(os.environ.get("AG_MODULE_AGENT_TIMEOUT_SECONDS", "45"))

        # In quick mode, only run agents for modules affected by changed files.
        if quick:
            affected = _compute_affected_modules(report, [m for m, _ in module_agents])
            if affected is not None:
                original_count = len(module_agents)
                module_agents = [(m, a) for m, a in module_agents if m in affected]
                print(
                    f"  Quick mode: {len(module_agents)}/{original_count} modules affected.",
                    file=sys.stderr,
                )

        for mod_name, mod_agent in module_agents:
            print(f"  → RefreshModule_{mod_name} analyzing...", file=sys.stderr)
            try:
                if module_timeout > 0:
                    await asyncio.wait_for(
                        Runner.run(
                            mod_agent,
                            f"Analyze the '{mod_name}' module thoroughly and write your knowledge document.",
                        ),
                        timeout=module_timeout,
                    )
                else:
                    await Runner.run(
                        mod_agent,
                        f"Analyze the '{mod_name}' module thoroughly and write your knowledge document.",
                    )
            except Exception as exc:
                print(f"  ⚠ RefreshModule_{mod_name} failed: {exc}", file=sys.stderr)

        print("  → RefreshGitAgent analyzing git history...", file=sys.stderr)
        try:
            git_agent = build_refresh_git_agent(model, workspace)
            if module_timeout > 0:
                await asyncio.wait_for(
                    Runner.run(
                        git_agent,
                        "Analyze the project's git history and write your git insights document.",
                    ),
                    timeout=module_timeout,
                )
            else:
                await Runner.run(
                    git_agent,
                    "Analyze the project's git history and write your git insights document.",
                )
        except Exception as exc:
            print(f"  ⚠ RefreshGitAgent failed: {exc}", file=sys.stderr)
    else:
        print("[7/7] Scan-only mode: module agents skipped.", file=sys.stderr)

    current_sha = _get_head_sha(workspace)
    if current_sha:
        sha_file.write_text(current_sha, encoding="utf-8")

    print(f"Updated {ag_dir / 'conventions.md'}")
    print(f"Updated {ag_dir / 'structure.md'}")
    print(f"Updated {ag_dir / 'knowledge_graph.json'}")
    print(f"Updated {ag_dir / 'knowledge_graph.md'}")
    print(f"Updated {ag_dir / 'knowledge_graph.mmd'}")
    print(f"Updated {ag_dir / 'document_index.md'}")
    print(f"Updated {ag_dir / 'data_overview.md'}")
    print(f"Updated {ag_dir / 'media_manifest.md'}")
    modules_dir = ag_dir / "modules"
    if modules_dir.exists():
        mod_count = len(list(modules_dir.glob("*.md")))
        print(f"Updated {modules_dir} ({mod_count} module docs)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    lines.append(f"Scan elapsed seconds: {getattr(report, 'scan_elapsed_seconds', 0.0):.2f}")
    lines.append(f"Scan timed out: {getattr(report, 'timed_out', False)}")
    if getattr(report, "scan_stopped_reason", ""):
        lines.append(f"Scan stop reason: {report.scan_stopped_reason}")
    lines.append(f"Has tests: {report.has_tests}")
    lines.append(f"Has CI: {report.has_ci}")
    lines.append(f"Has Docker: {report.has_docker}")
    if getattr(report, "type_distribution", None):
        lines.append("\nFile types:")
        for ftype, count in report.type_distribution.items():
            lines.append(f"  - {ftype}: {count}")
    lines.append(f"Unreadable files: {getattr(report, 'unreadable_files', 0)}")
    lines.append(f"Oversized files: {getattr(report, 'oversized_files', 0)}")

    if report.readme_snippet:
        lines.append(f"\nREADME excerpt:\n{report.readme_snippet}")

    samples = getattr(report, "scanned_file_samples", [])
    if samples:
        lines.append("\nScanned file samples:")
        for rel in samples[:30]:
            lines.append(f"  - {rel}")

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


def _build_non_code_indexes(report) -> tuple[str, str, str]:
    """Build document/data/media markdown indexes from scan metadata."""
    docs: list[str] = []
    data: list[str] = []
    media: list[str] = []
    for rel, meta in getattr(report, "file_metadata", {}).items():
        ftype = str(meta.get("type", "other"))
        size = int(meta.get("size", 0))
        mime = str(meta.get("mime", "unknown"))
        line = f"- {rel} ({size} bytes, {mime})"
        if ftype == "documentation":
            docs.append(line)
        elif ftype == "data":
            data.append(line)
        elif ftype == "media":
            media.append(line)

    def _render(title: str, items: list[str]) -> str:
        if not items:
            return f"# {title}\n\n(none)\n"
        body = "\n".join(items[:200])
        if len(items) > 200:
            body += f"\n- ... ({len(items) - 200} more)"
        return f"# {title}\n\n{body}\n"

    return (
        _render("Document Index", docs),
        _render("Data Overview", data),
        _render("Media Manifest", media),
    )


def _compute_affected_modules(
    report,
    module_ids: list[str],
) -> set[str] | None:
    """Determine which modules were touched by changed files in a quick scan.

    Returns ``None`` if the impact cannot be determined (e.g. no file
    metadata), in which case the caller should run all modules.

    Args:
        report: ScanReport from quick_scan.
        module_ids: List of known module identifiers.

    Returns:
        Set of affected module identifiers, or None.
    """
    metadata = getattr(report, "file_metadata", None)
    samples = getattr(report, "scanned_file_samples", None)
    changed_paths = list(metadata.keys()) if metadata else (samples or [])
    if not changed_paths:
        return None

    affected: set[str] = set()
    for rel_path in changed_paths:
        parts = rel_path.replace("\\", "/").split("/")
        if not parts:
            continue
        # Match against module IDs — check both simple ("cli") and
        # two-level ("engine_hub") patterns.
        top = parts[0]
        for mid in module_ids:
            if mid == top:
                affected.add(mid)
            elif mid.startswith(f"{top}_") and len(parts) > 1:
                # Two-level: "engine_hub" matches "engine/antigravity_engine/hub/..."
                # Heuristic: if any path component matches the suffix, it's affected.
                suffix = mid.split("_", 1)[1]
                if suffix in parts:
                    affected.add(mid)
    return affected


def _build_scan_payload(report) -> dict[str, object]:
    """Build a JSON-serializable scan payload for traceability."""
    return {
        "root": str(getattr(report, "root", "")),
        "file_count": int(getattr(report, "file_count", 0)),
        "walked_file_count": int(getattr(report, "walked_file_count", 0)),
        "languages": dict(getattr(report, "languages", {}) or {}),
        "frameworks": list(getattr(report, "frameworks", []) or []),
        "type_distribution": dict(getattr(report, "type_distribution", {}) or {}),
        "timed_out": bool(getattr(report, "timed_out", False)),
        "scan_elapsed_seconds": float(getattr(report, "scan_elapsed_seconds", 0.0)),
        "scan_stopped_reason": str(getattr(report, "scan_stopped_reason", "") or ""),
        "scanned_file_samples": list(getattr(report, "scanned_file_samples", []) or []),
        "unreadable_files": int(getattr(report, "unreadable_files", 0)),
        "oversized_files": int(getattr(report, "oversized_files", 0)),
        "binary_files": int(getattr(report, "binary_files", 0)),
    }


def _build_fallback_conventions(report) -> str:
    """Build minimal conventions content when refresh runs in scan-only mode."""
    languages = ", ".join(report.languages.keys()) if getattr(report, "languages", None) else "unknown"
    frameworks = ", ".join(report.frameworks) if getattr(report, "frameworks", None) else "none"
    return (
        "# Project Conventions (Scan-Only)\n\n"
        "This file was generated in scan-only mode without LLM analysis.\n\n"
        f"- Languages: {languages}\n"
        f"- Frameworks: {frameworks}\n"
        f"- File count: {getattr(report, 'file_count', 0)}\n"
        f"- Scan elapsed: {getattr(report, 'scan_elapsed_seconds', 0.0):.2f}s\n"
        f"- Timed out: {getattr(report, 'timed_out', False)}\n"
        f"- Stop reason: {getattr(report, 'scan_stopped_reason', '') or 'completed'}\n"
    )
