"""Code exploration tools for the Ask Swarm agents.

These tools let the ask-pipeline agents search, read, and inspect
the user's project at query time — turning ``ag ask`` from
"guess from metadata" into "answer with code evidence".

All tools are scoped to a *workspace* directory that is captured
via :func:`create_ask_tools`.  Path-traversal outside the workspace
is rejected.
"""
from __future__ import annotations

import functools
import fnmatch
import inspect
import json
import mimetypes
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

# Directories that should never be searched / listed.
_SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
    ".next",
    ".nuxt",
    "target",
    "vendor",
}

# Maximum search results returned by search_code.
_MAX_SEARCH_RESULTS = 50
# Maximum lines returned by read_file.
_MAX_READ_LINES = 200


def _env_int(name: str, default: int, *, minimum: int) -> int:
    """Read an integer env var with fallback and min guard."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _trim_file_to_last_lines(path: Path, max_lines: int) -> None:
    """Keep only the most recent N lines in a text file."""
    if max_lines <= 0 or not path.exists() or not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    if len(lines) <= max_lines:
        return
    trimmed = "\n".join(lines[-max_lines:]) + "\n"
    try:
        path.write_text(trimmed, encoding="utf-8")
    except OSError:
        return


def _prune_retrieval_artifacts(out_dir: Path, max_retrievals: int) -> None:
    """Keep only the latest retrieval graph artifact groups (.json/.md/.mmd)."""
    if max_retrievals <= 0 or not out_dir.exists() or not out_dir.is_dir():
        return

    json_files = sorted(out_dir.glob("*.json"))
    if len(json_files) <= max_retrievals:
        return

    stale = json_files[: len(json_files) - max_retrievals]
    for jf in stale:
        base = jf.with_suffix("")
        for suffix in (".json", ".md", ".mmd"):
            target = base.with_suffix(suffix)
            try:
                if target.exists():
                    target.unlink()
            except OSError:
                continue


def _jsonable(value: object) -> object:
    """Convert arbitrary Python values into JSON-serializable structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return repr(value)


def _render_retrieval_graph_markdown(graph: dict[str, object]) -> str:
    """Render retrieval graph as markdown while preserving full raw payload."""
    lines = [
        "# Retrieval Knowledge Graph",
        "",
        f"- schema: {graph.get('schema', 'unknown')}",
        f"- retrieval_id: {graph.get('retrieval_id', 'unknown')}",
        f"- tool_name: {graph.get('tool_name', 'unknown')}",
        f"- created_at_utc: {graph.get('created_at_utc', 'unknown')}",
        "",
        "## Raw Input (Lossless)",
        "```json",
        json.dumps(graph.get("raw_input", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Raw Output (Lossless)",
        "```text",
        str(graph.get("raw_output", "")),
        "```",
        "",
        "## Graph Data",
        "```json",
        json.dumps(
            {
                "nodes": graph.get("nodes", []),
                "edges": graph.get("edges", []),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
    ]
    return "\n".join(lines)


def _render_retrieval_graph_mermaid(graph: dict[str, object]) -> str:
    """Render retrieval graph as Mermaid syntax for visualization."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return "graph TD\n  A[invalid graph]"

    labels: dict[str, str] = {}
    for n in nodes:
        if isinstance(n, dict):
            nid = str(n.get("id", ""))
            lbl = str(n.get("label", nid)).replace('"', "'")
            if nid:
                labels[nid] = lbl

    lines = ["graph TD"]

    def _mid(raw: str) -> str:
        safe = re.sub(r"[^0-9A-Za-z_]", "_", raw)
        return f"n_{safe}"

    for e in edges:
        if not isinstance(e, dict):
            continue
        src = str(e.get("from", ""))
        dst = str(e.get("to", ""))
        etype = str(e.get("type", "rel"))
        if not src or not dst:
            continue
        lines.append(
            f"  {_mid(src)}[\"{labels.get(src, src)}\"] -->|{etype}| {_mid(dst)}[\"{labels.get(dst, dst)}\"]"
        )
    return "\n".join(lines)


def _record_retrieval_graph(
    workspace: Path,
    tool_name: str,
    raw_input: dict[str, object],
    raw_output: str,
) -> None:
    """Persist one lossless graph artifact per tool retrieval call."""
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    retrieval_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:8]}"

    project_id = "project:workspace"
    tool_id = f"tool:{tool_name}"
    output_id = f"output:{retrieval_id}"
    nodes: list[dict[str, str]] = [
        {
            "id": project_id,
            "type": "project",
            "label": workspace.name or str(workspace),
        },
        {
            "id": tool_id,
            "type": "tool",
            "label": tool_name,
        },
        {
            "id": output_id,
            "type": "output",
            "label": f"output_of_{tool_name}",
        },
    ]
    edges: list[dict[str, str]] = [
        {"from": project_id, "to": tool_id, "type": "invokes"},
        {"from": tool_id, "to": output_id, "type": "produces"},
    ]

    for key, value in raw_input.items():
        input_id = f"input:{retrieval_id}:{key}"
        nodes.append(
            {
                "id": input_id,
                "type": "input",
                "label": f"{key}={value!r}",
            }
        )
        edges.append({"from": tool_id, "to": input_id, "type": "uses_input"})

    graph = {
        "schema": "antigravity-retrieval-kg-v1",
        "retrieval_id": retrieval_id,
        "created_at_utc": created_at,
        "workspace": str(workspace),
        "tool_name": tool_name,
        # Lossless payload: exact call arguments and exact tool output string.
        "raw_input": _jsonable(raw_input),
        "raw_output": raw_output,
        "nodes": nodes,
        "edges": edges,
    }

    out_dir = workspace / ".antigravity" / "retrieval_graphs"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_tool = re.sub(r"[^0-9A-Za-z_-]", "_", tool_name)
    base = out_dir / f"{safe_tool}_{retrieval_id}"

    (base.with_suffix(".json")).write_text(
        json.dumps(graph, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (base.with_suffix(".md")).write_text(
        _render_retrieval_graph_markdown(graph),
        encoding="utf-8",
    )
    (base.with_suffix(".mmd")).write_text(
        _render_retrieval_graph_mermaid(graph),
        encoding="utf-8",
    )

    # Prevent unbounded growth of per-call graph artifacts on long-running projects.
    max_artifacts = _env_int("AG_RETRIEVAL_ARTIFACT_MAX_FILES", 300, minimum=1)
    _prune_retrieval_artifacts(out_dir, max_artifacts)

    _append_knowledge_graph_store(workspace, graph)


def _append_knowledge_graph_store(workspace: Path, graph: dict[str, object]) -> None:
    """Append retrieval graph nodes/edges into normalized graph store files.

    This is the persistent graph layer consumed by Graph Skill.
    """
    graph_dir = workspace / ".antigravity" / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)

    nodes_file = graph_dir / "nodes.jsonl"
    edges_file = graph_dir / "edges.jsonl"
    latest_file = graph_dir / "latest_graph_context.md"
    max_rows = _env_int("AG_GRAPH_STORE_MAX_ROWS", 3000, minimum=1)

    retrieval_id = str(graph.get("retrieval_id", ""))
    tool_name = str(graph.get("tool_name", "unknown"))
    raw_input = _jsonable(graph.get("raw_input", {}))
    raw_output = str(graph.get("raw_output", ""))

    nodes = graph.get("nodes", [])
    if isinstance(nodes, list):
        with nodes_file.open("a", encoding="utf-8") as fh:
            for n in nodes:
                if not isinstance(n, dict):
                    continue
                record = {
                    "schema": "antigravity-graph-node-v1",
                    "retrieval_id": retrieval_id,
                    "tool_name": tool_name,
                    "node": n,
                }
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _trim_file_to_last_lines(nodes_file, max_rows)

    edges = graph.get("edges", [])
    if isinstance(edges, list):
        with edges_file.open("a", encoding="utf-8") as fh:
            for e in edges:
                if not isinstance(e, dict):
                    continue
                record = {
                    "schema": "antigravity-graph-edge-v1",
                    "retrieval_id": retrieval_id,
                    "tool_name": tool_name,
                    "edge": e,
                }
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _trim_file_to_last_lines(edges_file, max_rows)

    # LLM-oriented latest context: concise summary + full-fidelity payload pointers.
    latest_lines = [
        "# Latest Graph Context",
        "",
        f"- retrieval_id: {retrieval_id}",
        f"- tool_name: {tool_name}",
        "",
        "## Raw Input",
        "```json",
        json.dumps(raw_input, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Raw Output",
        "```text",
        raw_output,
        "```",
        "",
        "## Graph Store Files",
        f"- {nodes_file}",
        f"- {edges_file}",
    ]
    latest_file.write_text("\n".join(latest_lines), encoding="utf-8")


def _wrap_retrieval_tools(workspace: Path, tools: dict[str, Callable]) -> dict[str, Callable]:
    """Wrap each tool so every call emits one lossless retrieval graph."""
    wrapped_tools: dict[str, Callable] = {}
    for tool_name, fn in tools.items():
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def _wrapped(*args, __fn=fn, __sig=sig, __tool_name=tool_name, **kwargs):
            bound = __sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            raw_input = {k: _jsonable(v) for k, v in bound.arguments.items()}
            try:
                result = __fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                _record_retrieval_graph(workspace, __tool_name, raw_input, f"ERROR: {exc}")
                raise

            raw_output = result if isinstance(result, str) else repr(result)
            _record_retrieval_graph(workspace, __tool_name, raw_input, raw_output)
            return result

        _wrapped.__signature__ = sig
        wrapped_tools[tool_name] = _wrapped
    return wrapped_tools


def _is_safe_path(workspace: Path, target: Path) -> bool:
    """Return True if *target* is inside *workspace* (no traversal)."""
    try:
        target.resolve().relative_to(workspace.resolve())
        return True
    except ValueError:
        return False


def _should_skip_dir(name: str) -> bool:
    """Return True if a directory name matches the skip list."""
    return name in _SKIP_DIRS or name.endswith(".egg-info")


def _is_gitnexus_available() -> bool:
    """Check if the ``gitnexus`` CLI is installed and reachable."""
    try:
        subprocess.run(
            ["gitnexus", "--version"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_gitnexus(workspace: Path, args: list[str], timeout: int = 30) -> str:
    """Run a gitnexus CLI command and return stdout.

    Args:
        workspace: Project root.
        args: CLI arguments after ``gitnexus``.
        timeout: Seconds before giving up.

    Returns:
        stdout text, or an error string.
    """
    try:
        result = subprocess.run(
            ["gitnexus", *args],
            capture_output=True,
            text=True,
            cwd=str(workspace),
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            err = result.stderr.strip() or "unknown error"
            return f"GitNexus error: {err}"
        return result.stdout.strip() or "(no output)"
    except FileNotFoundError:
        return "GitNexus is not installed."
    except subprocess.TimeoutExpired:
        return "GitNexus query timed out."


def _create_gitnexus_tools(workspace: Path) -> dict[str, Callable]:
    """Create GitNexus-powered tools if gitnexus is installed.

    These tools provide deep code intelligence: symbol search with
    semantic ranking, call-graph analysis, and impact/blast-radius
    analysis.  They complement the basic search_code/read_file tools.

    When gitnexus is not installed, returns an empty dict (zero cost).

    Args:
        workspace: Absolute path to the project root.

    Returns:
        Dict of tool-name to callable, empty if gitnexus unavailable.
    """
    if not _is_gitnexus_available():
        return {}

    ws = workspace.resolve()

    def gitnexus_query(query: str) -> str:
        """Search the project's code knowledge graph using hybrid search.

        This is more powerful than search_code for semantic queries like
        "authentication flow" or "database connection handling".  It uses
        BM25 + semantic ranking and returns symbols with context.

        Args:
            query: Natural-language or symbol-name query.

        Returns:
            Ranked search results with file paths, symbols, and context.
        """
        return _run_gitnexus(ws, ["query", query])

    def gitnexus_context(symbol: str) -> str:
        """Get a 360-degree view of a symbol: definition, callers, callees, and references.

        Use this to understand how a function, class, or variable fits
        into the broader codebase — who calls it, what it calls, and
        where it is referenced.

        Args:
            symbol: Fully-qualified or short symbol name (e.g. "login",
                "UserService", "auth.verify_token").

        Returns:
            Symbol definition, categorized references, and relationships.
        """
        return _run_gitnexus(ws, ["context", symbol])

    def gitnexus_impact(symbol: str) -> str:
        """Analyze the blast radius of changing a symbol.

        Use this to understand what would break or need updating if a
        function, class, or module were modified.  Returns affected
        files, dependent symbols, and confidence scores.

        Args:
            symbol: The symbol to analyze impact for.

        Returns:
            Impact analysis with affected files and confidence scores.
        """
        return _run_gitnexus(ws, ["impact", symbol])

    return {
        "gitnexus_query": gitnexus_query,
        "gitnexus_context": gitnexus_context,
        "gitnexus_impact": gitnexus_impact,
    }


# ---------------------------------------------------------------------------
# Tool factory — returns workspace-bound tool functions
# ---------------------------------------------------------------------------


def create_ask_tools(workspace: Path) -> dict[str, Callable]:
    """Create code-exploration tools bound to *workspace*.

    Returns a dict of ``{tool_name: callable}`` ready to be wrapped
    with the OpenAI Agent SDK ``function_tool`` decorator.

    Args:
        workspace: Absolute path to the user's project root.

    Returns:
        Dict mapping tool name to its implementation function.
    """
    ws = workspace.resolve()

    # ── search_code ───────────────────────────────────────────────

    def search_code(query: str, file_pattern: str = "*") -> str:
        """Search project source files for a text pattern.

        Use this tool to find where a function, class, variable, or
        concept appears in the codebase.  Results include file path,
        line number, and the matching line.

        Args:
            query: Text or regex pattern to search for.
            file_pattern: Glob pattern to filter files (e.g. "*.py",
                "*.ts").  Defaults to all files.

        Returns:
            Matching lines formatted as ``file:line: content``,
            up to 50 results.  Returns a message if nothing is found.
        """
        if not query:
            return "Error: query must not be empty."

        matches: list[str] = []
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            # Fall back to literal search if regex is invalid.
            pattern = re.compile(re.escape(query), re.IGNORECASE)

        for dirpath_str, dirnames, filenames in os.walk(ws):
            # Prune skip dirs in-place so os.walk doesn't descend.
            dirnames[:] = [
                d for d in dirnames if not _should_skip_dir(d)
            ]
            for fname in filenames:
                if file_pattern != "*" and not fnmatch.fnmatch(fname, file_pattern):
                    continue
                fpath = Path(dirpath_str) / fname
                try:
                    rel = fpath.relative_to(ws)
                except ValueError:
                    continue
                try:
                    text = fpath.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for lineno, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        matches.append(f"{rel}:{lineno}: {line.rstrip()}")
                        if len(matches) >= _MAX_SEARCH_RESULTS:
                            break
                if len(matches) >= _MAX_SEARCH_RESULTS:
                    break
            if len(matches) >= _MAX_SEARCH_RESULTS:
                break

        if not matches:
            return f"No results found for '{query}'."
        header = f"Found {len(matches)} result(s):\n"
        return header + "\n".join(matches)

    # ── read_file ─────────────────────────────────────────────────

    def read_file(file_path: str, start_line: int = 1, end_line: int = 100) -> str:
        """Read a file from the project, returning numbered lines.

        Use this to inspect the actual source code of a file after
        finding it with search_code or list_directory.

        Args:
            file_path: Relative path from the project root
                (e.g. "src/auth.py").
            start_line: First line to return (1-based, default 1).
            end_line: Last line to return (default 100, max 200 lines
                per call).

        Returns:
            Numbered source lines, or an error message.
        """
        target = (ws / file_path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{file_path}' is outside the project."
        if not target.is_file():
            return f"Error: '{file_path}' does not exist or is not a file."

        start_line = max(1, start_line)
        end_line = min(end_line, start_line + _MAX_READ_LINES - 1)

        try:
            all_lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return f"Error reading '{file_path}': {exc}"

        selected = all_lines[start_line - 1 : end_line]
        numbered = [
            f"{start_line + i:>5}  {line}"
            for i, line in enumerate(selected)
        ]
        header = f"--- {file_path} (lines {start_line}-{start_line + len(selected) - 1} of {len(all_lines)}) ---\n"
        return header + "\n".join(numbered)

    # ── list_directory ────────────────────────────────────────────

    def list_directory(path: str = ".") -> str:
        """List the contents of a project directory.

        Use this to understand the project structure — what modules,
        packages, and config files exist.

        Args:
            path: Relative directory path from the project root.
                Defaults to the project root.

        Returns:
            A formatted listing of files and subdirectories.
        """
        target = (ws / path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{path}' is outside the project."
        if not target.is_dir():
            return f"Error: '{path}' is not a directory."

        entries: list[str] = []
        try:
            for item in sorted(target.iterdir()):
                if _should_skip_dir(item.name):
                    continue
                if item.is_dir():
                    entries.append(f"  {item.name}/")
                else:
                    size = item.stat().st_size
                    entries.append(f"  {item.name}  ({size} bytes)")
        except OSError as exc:
            return f"Error listing '{path}': {exc}"

        if not entries:
            return f"Directory '{path}' is empty."
        header = f"Contents of {path}/:\n"
        return header + "\n".join(entries)

    # ── read_file_metadata ────────────────────────────────────────

    def read_file_metadata(file_path: str) -> str:
        """Read lightweight metadata for a file without loading full content.

        Args:
            file_path: Relative path from the project root.

        Returns:
            Size/mime/binary flags and file system times.
        """
        target = (ws / file_path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{file_path}' is outside the project."
        if not target.exists() or not target.is_file():
            return f"Error: '{file_path}' does not exist or is not a file."

        try:
            st = target.stat()
            mime, _ = mimetypes.guess_type(target.name)
            binary = False
            try:
                with target.open("rb") as fh:
                    binary = b"\x00" in fh.read(2048)
            except OSError:
                pass
        except OSError as exc:
            return f"Error reading metadata '{file_path}': {exc}"

        return (
            f"Metadata for {file_path}:\n"
            f"- size_bytes: {st.st_size}\n"
            f"- mime: {mime or 'unknown'}\n"
            f"- is_binary: {binary}\n"
            f"- modified_ts: {st.st_mtime:.0f}"
        )

    # ── search_by_type ────────────────────────────────────────────

    def search_by_type(file_type: str, limit: int = 50) -> str:
        """Find files by high-level type: code/documentation/data/media/binary.

        Args:
            file_type: Target file type.
            limit: Maximum number of paths returned (max 200).

        Returns:
            Matching relative paths.
        """
        category = file_type.strip().lower()
        if category not in {"code", "documentation", "data", "media", "binary"}:
            return "Error: file_type must be one of code/documentation/data/media/binary."

        limit = max(1, min(limit, 200))
        ext_map = {
            "documentation": {".md", ".rst", ".txt", ".adoc", ".pdf"},
            "data": {".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml", ".xml", ".sql", ".db", ".sqlite", ".parquet"},
            "media": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv"},
        }

        matches: list[str] = []
        for dirpath_str, dirnames, filenames in os.walk(ws):
            dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
            for fname in filenames:
                fpath = Path(dirpath_str) / fname
                try:
                    rel = fpath.relative_to(ws)
                except ValueError:
                    continue
                ext = fpath.suffix.lower()

                if category == "code":
                    hit = ext in {
                        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".cpp", ".c", ".swift", ".dart", ".lua", ".sh", ".html", ".css", ".scss", ".sql",
                    }
                elif category in ext_map:
                    hit = ext in ext_map[category]
                else:
                    # binary detection for uncategorized/binary request
                    try:
                        with fpath.open("rb") as fh:
                            hit = b"\x00" in fh.read(2048)
                    except OSError:
                        hit = False

                if hit:
                    matches.append(rel.as_posix())
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break

        if not matches:
            return f"No files found for type '{category}'."
        return f"Found {len(matches)} file(s) for type '{category}':\n" + "\n".join(matches)

    # ── summarize_directory ───────────────────────────────────────

    def summarize_directory(path: str = ".") -> str:
        """Summarize a directory by file counts and total size per extension."""
        target = (ws / path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{path}' is outside the project."
        if not target.is_dir():
            return f"Error: '{path}' is not a directory."

        counts: dict[str, int] = {}
        sizes: dict[str, int] = {}
        total_files = 0
        for dirpath_str, dirnames, filenames in os.walk(target):
            dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
            for fname in filenames:
                fpath = Path(dirpath_str) / fname
                ext = fpath.suffix.lower() or "(no-ext)"
                try:
                    sz = fpath.stat().st_size
                except OSError:
                    sz = 0
                counts[ext] = counts.get(ext, 0) + 1
                sizes[ext] = sizes.get(ext, 0) + sz
                total_files += 1

        lines = [f"Directory summary for {path}:", f"- total_files: {total_files}"]
        for ext, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:20]:
            lines.append(f"- {ext}: {c} file(s), {sizes.get(ext, 0)} bytes")
        return "\n".join(lines)

    # ── read_binary_stub ──────────────────────────────────────────

    def read_binary_stub(file_path: str, preview_bytes: int = 64) -> str:
        """Read a safe hex preview of a binary file.

        Args:
            file_path: Relative path from workspace.
            preview_bytes: Number of bytes to preview (max 256).
        """
        target = (ws / file_path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{file_path}' is outside the project."
        if not target.exists() or not target.is_file():
            return f"Error: '{file_path}' does not exist or is not a file."

        n = max(16, min(preview_bytes, 256))
        try:
            data = target.read_bytes()[:n]
        except OSError as exc:
            return f"Error reading '{file_path}': {exc}"

        hex_preview = data.hex(" ")
        return (
            f"Binary stub for {file_path}:\n"
            f"- preview_bytes: {len(data)}\n"
            f"- hex: {hex_preview}"
        )

    # ── git_file_history ──────────────────────────────────────────

    def git_file_history(file_path: str, limit: int = 10) -> str:
        """Show the recent git commit history for a specific file.

        Use this to understand when and why a file was changed.

        Args:
            file_path: Relative path from the project root.
            limit: Maximum number of commits to show (default 10).

        Returns:
            Recent commits touching this file, or a message if git
            is unavailable.
        """
        target = (ws / file_path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{file_path}' is outside the project."

        limit = min(limit, 20)
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"--max-count={limit}",
                    "--format=%h %ai %s",
                    "--",
                    file_path,
                ],
                capture_output=True,
                text=True,
                cwd=str(ws),
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return f"No git history found for '{file_path}'."
            return f"Git history for {file_path}:\n{result.stdout.strip()}"
        except FileNotFoundError:
            return "Git is not available."

    tools: dict[str, Callable] = {
        "search_code": search_code,
        "read_file": read_file,
        "list_directory": list_directory,
        "git_file_history": git_file_history,
        "read_file_metadata": read_file_metadata,
        "search_by_type": search_by_type,
        "summarize_directory": summarize_directory,
        "read_binary_stub": read_binary_stub,
    }

    # ── GitNexus tools (optional — only registered if gitnexus is installed) ──

    gitnexus_tools = _create_gitnexus_tools(ws)
    tools.update(gitnexus_tools)

    # Every retrieval call (including errors) emits a lossless graph artifact.
    return _wrap_retrieval_tools(ws, tools)


# ---------------------------------------------------------------------------
# Git tools — deeper git analysis for GitAgent
# ---------------------------------------------------------------------------


def create_git_tools(workspace: Path) -> dict[str, Callable]:
    """Create git-focused tools for the GitAgent.

    These tools provide deeper git analysis beyond simple file history,
    including log browsing, diff inspection, and blame analysis.

    Args:
        workspace: Absolute path to the user's project root.

    Returns:
        Dict mapping tool name to its implementation function.
    """
    ws = workspace.resolve()

    def git_log(limit: int = 20, path: str = "") -> str:
        """Show recent git commit history, optionally filtered by path.

        Args:
            limit: Maximum number of commits to show (default 20, max 50).
            path: Optional relative path to filter commits by
                (e.g. "engine/" for engine module only).

        Returns:
            Formatted commit history with hash, date, author, and message.
        """
        limit = min(max(1, limit), 50)
        cmd = [
            "git", "log",
            f"--max-count={limit}",
            "--format=%h %ai %an | %s",
        ]
        if path:
            target = (ws / path).resolve()
            if not _is_safe_path(ws, target):
                return f"Error: path '{path}' is outside the project."
            cmd.extend(["--", path])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(ws), check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return "No git history found."
            return f"Git log ({limit} commits):\n{result.stdout.strip()}"
        except FileNotFoundError:
            return "Git is not available."

    def git_diff(commit_hash: str) -> str:
        """Show the diff of a specific commit.

        Use this to understand what changed in a particular commit.

        Args:
            commit_hash: Short or full git commit hash.

        Returns:
            The diff output for the commit, truncated to 3000 chars.
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{commit_hash}~1", commit_hash, "--stat"],
                capture_output=True, text=True,
                cwd=str(ws), check=False,
            )
            stat = result.stdout.strip() if result.returncode == 0 else ""

            result = subprocess.run(
                ["git", "diff", f"{commit_hash}~1", commit_hash],
                capture_output=True, text=True,
                cwd=str(ws), check=False,
            )
            if result.returncode != 0:
                return f"Error: could not get diff for '{commit_hash}'."

            diff = result.stdout.strip()
            header = f"Diff for {commit_hash}:\n\n{stat}\n\n"
            if len(diff) > 3000:
                diff = diff[:3000] + "\n... (truncated)"
            return header + diff
        except FileNotFoundError:
            return "Git is not available."

    def git_blame(file_path: str, start_line: int = 1, end_line: int = 50) -> str:
        """Show git blame for a range of lines in a file.

        Use this to understand who wrote specific code and when.

        Args:
            file_path: Relative path from the project root.
            start_line: First line to blame (1-based, default 1).
            end_line: Last line to blame (default 50).

        Returns:
            Blame output with author, date, and line content.
        """
        target = (ws / file_path).resolve()
        if not _is_safe_path(ws, target):
            return f"Error: path '{file_path}' is outside the project."
        if not target.is_file():
            return f"Error: '{file_path}' does not exist."

        start_line = max(1, start_line)
        end_line = max(start_line, min(end_line, start_line + 100))

        try:
            result = subprocess.run(
                [
                    "git", "blame",
                    f"-L{start_line},{end_line}",
                    "--date=short",
                    "--", file_path,
                ],
                capture_output=True, text=True,
                cwd=str(ws), check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return f"No blame info for '{file_path}'."
            return f"Blame for {file_path} (lines {start_line}-{end_line}):\n{result.stdout.strip()}"
        except FileNotFoundError:
            return "Git is not available."

    tools = {
        "git_log": git_log,
        "git_diff": git_diff,
        "git_blame": git_blame,
    }

    return _wrap_retrieval_tools(ws, tools)


# ---------------------------------------------------------------------------
# Write tools — used by RefreshModuleAgents during refresh to persist docs
# ---------------------------------------------------------------------------


def create_write_tools(workspace: Path, module_name: str) -> dict[str, Callable]:
    """Create tools for a RefreshModuleAgent to write its knowledge doc.

    Args:
        workspace: Absolute path to the user's project root.
        module_name: Name of the module this agent is responsible for.

    Returns:
        Dict with a single ``write_module_doc`` tool.
    """
    ws = workspace.resolve()
    modules_dir = ws / ".antigravity" / "modules"

    def write_module_doc(content: str) -> str:
        """Write the module knowledge document.

        After reading and analyzing all the code in your module area,
        call this tool with a comprehensive Markdown document that
        captures your deep understanding of the module.

        The document should include:
        - Module purpose and responsibilities
        - Key files and what each one does
        - Important classes and functions with their roles
        - Internal data flow and call relationships
        - Dependencies on other modules
        - Design patterns used
        - Public API / interfaces exposed to other modules

        Args:
            content: Full Markdown content of the knowledge document.

        Returns:
            Confirmation message.
        """
        modules_dir.mkdir(parents=True, exist_ok=True)
        doc_path = modules_dir / f"{module_name}.md"
        doc_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {doc_path.relative_to(ws)}"

    return {
        "write_module_doc": write_module_doc,
    }


def create_git_write_tools(workspace: Path) -> dict[str, Callable]:
    """Create tools for the RefreshGitAgent to write its knowledge doc.

    Args:
        workspace: Absolute path to the user's project root.

    Returns:
        Dict with a single ``write_git_doc`` tool.
    """
    ws = workspace.resolve()
    modules_dir = ws / ".antigravity" / "modules"

    def write_git_doc(content: str) -> str:
        """Write the git insights knowledge document.

        After analyzing the project's git history, call this tool
        with a comprehensive Markdown document covering:
        - Recent development activity
        - Per-module change frequency
        - Key contributors
        - Notable recent changes and their impact
        - Development velocity and trends

        Args:
            content: Full Markdown content of the git knowledge document.

        Returns:
            Confirmation message.
        """
        modules_dir.mkdir(parents=True, exist_ok=True)
        doc_path = modules_dir / "_git_insights.md"
        doc_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {doc_path.relative_to(ws)}"

    return {
        "write_git_doc": write_git_doc,
    }

