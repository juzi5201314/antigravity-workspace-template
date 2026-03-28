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
import functools
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


@functools.lru_cache(maxsize=1)
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
    }

    # ── GitNexus tools (optional — only registered if gitnexus is installed) ──

    gitnexus_tools = _create_gitnexus_tools(ws)
    tools.update(gitnexus_tools)

    return tools


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

    return {
        "git_log": git_log,
        "git_diff": git_diff,
        "git_blame": git_blame,
    }


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

