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
        try:
            if refresh_timeout > 0:
                result = await asyncio.wait_for(Runner.run(agent, prompt), timeout=refresh_timeout)
            else:
                result = await Runner.run(agent, prompt)
            conventions_content = result.final_output
        except Exception as exc:
            print(f"  ⚠ Conventions swarm failed: {exc}. Using fallback.", file=sys.stderr)
            conventions_content = _build_fallback_conventions(report)
    else:
        print("[2/3] Scan-only mode enabled; skipping LLM analysis.", file=sys.stderr)
        conventions_content = _build_fallback_conventions(report)

    print("[3/8] Writing conventions.md...", file=sys.stderr)

    (ag_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

    # In quick mode the ScanReport only contains changed files, so
    # rebuilding structure / knowledge-graph / non-code indexes from it
    # would overwrite the full artifacts with near-empty content.
    # Skip these stages and keep the previous full-refresh output.
    if not quick:
        print("[4/8] Generating structure.md...", file=sys.stderr)
        structure_content = extract_structure(workspace)
        (ag_dir / "structure.md").write_text(structure_content, encoding="utf-8")

        print("[5/8] Building knowledge graph artifacts...", file=sys.stderr)
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

        print("[6/8] Writing document/data/media indexes...", file=sys.stderr)
        doc_index, data_overview, media_manifest = _build_non_code_indexes(report)
        (ag_dir / "document_index.md").write_text(doc_index, encoding="utf-8")
        (ag_dir / "data_overview.md").write_text(data_overview, encoding="utf-8")
        (ag_dir / "media_manifest.md").write_text(media_manifest, encoding="utf-8")
    else:
        print("[4-6/8] Quick mode: keeping existing structure/graph/index artifacts.", file=sys.stderr)

    if not refresh_scan_only:
        print("[7/8] Module agents learning codebase...", file=sys.stderr)
        from antigravity_engine.hub.agents import (
            build_refresh_module_swarm_v2,
            build_refresh_git_agent,
            _REFRESH_MERGE_INSTRUCTIONS,
        )

        try:
            from agents import Agent, Runner
        except ImportError:
            raise ImportError(
                "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
            ) from None

        module_entries = build_refresh_module_swarm_v2(model, workspace)
        module_timeout = float(os.environ.get("AG_MODULE_AGENT_TIMEOUT_SECONDS", "45"))
        mod_concurrency = int(os.environ.get("AG_REFRESH_CONCURRENCY", "8"))
        _mod_sem = asyncio.Semaphore(mod_concurrency)

        async def _run_module(entry: tuple) -> None:
            """Run a single module (single-agent or multi-sub-agent+merge)."""
            async with _mod_sem:
                if len(entry) == 2:
                    mod_name, mod_agent = entry
                    print(f"  → RefreshModule_{mod_name} (1 group, pre-loaded)...", file=sys.stderr)
                    try:
                        if module_timeout > 0:
                            await asyncio.wait_for(
                                Runner.run(
                                    mod_agent,
                                    "Analyze the pre-loaded source code and write your module knowledge document.",
                                    max_turns=5,
                                ),
                                timeout=module_timeout,
                            )
                        else:
                            await Runner.run(
                                mod_agent,
                                "Analyze the pre-loaded source code and write your module knowledge document.",
                                max_turns=5,
                            )
                    except Exception as exc:
                        print(f"  ⚠ RefreshModule_{mod_name} failed: {exc}", file=sys.stderr)
                    return

                # Multi sub-agents + merge
                mod_name, sub_agents, write_tools = entry
                print(
                    f"  → RefreshModule_{mod_name} ({len(sub_agents)} groups)...",
                    file=sys.stderr,
                )

                async def _run_sub(
                    gname: str, sagent: object,
                ) -> tuple[str, str | None]:
                    try:
                        if module_timeout > 0:
                            res = await asyncio.wait_for(
                                Runner.run(
                                    sagent,
                                    "Analyze the pre-loaded source code. Output your analysis as Markdown.",
                                    max_turns=3,
                                ),
                                timeout=module_timeout,
                            )
                        else:
                            res = await Runner.run(
                                sagent,
                                "Analyze the pre-loaded source code. Output your analysis as Markdown.",
                                max_turns=3,
                            )
                        print(f"    ✓ {mod_name}/{gname}", file=sys.stderr)
                        return gname, res.final_output
                    except Exception as exc:
                        print(f"    ⚠ {mod_name}/{gname} failed: {exc}", file=sys.stderr)
                        return gname, None

                sub_results = await asyncio.gather(
                    *[_run_sub(gn, sa) for gn, sa in sub_agents]
                )
                analyses: list[str] = [
                    f"## Group: {gn}\n\n{out}"
                    for gn, out in sub_results if out is not None
                ]

                if analyses:
                    print(f"    → merging {len(analyses)} analyses for {mod_name}...", file=sys.stderr)
                    try:
                        merge_agent = Agent(
                            name=f"RefreshModule_{mod_name}_merge",
                            instructions=_REFRESH_MERGE_INSTRUCTIONS.format(
                                module=mod_name,
                                analyses="\n\n---\n\n".join(analyses),
                            ) + "\n\nCall ``write_module_doc`` with the merged document.",
                            model=model,
                            tools=write_tools,
                        )
                        if module_timeout > 0:
                            await asyncio.wait_for(
                                Runner.run(merge_agent, "Merge and write.", max_turns=3),
                                timeout=module_timeout,
                            )
                        else:
                            await Runner.run(merge_agent, "Merge and write.", max_turns=3)
                        print(f"  ✓ RefreshModule_{mod_name} done", file=sys.stderr)
                    except Exception as exc:
                        print(f"    ⚠ merge {mod_name} failed: {exc}", file=sys.stderr)

        print(
            f"  ▶ Running {len(module_entries)} modules "
            f"(concurrency={mod_concurrency})...",
            file=sys.stderr,
        )
        await asyncio.gather(*[_run_module(e) for e in module_entries])

        print("  → RefreshGitAgent analyzing git history...", file=sys.stderr)
        try:
            git_agent = build_refresh_git_agent(model, workspace)
            if module_timeout > 0:
                await asyncio.wait_for(
                    Runner.run(
                        git_agent,
                        "Analyze the project's git history and write your git insights document.",
                        max_turns=25,
                    ),
                    timeout=module_timeout,
                )
            else:
                await Runner.run(
                    git_agent,
                    "Analyze the project's git history and write your git insights document.",
                    max_turns=25,
                )
        except Exception as exc:
            print(f"  ⚠ RefreshGitAgent failed: {exc}", file=sys.stderr)
    else:
        print("[7/8] Scan-only mode: module agents skipped.", file=sys.stderr)

    # -- Step 8: Generate module_registry.md via LLM --
    if not refresh_scan_only:
        print("[8/8] Generating module registry...", file=sys.stderr)
        try:
            registry_content = await _generate_module_registry(workspace, model)
            (ag_dir / "module_registry.md").write_text(registry_content, encoding="utf-8")
            print(f"  ✓ module_registry.md generated", file=sys.stderr)
        except Exception as exc:
            print(f"  ⚠ Module registry generation failed: {exc}", file=sys.stderr)
            # Fallback: build a basic registry from structure.md
            fallback = _build_fallback_registry(workspace)
            if fallback:
                (ag_dir / "module_registry.md").write_text(fallback, encoding="utf-8")
                print(f"  ✓ module_registry.md generated (fallback)", file=sys.stderr)
    else:
        print("[8/8] Scan-only mode: module registry skipped.", file=sys.stderr)

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
    if (ag_dir / "module_registry.md").exists():
        print(f"Updated {ag_dir / 'module_registry.md'}")
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


async def _generate_module_registry(workspace: Path, model: str) -> str:
    """Call LLM to generate a module registry from all available knowledge.

    Reads structure.md (always available) and modules/*.md (if generated),
    then asks the LLM to produce a concise 2-3 sentence description per module.

    Args:
        workspace: Project root directory.
        model: LLM model identifier.

    Returns:
        Markdown content for module_registry.md.
    """
    from antigravity_engine.hub.scanner import detect_modules

    ag_dir = workspace / ".antigravity"
    modules = detect_modules(workspace)

    # -- Collect per-module evidence --
    from antigravity_engine.hub.scanner import resolve_module_path

    # Read structure.md once
    structure = ""
    structure_file = ag_dir / "structure.md"
    if structure_file.is_file():
        try:
            structure = structure_file.read_text(encoding="utf-8")
        except OSError:
            pass

    module_evidence: list[str] = []
    for mod in modules:
        parts: list[str] = [f"### Module: {mod}"]

        # Source 1: module knowledge doc (best quality, from RefreshModuleAgent)
        mod_doc = ag_dir / "modules" / f"{mod}.md"
        if mod_doc.is_file():
            try:
                content = mod_doc.read_text(encoding="utf-8")
                # Take first 800 chars — usually contains purpose + key files
                parts.append(f"**Deep knowledge (excerpt):**\n{content[:800]}")
            except OSError:
                pass

        # Source 2: structure.md section (AST-extracted)
        # Use resolve_module_path for accurate directory matching
        mod_path = resolve_module_path(workspace, mod)
        rel_dir = str(mod_path.relative_to(workspace)) + "/"
        if structure:
            section = _extract_module_section(structure, mod, rel_dir)
            if section:
                parts.append(f"**Code structure:**\n{section[:1200]}")

        # Source 3: fallback — list actual files if structure.md had no section
        if len(parts) == 1:  # Only has the header, no evidence yet
            file_listing = _list_module_files(mod_path)
            if file_listing:
                parts.append(f"**Files in module:**\n{file_listing[:1200]}")

        module_evidence.append("\n".join(parts))

    # -- Build LLM prompt --
    evidence_text = "\n\n---\n\n".join(module_evidence)

    # Include conventions.md for overall context
    conventions = ""
    conv_file = ag_dir / "conventions.md"
    if conv_file.is_file():
        try:
            conventions = conv_file.read_text(encoding="utf-8")[:2000]
        except OSError:
            pass

    prompt = f"""\
You are a senior software architect. Based on the evidence below, write a
**Module Registry** — a concise reference that describes what each module
is responsible for.

For EACH module, write exactly:
- **Module name** (as given)
- **2-3 sentences** describing: what it does, what it owns, what other
  modules depend on it or it depends on.

The registry will be used by a Router agent to decide which module expert
to consult for a given question. So focus on **what questions each module
can answer** — not implementation details.

Output ONLY the Markdown registry. Start with `# Module Registry`. Use a
bullet list with bold module names.

---

## Project Overview
{conventions}

---

## Module Evidence

{evidence_text}
"""

    # -- Single LLM call --
    from agents import Agent, Runner

    registry_agent = Agent(
        name="RegistryWriter",
        instructions="Output only the requested Markdown. No commentary.",
        model=model,
    )

    registry_timeout = float(os.environ.get("AG_REGISTRY_TIMEOUT_SECONDS", "60"))
    if registry_timeout > 0:
        result = await asyncio.wait_for(
            Runner.run(registry_agent, prompt),
            timeout=registry_timeout,
        )
    else:
        result = await Runner.run(registry_agent, prompt)

    return result.final_output


def _extract_module_section(structure_text: str, module_id: str, rel_dir: str = "") -> str:
    """Extract lines from structure.md relevant to a module.

    Matches both ``## dir/`` section headers and ``### dir/file.py`` file
    entries whose path starts with the module's resolved directory.

    Args:
        structure_text: Full content of structure.md.
        module_id: Module identifier (e.g. "src_tools", "frontend").
        rel_dir: Resolved relative directory path (e.g. "src/opencmo/tools/").

    Returns:
        Extracted section text, or empty string.
    """
    # Build prefixes to match
    prefixes: list[str] = [f"{module_id}/"]
    if rel_dir:
        prefixes.append(rel_dir)
        prefixes.append(rel_dir.rstrip("/"))
    if "_" in module_id:
        parts = module_id.split("_", 1)
        prefixes.append(f"{parts[0]}/{parts[1]}/")

    def _line_matches(line: str) -> bool:
        # Match ## or ### headers that contain a matching path
        stripped = line.lstrip("#").strip()
        return any(stripped.startswith(p) or stripped.startswith(p.rstrip("/")) for p in prefixes)

    lines = structure_text.splitlines()
    result: list[str] = []
    collecting = False

    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if _line_matches(line):
                collecting = True
                result.append(line)
                continue
            elif collecting and line.startswith("## "):
                # New top-level section that doesn't match → stop
                if not _line_matches(line):
                    collecting = False
                    continue
        if collecting:
            result.append(line)

    return "\n".join(result[:80])  # Cap at 80 lines per module


def _list_module_files(mod_path: Path) -> str:
    """List Python/JS/TS files in a module directory for evidence.

    Args:
        mod_path: Absolute path to the module directory.

    Returns:
        Newline-separated list of relative file paths, or empty string.
    """
    if not mod_path.is_dir():
        return ""
    exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
    files: list[str] = []
    try:
        for f in sorted(mod_path.rglob("*")):
            if f.is_file() and f.suffix in exts and "__pycache__" not in str(f):
                files.append(f"- {f.relative_to(mod_path)}")
    except OSError:
        pass
    return "\n".join(files[:50])


def _build_fallback_registry(workspace: Path) -> str:
    """Build a basic module registry without LLM, from structure.md.

    Used when the LLM call fails. Extracts file listings per module
    and uses them as rough descriptions.

    Args:
        workspace: Project root directory.

    Returns:
        Markdown content for a fallback registry, or empty string.
    """
    from antigravity_engine.hub.scanner import detect_modules, resolve_module_path

    ag_dir = workspace / ".antigravity"
    modules = detect_modules(workspace)
    if not modules:
        return ""

    structure_file = ag_dir / "structure.md"
    structure = ""
    if structure_file.is_file():
        try:
            structure = structure_file.read_text(encoding="utf-8")
        except OSError:
            pass

    lines: list[str] = ["# Module Registry (auto-generated fallback)\n"]
    for mod in modules:
        rel_dir = str(resolve_module_path(workspace, mod).relative_to(workspace)) + "/"
        section = _extract_module_section(structure, mod, rel_dir) if structure else ""
        file_count = section.count("###")
        desc = f"Contains {file_count} files." if file_count else "No structure data available."
        lines.append(f"- **{mod}**: {desc}")

    return "\n".join(lines)


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
