"""Hub pipelines — refresh and ask."""
from __future__ import annotations

import asyncio
import ast
import json
import logging
import os
import re
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
    from antigravity_engine.hub.scanner import (
        build_knowledge_graph,
        extract_structure,
        full_scan,
        quick_scan,
        render_knowledge_graph_markdown,
        render_knowledge_graph_mermaid,
    )

    settings = Settings()
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

    # Write conventions
    (ag_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

    # Generate structure map (pure Python, no LLM)
    print("[4/7] Generating structure.md...", file=sys.stderr)
    structure_content = extract_structure(workspace)
    (ag_dir / "structure.md").write_text(structure_content, encoding="utf-8")

    # Build graph-first knowledge artifacts.
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

    # Derived indexes for non-code files.
    print("[6/7] Writing document/data/media indexes...", file=sys.stderr)
    doc_index, data_overview, media_manifest = _build_non_code_indexes(report)
    (ag_dir / "document_index.md").write_text(doc_index, encoding="utf-8")
    (ag_dir / "data_overview.md").write_text(data_overview, encoding="utf-8")
    (ag_dir / "media_manifest.md").write_text(media_manifest, encoding="utf-8")

    # Run RefreshModuleAgents — each agent reads its module and writes a knowledge doc
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

        # Run RefreshGitAgent
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

    # Save SHA checkpoint
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
    """Collect project context for Q&A with graph-first priority."""
    context_parts: list[str] = []
    # Keep context bounded to avoid prompt explosion.
    max_chars = int(os.environ.get("AG_ASK_CONTEXT_MAX_CHARS", "30000"))

    prioritized_sources = [
        (
            workspace / ".antigravity" / "knowledge_graph.md",
            ".antigravity/knowledge_graph.md",
        ),
        (
            workspace / ".antigravity" / "document_index.md",
            ".antigravity/document_index.md",
        ),
        (
            workspace / ".antigravity" / "data_overview.md",
            ".antigravity/data_overview.md",
        ),
        (
            workspace / ".antigravity" / "media_manifest.md",
            ".antigravity/media_manifest.md",
        ),
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

    for path, label in prioritized_sources:
        rendered = _read_context_file(path, label)
        if rendered:
            if sum(len(p) for p in context_parts) + len(rendered) > max_chars:
                break
            context_parts.append(rendered)

    memory_dir = workspace / ".antigravity" / "memory"
    if memory_dir.exists():
        for memory_file in sorted(memory_dir.glob("*.md")):
            rendered = _read_context_file(
                memory_file,
                f".antigravity/memory/{memory_file.name}",
            )
            if rendered:
                if sum(len(p) for p in context_parts) + len(rendered) > max_chars:
                    break
                context_parts.append(rendered)

    return "\n\n".join(context_parts) if context_parts else "(no context available)"


def _is_structure_query(question: str) -> bool:
    """Heuristic for topology/structure/dependency style questions."""
    q = question.lower()
    keywords = {
        "依赖", "关系", "调用", "结构", "拓扑", "子图", "知识图谱", "谁调用", "路径",
        "dependency", "dependencies", "relation", "relations", "calls", "called by",
        "graph", "topology", "structure", "ownership", "impact",
    }
    return any(k in q for k in keywords)


def _build_graph_skill_context(workspace: Path, question: str) -> str | None:
    """Invoke Graph Skill and convert output to prompt-ready context block."""
    from antigravity_engine.skills.loader import load_skills

    tools: dict = {}
    load_skills(tools)
    query_graph = tools.get("query_graph")
    if not callable(query_graph):
        return None

    try:
        result = query_graph(question, max_hops=2, workspace=str(workspace))
    except Exception:  # noqa: BLE001
        return None

    max_chars = int(os.environ.get("AG_GRAPH_CONTEXT_MAX_CHARS", "8000"))
    max_chars = max(1000, max_chars)

    if isinstance(result, dict):
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if len(payload) > max_chars:
            payload = payload[:max_chars] + "\n... [truncated by AG_GRAPH_CONTEXT_MAX_CHARS]"
        return "--- graph_skill_context ---\n" + payload
    return f"--- graph_skill_context ---\n{result}"


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

    retrieval_first = os.environ.get("AG_ASK_RETRIEVAL_FIRST", "1").strip().lower() in {"1", "true", "yes"}
    if retrieval_first:
        retrieval_answer = _build_retrieval_semantic_answer(workspace, question)
        if retrieval_answer:
            print("[2/3] Retrieval-first answer hit; skipping LLM.", file=sys.stderr)
            return retrieval_answer

    context = _build_ask_context(workspace)
    graph_skill_context = None
    if _is_structure_query(question):
        graph_skill_context = _build_graph_skill_context(workspace, question)

    prompt_parts = [f"Project context:\n{context}"]
    if graph_skill_context:
        prompt_parts.append(graph_skill_context)
    prompt_parts.append(f"Question: {question}")
    prompt = "\n\n".join(prompt_parts)

    mcp_tools: dict | None = None
    mcp_manager = None
    if settings.MCP_ENABLED:
        print("[…] Connecting to MCP servers...", file=sys.stderr)
        try:
            from antigravity_engine.mcp_client import MCPClientManager

            mcp_manager = MCPClientManager()
            await mcp_manager.initialize()
            mcp_tools = mcp_manager.get_all_tools_as_callables()
            if mcp_tools:
                logger.info("MCP tools loaded: %s", list(mcp_tools.keys()))
            else:
                logger.info("MCP enabled but no tools discovered")
        except Exception as exc:
            logger.warning("MCP initialization failed: %s", exc)
            print(f"  ⚠ MCP init failed: {exc}", file=sys.stderr)
            mcp_manager = None

    agent = build_reviewer_agent(model, workspace=workspace, mcp_tools=mcp_tools)
    try:
        from agents import Runner
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None

    print("[2/3] Analyzing with multi-agent swarm...", file=sys.stderr)

    ask_timeout = float(os.environ.get("AG_ASK_TIMEOUT_SECONDS", "45"))
    try:
        try:
            if ask_timeout > 0:
                result = await asyncio.wait_for(
                    Runner.run(agent, prompt, max_turns=12),
                    timeout=ask_timeout,
                )
            else:
                result = await Runner.run(agent, prompt, max_turns=12)
        finally:
            if mcp_manager is not None:
                try:
                    await mcp_manager.shutdown()
                except Exception as exc:
                    logger.warning("MCP shutdown error: %s", exc)
    except TimeoutError:
        return _build_timeout_fallback_answer(workspace, question)

    print("[3/3] Synthesizing answer...", file=sys.stderr)

    return result.final_output


def _iter_python_files(workspace: Path) -> list[Path]:
    """Collect python files under workspace with lightweight skip rules."""
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".nuxt",
        "target", "vendor", "data", "logs",
    }
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".py"):
                files.append(Path(dirpath) / fname)
    return files


def _iter_shell_files(workspace: Path) -> list[Path]:
    """Collect shell script files under workspace with lightweight skip rules."""
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".nuxt",
        "target", "vendor", "data", "logs",
    }
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for fname in filenames:
            p = Path(dirpath) / fname
            if fname.endswith(".sh"):
                files.append(p)
                continue
            if fname in {"Dockerfile", "Makefile"}:
                continue
            try:
                if p.is_file() and p.read_text(encoding="utf-8", errors="ignore").startswith("#!/usr/bin/env bash"):
                    files.append(p)
            except Exception:
                continue
    return files


def _extract_identifiers(question: str) -> list[str]:
    """Extract candidate symbol identifiers from user question."""
    ids = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", question)
    # Keep order and unique
    seen: set[str] = set()
    out: list[str] = []
    for item in ids:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _find_function_defs(workspace: Path, identifiers: list[str]) -> list[dict[str, object]]:
    """Find function definitions matching identifiers."""
    targets = {x.lower() for x in identifiers}
    matches: list[dict[str, object]] = []
    for fpath in _iter_python_files(workspace):
        try:
            source = fpath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
            lines = source.splitlines()
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if targets and name.lower() not in targets:
                    continue
                start = int(getattr(node, "lineno", 1))
                end = int(getattr(node, "end_lineno", start))
                snippet = "\n".join(lines[start - 1 : min(end, start + 20)])
                matches.append(
                    {
                        "name": name,
                        "file": str(fpath.relative_to(workspace)),
                        "start": start,
                        "end": end,
                        "snippet": snippet,
                    }
                )
    return matches[:6]


def _find_call_sites(workspace: Path, func_name: str, limit: int = 12) -> list[str]:
    """Find call sites for a function name."""
    pattern = re.compile(rf"\b{re.escape(func_name)}\s*\(")
    calls: list[str] = []
    for fpath in _iter_python_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if pattern.search(line) and not line.lstrip().startswith("def "):
                calls.append(f"{rel}:{i}: {line.strip()}")
                if len(calls) >= limit:
                    return calls
    return calls


def _find_shell_function_defs(workspace: Path, identifiers: list[str]) -> list[dict[str, object]]:
    """Find shell function definitions matching identifiers."""
    targets = {x.lower() for x in identifiers}
    matches: list[dict[str, object]] = []
    # Matches forms: foo() { ... } and function foo() { ... }
    def_pattern = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{")

    for fpath in _iter_shell_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        i = 0
        while i < len(lines):
            line = lines[i]
            m = def_pattern.match(line)
            if not m:
                i += 1
                continue

            name = m.group(1)
            if targets and name.lower() not in targets:
                i += 1
                continue

            start = i + 1
            brace_balance = line.count("{") - line.count("}")
            j = i + 1
            while j < len(lines) and brace_balance > 0:
                brace_balance += lines[j].count("{") - lines[j].count("}")
                j += 1
            end = j if j > start else start
            snippet = "\n".join(lines[start - 1 : min(end, start + 25)])
            matches.append(
                {
                    "name": name,
                    "file": str(rel),
                    "start": start,
                    "end": end,
                    "snippet": snippet,
                }
            )
            i = j
            if len(matches) >= 6:
                return matches
    return matches


def _find_shell_call_sites(workspace: Path, func_name: str, limit: int = 12) -> list[str]:
    """Find shell call sites for a function name."""
    call_pattern = re.compile(rf"\b{re.escape(func_name)}\b")
    def_pattern = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{")
    calls: list[str] = []
    for fpath in _iter_shell_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if not call_pattern.search(line):
                continue
            if def_pattern.match(line):
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            calls.append(f"{rel}:{i}: {stripped}")
            if len(calls) >= limit:
                return calls
    return calls


def _extract_blueprints_from_app(workspace: Path) -> list[str]:
    """Extract blueprint modules from backend app factory registration."""
    app_path = workspace / "backend" / "app.py"
    if not app_path.is_file():
        return []
    try:
        text = app_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    mods = re.findall(r'"backend\.blueprints\.([a-zA-Z0-9_]+)"', text)
    return mods


def _build_retrieval_semantic_answer(workspace: Path, question: str) -> str | None:
    """Build a semantic answer from retrieval artifacts and code evidence.

    This path avoids LLM calls when possible, preserving responsiveness.
    """
    q = question.strip()
    if not q:
        return None

    lines: list[str] = []
    scan_report = workspace / ".antigravity" / "scan_report.json"
    if scan_report.is_file():
        try:
            payload = json.loads(scan_report.read_text(encoding="utf-8"))
            lines.append(
                "[retrieval] "
                f"files={payload.get('file_count', 0)}, "
                f"elapsed={payload.get('scan_elapsed_seconds', 0.0)}s"
            )
        except Exception:
            pass

    # Architecture / module registration question shortcut.
    if ("blueprint" in q.lower()) or ("模块" in q and "注册" in q):
        bps = _extract_blueprints_from_app(workspace)
        if bps:
            lines.append("后端注册的 blueprint 模块:")
            lines.extend([f"- {m}" for m in bps])
            lines.append("证据: backend/app.py")
            return "\n".join(lines)

    identifiers = _extract_identifiers(q)
    if not identifiers and ("函数" not in q and "调用" not in q and "function" not in q.lower()):
        return None

    py_defs = _find_function_defs(workspace, identifiers)
    sh_defs = _find_shell_function_defs(workspace, identifiers)
    if not py_defs and not sh_defs:
        return None

    lines.append("基于检索到的函数实现与调用关系:")
    for item in py_defs[:3]:
        name = str(item["name"])
        file = str(item["file"])
        start = int(item["start"])
        lines.append(f"- 函数 {name} 定义于 {file}:{start}")
        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            lines.append("```python")
            lines.append(snippet)
            lines.append("```")
        calls = _find_call_sites(workspace, name, limit=8)
        if calls:
            lines.append("  相关调用:")
            lines.extend([f"  - {c}" for c in calls])

    for item in sh_defs[:3]:
        name = str(item["name"])
        file = str(item["file"])
        start = int(item["start"])
        lines.append(f"- Shell 函数 {name} 定义于 {file}:{start}")
        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            lines.append("```bash")
            lines.append(snippet)
            lines.append("```")
        calls = _find_shell_call_sites(workspace, name, limit=8)
        if calls:
            lines.append("  相关调用:")
            lines.extend([f"  - {c}" for c in calls])

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


def _build_timeout_fallback_answer(workspace: Path, question: str) -> str:
    """Return deterministic retrieval output when ask agent times out."""
    ag_dir = workspace / ".antigravity"
    scan_report = ag_dir / "scan_report.json"
    structure = ag_dir / "structure.md"

    lines: list[str] = [
        "LLM answering timed out, but retrieval results are available:",
        f"- Question: {question}",
    ]

    if scan_report.exists():
        try:
            payload = json.loads(scan_report.read_text(encoding="utf-8"))
            summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
            file_count = 0
            scan_elapsed = 0.0
            timed_out = False
            if isinstance(summary, dict) and summary:
                file_count = int(summary.get("file_count", 0))
                scan_elapsed = float(summary.get("scan_elapsed_seconds", 0.0))
                timed_out = bool(summary.get("timed_out", False))
            elif isinstance(payload, dict):
                file_count = int(payload.get("file_count", 0))
                scan_elapsed = float(payload.get("scan_elapsed_seconds", 0.0))
                timed_out = bool(payload.get("timed_out", False))
            samples = payload.get("scanned_file_samples", []) if isinstance(payload, dict) else []
            lines.append(f"- Scan files: {file_count}")
            lines.append(f"- Scan elapsed: {scan_elapsed}s")
            lines.append(f"- Timed out: {timed_out}")
            if isinstance(samples, list) and samples:
                lines.append("- Retrieved file samples:")
                lines.extend([f"  - {p}" for p in samples[:20]])
        except Exception:
            lines.append(f"- Retrieval artifact exists: {scan_report}")
    else:
        lines.append("- scan_report.json not found; run ag-refresh first.")

    if structure.exists():
        lines.append(f"- Structure file: {structure}")

    return "\n".join(lines)


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
    lines.append(f"Binary files: {getattr(report, 'binary_files', 0)}")

    if report.readme_snippet:
        lines.append(f"\nREADME excerpt:\n{report.readme_snippet}")

    samples = getattr(report, "scanned_file_samples", [])
    if samples:
        lines.append("\nScanned file samples:")
        for rel in samples[:30]:
            lines.append(f"  - {rel}")

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
