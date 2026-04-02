"""Knowledge graph construction and rendering.

Extracted from ``scanner.py`` to reduce file size and improve
separation of concerns.  The scanner builds a :class:`ScanReport`;
this module transforms it into a knowledge graph.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from antigravity_engine.hub.scanner import ScanReport


def build_knowledge_graph(root: Path, report: "ScanReport") -> dict[str, object]:
    """Build a lightweight project knowledge graph from scan metadata.

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

    for rel, meta in list(report.file_metadata.items())[:500]:
        file_id = f"file:{rel}"
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

    return {
        "schema": "antigravity-knowledge-graph-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace": str(root.resolve()),
        "summary": {
            "file_count": report.file_count,
            "walked_file_count": report.walked_file_count,
            "languages": report.languages,
            "frameworks": report.frameworks,
            "type_distribution": report.type_distribution,
        },
        "nodes": nodes,
        "edges": edges,
    }


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
