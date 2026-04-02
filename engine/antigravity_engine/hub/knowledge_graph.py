"""Knowledge graph construction and rendering.

Extracted from ``scanner.py`` to reduce file size and improve
separation of concerns.  The scanner builds a :class:`ScanReport`;
this module transforms it into a knowledge graph.

Since v2 the graph includes **semantic edges** extracted from Python
AST: ``imports`` (file → module) and ``defines`` (file → symbol).
"""
from __future__ import annotations

import ast as _ast
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from antigravity_engine.hub._constants import SKIP_DIRS

if TYPE_CHECKING:
    from antigravity_engine.hub.scanner import ScanReport

# Maximum number of Python files to parse for semantic edges.
_MAX_SEMANTIC_FILES = 300


def build_knowledge_graph(root: Path, report: "ScanReport") -> dict[str, object]:
    """Build a project knowledge graph from scan metadata and AST analysis.

    In addition to the structural nodes (workspace, language, framework,
    directory, file), this now extracts **import relationships** and
    **symbol definitions** from Python files to create a semantic layer.

    Args:
        root: Project root directory.
        report: Completed scan report.

    Returns:
        JSON-serialisable graph dict with nodes, edges, and summary.
    """
    workspace_id = f"workspace:{root.resolve()}"
    nodes: list[dict[str, object]] = [
        {
            "id": workspace_id,
            "type": "workspace",
            "label": root.name or str(root),
        }
    ]
    edges: list[dict[str, str]] = []

    for lang, count in report.languages.items():
        lang_id = f"language:{lang.lower().replace(' ', '_')}"
        nodes.append({"id": lang_id, "type": "language", "label": lang, "count": count})
        edges.append({"from": workspace_id, "to": lang_id, "type": "uses_language"})

    for framework in report.frameworks:
        fw_id = f"framework:{framework.lower().replace(' ', '_').replace('/', '_')}"
        nodes.append({"id": fw_id, "type": "framework", "label": framework})
        edges.append({"from": workspace_id, "to": fw_id, "type": "uses_framework"})

    for directory in report.top_dirs:
        dir_id = f"dir:{directory}"
        nodes.append({"id": dir_id, "type": "directory", "label": directory})
        edges.append({"from": workspace_id, "to": dir_id, "type": "contains"})

    # File nodes (capped at 500)
    file_ids: set[str] = set()
    for rel, meta in list(report.file_metadata.items())[:500]:
        file_id = f"file:{rel}"
        file_ids.add(file_id)
        nodes.append(
            {
                "id": file_id,
                "type": str(meta.get("type", "file")),
                "label": rel,
                "size": int(meta.get("size", 0)),
                "mime": str(meta.get("mime", "unknown")),
            }
        )
        edges.append({"from": workspace_id, "to": file_id, "type": "contains"})

    # ── Semantic edges: Python imports and symbol definitions ──
    semantic = _extract_semantic_edges(root, file_ids)
    nodes.extend(semantic["nodes"])
    edges.extend(semantic["edges"])

    return {
        "schema": "antigravity-knowledge-graph-v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace": str(root.resolve()),
        "summary": {
            "file_count": report.file_count,
            "walked_file_count": report.walked_file_count,
            "languages": report.languages,
            "frameworks": report.frameworks,
            "type_distribution": report.type_distribution,
            "semantic_edges": len(semantic["edges"]),
        },
        "nodes": nodes,
        "edges": edges,
    }


def _extract_semantic_edges(
    root: Path,
    existing_file_ids: set[str],
) -> dict[str, list]:
    """Extract import and symbol-definition edges from Python files.

    Args:
        root: Project root directory.
        existing_file_ids: Set of ``file:…`` node IDs already in the graph.

    Returns:
        Dict with ``nodes`` and ``edges`` lists.
    """
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, str]] = []
    seen_modules: set[str] = set()
    seen_symbols: set[str] = set()
    file_count = 0
    skip = SKIP_DIRS | {"data", "logs"}

    for dirpath_str, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = Path(dirpath_str) / fname
            try:
                rel = fpath.relative_to(root).as_posix()
            except ValueError:
                continue

            file_id = f"file:{rel}"
            file_count += 1
            if file_count > _MAX_SEMANTIC_FILES:
                return {"nodes": nodes, "edges": edges}

            try:
                source = fpath.read_text(encoding="utf-8", errors="replace")
                tree = _ast.parse(source, filename=str(fpath))
            except (SyntaxError, OSError):
                continue

            for node in _ast.iter_child_nodes(tree):
                # Import edges
                if isinstance(node, _ast.ImportFrom) and node.module:
                    mod_id = f"module:{node.module}"
                    if mod_id not in seen_modules:
                        seen_modules.add(mod_id)
                        nodes.append({
                            "id": mod_id,
                            "type": "module",
                            "label": node.module,
                        })
                    edges.append({
                        "from": file_id,
                        "to": mod_id,
                        "type": "imports",
                    })
                elif isinstance(node, _ast.Import):
                    for alias in node.names:
                        mod_id = f"module:{alias.name}"
                        if mod_id not in seen_modules:
                            seen_modules.add(mod_id)
                            nodes.append({
                                "id": mod_id,
                                "type": "module",
                                "label": alias.name,
                            })
                        edges.append({
                            "from": file_id,
                            "to": mod_id,
                            "type": "imports",
                        })

                # Symbol definition edges
                if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    sym_id = f"symbol:{rel}:{node.name}"
                    if sym_id not in seen_symbols:
                        seen_symbols.add(sym_id)
                        nodes.append({
                            "id": sym_id,
                            "type": "function",
                            "label": node.name,
                            "lineno": node.lineno,
                        })
                    edges.append({
                        "from": file_id,
                        "to": sym_id,
                        "type": "defines",
                    })
                elif isinstance(node, _ast.ClassDef):
                    sym_id = f"symbol:{rel}:{node.name}"
                    if sym_id not in seen_symbols:
                        seen_symbols.add(sym_id)
                        bases = []
                        if hasattr(_ast, "unparse"):
                            bases = [_ast.unparse(b) for b in node.bases]
                        nodes.append({
                            "id": sym_id,
                            "type": "class",
                            "label": node.name,
                            "lineno": node.lineno,
                            "bases": bases,
                        })
                    edges.append({
                        "from": file_id,
                        "to": sym_id,
                        "type": "defines",
                    })

    return {"nodes": nodes, "edges": edges}


def render_knowledge_graph_markdown(graph: dict[str, object]) -> str:
    """Render a knowledge graph as Markdown for prompt/context use.

    Args:
        graph: Graph dict produced by :func:`build_knowledge_graph`.

    Returns:
        Markdown string.
    """
    summary = graph.get("summary", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    lines = [
        "# Knowledge Graph",
        "",
        f"- workspace: {graph.get('workspace', '')}",
        f"- created_at_utc: {graph.get('created_at_utc', '')}",
        f"- nodes: {len(nodes) if isinstance(nodes, list) else 0}",
        f"- edges: {len(edges) if isinstance(edges, list) else 0}",
        "",
        "## Summary",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
    ]

    if isinstance(nodes, list) and nodes:
        lines.extend(["", "## Sample Nodes"])
        for node in nodes[:20]:
            if not isinstance(node, dict):
                continue
            lines.append(
                f"- {node.get('type', 'node')}: {node.get('label', node.get('id', ''))}"
            )

    if isinstance(edges, list) and edges:
        lines.extend(["", "## Sample Edges"])
        for edge in edges[:20]:
            if not isinstance(edge, dict):
                continue
            lines.append(
                f"- {edge.get('from', '')} --{edge.get('type', 'rel')}--> {edge.get('to', '')}"
            )

    return "\n".join(lines) + "\n"


def render_knowledge_graph_mermaid(graph: dict[str, object]) -> str:
    """Render a knowledge graph as Mermaid syntax.

    Args:
        graph: Graph dict produced by :func:`build_knowledge_graph`.

    Returns:
        Mermaid graph definition string.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return 'graph TD\n  n_invalid["invalid graph"]\n'

    labels: dict[str, str] = {}
    for node in nodes[:200]:
        if isinstance(node, dict):
            labels[str(node.get("id", ""))] = str(node.get("label", node.get("id", ""))).replace('"', "'")

    def _mid(raw: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)
        return f"n_{safe}" if safe else "n_unknown"

    lines = ["graph TD"]
    for edge in edges[:200]:
        if not isinstance(edge, dict):
            continue
        src = str(edge.get("from", ""))
        dst = str(edge.get("to", ""))
        rel = str(edge.get("type", "rel"))
        if not src or not dst:
            continue
        src_label = labels.get(src, src)
        dst_label = labels.get(dst, dst)
        lines.append(
            f'  {_mid(src)}["{src_label}"] -->|{rel}| {_mid(dst)}["{dst_label}"]'
        )
    return "\n".join(lines) + "\n"
