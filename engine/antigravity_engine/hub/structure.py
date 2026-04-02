"""Code structure extraction for the project skeleton map.

Extracted from ``scanner.py`` to reduce file size.  Produces the
Markdown content written to ``.antigravity/structure.md``.
"""
from __future__ import annotations

from pathlib import Path

from antigravity_engine.hub._constants import LANG_MAP


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

# Max total size of the generated structure text.
_STRUCTURE_LIMIT = 50_000
# Max summary lines per file.
_PER_FILE_LIMIT = 15


# ---------------------------------------------------------------------------
# Python structure extraction (via ast)
# ---------------------------------------------------------------------------

def _extract_python_structure(path: Path) -> list[str]:
    """Extract classes, functions, and imports from a Python file using ``ast``.

    Args:
        path: Absolute path to a ``.py`` file.

    Returns:
        List of summary lines (e.g. ``"class Foo(Base)"``).
    """
    import ast as _ast

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = _ast.parse(source, filename=str(path))
    except (SyntaxError, OSError):
        return []

    lines: list[str] = []

    # Module docstring
    ds = _ast.get_docstring(tree)
    if ds:
        first_line = ds.strip().splitlines()[0]
        lines.append(f'"{first_line}"')

    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, _ast.ClassDef):
            bases = ", ".join(
                _ast.unparse(b) if hasattr(_ast, "unparse") else "..."
                for b in node.bases
            )
            base_str = f"({bases})" if bases else ""
            doc = _ast.get_docstring(node)
            doc_str = f' — "{doc.splitlines()[0]}"' if doc else ""
            lines.append(f"  class {node.name}{base_str}{doc_str}")
        elif isinstance(node, _ast.FunctionDef) or isinstance(node, _ast.AsyncFunctionDef):
            args_list = []
            for arg in node.args.args:
                ann = ""
                if arg.annotation and hasattr(_ast, "unparse"):
                    ann = f": {_ast.unparse(arg.annotation)}"
                if arg.arg != "self":
                    args_list.append(f"{arg.arg}{ann}")
            ret = ""
            if node.returns and hasattr(_ast, "unparse"):
                ret = f" -> {_ast.unparse(node.returns)}"
            sig = ", ".join(args_list)
            doc = _ast.get_docstring(node)
            doc_str = f' — "{doc.splitlines()[0]}"' if doc else ""
            prefix = "async " if isinstance(node, _ast.AsyncFunctionDef) else ""
            lines.append(f"  {prefix}def {node.name}({sig}){ret}{doc_str}")
        elif isinstance(node, (_ast.Import, _ast.ImportFrom)):
            if isinstance(node, _ast.ImportFrom) and node.module:
                lines.append(f"  import: {node.module}")

    return lines[:_PER_FILE_LIMIT]


# ---------------------------------------------------------------------------
# Regex-based structure extraction (JS/TS/Go/Rust)
# ---------------------------------------------------------------------------

def _extract_regex_structure(path: Path, patterns: list[tuple[str, str]]) -> list[str]:
    """Extract top-level symbols from a source file using regex patterns.

    Args:
        path: Absolute path to a source file.
        patterns: List of ``(regex, label_prefix)`` tuples.

    Returns:
        List of summary lines.
    """
    import re as _re

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines: list[str] = []
    for pattern, prefix in patterns:
        for m in _re.finditer(pattern, source, _re.MULTILINE):
            lines.append(f"  {prefix}{m.group(1).strip()}")
            if len(lines) >= _PER_FILE_LIMIT:
                return lines
    return lines


# Language-specific regex patterns
_JS_TS_PATTERNS: list[tuple[str, str]] = [
    (r"^export\s+(?:default\s+)?(?:function|class|const|interface|type)\s+(\w+)", "export "),
    (r"^import\s+.+\s+from\s+['\"]([^'\"]+)['\"]", "import: "),
]

_GO_PATTERNS: list[tuple[str, str]] = [
    (r"^package\s+(\w+)", "package "),
    (r"^func\s+(\w+.*?)\s*\{", "func "),
    (r"^type\s+(\w+\s+(?:struct|interface))", "type "),
]

_RUST_PATTERNS: list[tuple[str, str]] = [
    (r"^pub\s+(fn\s+\w+.*?)\s*[{\(]", "pub "),
    (r"^pub\s+(struct\s+\w+)", "pub "),
    (r"^pub\s+(enum\s+\w+)", "pub "),
    (r"^pub\s+(trait\s+\w+)", "pub "),
    (r"^mod\s+(\w+)", "mod "),
]

# Map file extensions to their extraction strategy.
REGEX_LANG_MAP: dict[str, list[tuple[str, str]]] = {
    ".js": _JS_TS_PATTERNS,
    ".jsx": _JS_TS_PATTERNS,
    ".ts": _JS_TS_PATTERNS,
    ".tsx": _JS_TS_PATTERNS,
    ".go": _GO_PATTERNS,
    ".rs": _RUST_PATTERNS,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_structure(root: Path) -> str:
    """Generate a code skeleton map of the project.

    For Python files, uses ``ast`` for accurate extraction.
    For JS/TS/Go/Rust, uses regex heuristics (may be incomplete).
    Other languages get file name + line count only.

    The output is a Markdown-formatted string organized by directory,
    suitable for writing to ``.antigravity/structure.md``.

    Args:
        root: Project root directory.

    Returns:
        Markdown string describing the code structure.
    """
    from antigravity_engine.hub.scanner import _find_venv_dirs, _should_skip

    venv_dirs = _find_venv_dirs(root)
    sections: list[str] = []
    total_chars = 0

    # Collect all source files grouped by directory.
    dir_files: dict[str, list[Path]] = {}
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        try:
            rel = item.relative_to(root)
        except ValueError:
            continue
        if _should_skip(rel, venv_dirs):
            continue
        ext = item.suffix.lower()
        if ext not in LANG_MAP:
            continue
        parent = str(rel.parent) if str(rel.parent) != "." else "."
        dir_files.setdefault(parent, []).append(item)

    for dir_path in sorted(dir_files):
        dir_lines: list[str] = []
        display_dir = dir_path if dir_path != "." else "(root)"
        dir_lines.append(f"## {display_dir}/")

        for fpath in sorted(dir_files[dir_path]):
            rel = fpath.relative_to(root)
            ext = fpath.suffix.lower()
            file_lines: list[str] = []

            if ext == ".py":
                file_lines = _extract_python_structure(fpath)
            elif ext in REGEX_LANG_MAP:
                file_lines = _extract_regex_structure(fpath, REGEX_LANG_MAP[ext])

            if file_lines:
                dir_lines.append(f"### {rel}")
                dir_lines.extend(file_lines)
            else:
                # Fallback: just file name + line count
                try:
                    lc = len(fpath.read_text(encoding="utf-8", errors="replace").splitlines())
                except OSError:
                    lc = 0
                dir_lines.append(f"### {rel}  ({lc} lines)")

        section = "\n".join(dir_lines)
        if total_chars + len(section) > _STRUCTURE_LIMIT:
            sections.append(f"\n(truncated — {_STRUCTURE_LIMIT} char limit reached)")
            break
        sections.append(section)
        total_chars += len(section)

    header = "# Project Structure Map\n\nAuto-generated by `ag refresh`. Do not edit manually.\n"
    return header + "\n\n".join(sections)


def generate_module_context(root: Path, module_name: str) -> str:
    """Generate a detailed code structure document for a single module.

    Uses AST/regex extraction (same as extract_structure) but scoped
    to one module directory.  The result is intended to be the raw
    material that a RefreshModuleAgent will digest into a knowledge doc.

    Args:
        root: Project root directory.
        module_name: Name of the top-level module directory.

    Returns:
        Markdown string with the module's code skeleton.
    """
    from antigravity_engine.hub.scanner import _find_venv_dirs, _should_skip

    module_path = root / module_name
    if not module_path.is_dir():
        return f"# {module_name}\n\nModule directory not found."

    venv_dirs = _find_venv_dirs(root)
    sections: list[str] = [f"# Module: {module_name}\n"]

    dir_files: dict[str, list[Path]] = {}
    for item in sorted(module_path.rglob("*")):
        if not item.is_file():
            continue
        try:
            rel = item.relative_to(root)
        except ValueError:
            continue
        if _should_skip(rel, venv_dirs):
            continue
        ext = item.suffix.lower()
        if ext not in LANG_MAP:
            continue
        parent = str(rel.parent) if str(rel.parent) != "." else module_name
        dir_files.setdefault(parent, []).append(item)

    for dir_path in sorted(dir_files):
        dir_lines: list[str] = [f"## {dir_path}/"]
        for fpath in sorted(dir_files[dir_path]):
            rel = fpath.relative_to(root)
            ext = fpath.suffix.lower()
            file_lines: list[str] = []

            if ext == ".py":
                file_lines = _extract_python_structure(fpath)
            elif ext in REGEX_LANG_MAP:
                file_lines = _extract_regex_structure(fpath, REGEX_LANG_MAP[ext])

            if file_lines:
                dir_lines.append(f"### {rel}")
                dir_lines.extend(file_lines)
            else:
                try:
                    lc = len(fpath.read_text(encoding="utf-8", errors="replace").splitlines())
                except OSError:
                    lc = 0
                dir_lines.append(f"### {rel}  ({lc} lines)")

        sections.append("\n".join(dir_lines))

    return "\n\n".join(sections)
