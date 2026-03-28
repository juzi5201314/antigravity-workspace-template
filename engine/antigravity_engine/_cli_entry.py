"""CLI entry points for Antigravity Engine.

Provides:
- ag-ask "question"   → ask the multi-agent cluster
- ag-refresh          → refresh the knowledge base (module agents self-learn)
- ag-mcp              → MCP server (see hub/mcp_server.py)
"""
import os
import sys
from pathlib import Path


def ask_main() -> None:
    """Entry point for ``ag-ask``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ag-ask",
        description="Ask the Antigravity multi-agent cluster a question",
    )
    parser.add_argument("question", help="Natural language question about the project")
    parser.add_argument("--workspace", default=".", help="Project root (default: cwd)")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    os.environ["WORKSPACE_PATH"] = str(workspace)

    try:
        import asyncio
        from antigravity_engine.hub.pipeline import ask_pipeline

        print(asyncio.run(ask_pipeline(workspace, args.question)))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def refresh_main() -> None:
    """Entry point for ``ag-refresh``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ag-refresh",
        description="Refresh the Antigravity knowledge base",
    )
    parser.add_argument("--workspace", default=".", help="Project root (default: cwd)")
    parser.add_argument("--quick", action="store_true", help="Only scan changed files")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    os.environ["WORKSPACE_PATH"] = str(workspace)

    try:
        import asyncio
        from antigravity_engine.hub.pipeline import refresh_pipeline

        asyncio.run(refresh_pipeline(workspace, args.quick))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
