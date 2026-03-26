"""Code exploration tools for the Ask Swarm agents.

These tools let the ask-pipeline agents search, read, and inspect
the user's project at query time — turning ``ag ask`` from
"guess from metadata" into "answer with code evidence".

All tools are scoped to a *workspace* directory that is captured
via :func:`create_ask_tools`.  Path-traversal outside the workspace
is rejected.
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from pathlib import Path
from typing import Callable

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

    return {
        "search_code": search_code,
        "read_file": read_file,
        "list_directory": list_directory,
        "git_file_history": git_file_history,
    }
