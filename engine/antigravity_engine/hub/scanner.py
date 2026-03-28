"""Project scanner — pure Python, no LLM dependency."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Maximum lines to read from a single config file.
_CONFIG_LINE_LIMIT = 200
# Maximum total bytes across all config file contents.
_CONFIG_TOTAL_LIMIT = 30_000
# Maximum lines to read from an entry-point file.
_ENTRY_POINT_LINE_LIMIT = 50


# File extensions → language names
_LANG_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".jsx": "JavaScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".dart": "Dart",
    ".lua": "Lua",
    ".sh": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".json": "JSON",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
}

# Marker files → framework/tool names
_FRAMEWORK_MARKERS: dict[str, str] = {
    "pyproject.toml": "Python (pyproject.toml)",
    "setup.py": "Python (setup.py)",
    "requirements.txt": "Python (requirements.txt)",
    "package.json": "Node.js",
    "Cargo.toml": "Rust (Cargo)",
    "go.mod": "Go Modules",
    "Gemfile": "Ruby (Bundler)",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "composer.json": "PHP (Composer)",
    "pubspec.yaml": "Dart/Flutter",
    "Makefile": "Make",
    "CMakeLists.txt": "CMake",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github/workflows": "GitHub Actions",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    "tsconfig.json": "TypeScript",
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "vite.config.ts": "Vite",
    "webpack.config.js": "Webpack",
    "tailwind.config.js": "Tailwind CSS",
    ".eslintrc.js": "ESLint",
    ".prettierrc": "Prettier",
    "pytest.ini": "Pytest",
    "setup.cfg": "Python (setup.cfg)",
    "tox.ini": "Tox",
}

# Directories to skip during scanning
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
    "*.egg-info",
    ".next",
    ".nuxt",
    "target",
    "vendor",
}


@dataclass
class ScanReport:
    """Result of scanning a project directory."""

    root: Path
    languages: dict[str, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    top_dirs: list[str] = field(default_factory=list)
    file_count: int = 0
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    has_pytest: bool = False
    readme_snippet: str = ""
    config_contents: dict[str, str] = field(default_factory=dict)
    entry_points: dict[str, str] = field(default_factory=dict)
    git_summary: str = ""


def _is_venv_dir(path: Path) -> bool:
    """Detect virtual environments by the presence of ``pyvenv.cfg``.

    Args:
        path: Directory to check.

    Returns:
        True if the directory looks like a Python virtual environment.
    """
    return (path / "pyvenv.cfg").is_file()


def _find_venv_dirs(root: Path) -> set[str]:
    """Discover virtualenv directory names under *root* (up to two levels deep).

    Args:
        root: Project root directory.

    Returns:
        Set of directory names that are virtual environments.
    """
    venv_names: set[str] = set()
    try:
        entries = list(root.iterdir())
    except OSError:
        return venv_names
    for d in entries:
        if d.is_dir():
            if _is_venv_dir(d):
                venv_names.add(d.name)
            # Also check one level deep (e.g. engine/venv)
            if not d.name.startswith(".") and d.name not in _SKIP_DIRS:
                try:
                    for sub in d.iterdir():
                        if sub.is_dir() and _is_venv_dir(sub):
                            venv_names.add(sub.name)
                except OSError:
                    pass
    return venv_names


def _should_skip(path: Path, extra_skip: set[str] | None = None) -> bool:
    """Check if a relative path should be skipped during scanning.

    Args:
        path: Relative path (from root) to evaluate.
        extra_skip: Additional directory names to skip (e.g. detected venvs).

    Returns:
        True if the path falls inside a skippable directory.
    """
    skip = _SKIP_DIRS | extra_skip if extra_skip else _SKIP_DIRS
    for part in path.parts:
        if part in skip or part.endswith(".egg-info"):
            return True
    return False


# Config files worth reading — relative paths (or glob patterns handled specially).
_CONFIG_FILES: list[str] = [
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    "tsconfig.json",
    ".env.example",
    ".gitlab-ci.yml",
    "Makefile",
]

# Common entry-point file names to look for when config doesn't specify one.
_COMMON_ENTRY_FILES: list[str] = [
    "main.py",
    "app.py",
    "manage.py",
    "index.ts",
    "index.js",
    "src/index.ts",
    "src/index.js",
    "src/main.ts",
    "src/main.py",
    "main.go",
    "cmd/main.go",
    "src/main.rs",
    "src/lib.rs",
]


def _read_file_head(path: Path, max_lines: int) -> str | None:
    """Read the first *max_lines* of a text file.

    Args:
        path: File to read.
        max_lines: Maximum number of lines to return.

    Returns:
        The truncated content, or None if the file cannot be read.
    """
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:max_lines]
        return "\n".join(lines)
    except OSError:
        return None


def _read_config_files(root: Path) -> dict[str, str]:
    """Read well-known config files from the project root.

    Args:
        root: Project root directory.

    Returns:
        Mapping of relative file path to its (possibly truncated) content.
    """
    contents: dict[str, str] = {}
    total_bytes = 0

    # Fixed-name config files
    for name in _CONFIG_FILES:
        path = root / name
        if not path.is_file():
            continue
        text = _read_file_head(path, _CONFIG_LINE_LIMIT)
        if text is None:
            continue
        if total_bytes + len(text) > _CONFIG_TOTAL_LIMIT:
            break
        contents[name] = text
        total_bytes += len(text)

    # CI workflow YAML files (may be multiple)
    workflows_dir = root / ".github" / "workflows"
    if workflows_dir.is_dir():
        try:
            for wf in sorted(workflows_dir.glob("*.yml")):
                rel = f".github/workflows/{wf.name}"
                text = _read_file_head(wf, _CONFIG_LINE_LIMIT)
                if text is None:
                    continue
                if total_bytes + len(text) > _CONFIG_TOTAL_LIMIT:
                    break
                contents[rel] = text
                total_bytes += len(text)
        except OSError:
            pass

    return contents


def _read_entry_points(root: Path, config_contents: dict[str, str]) -> dict[str, str]:
    """Detect and read project entry-point files.

    Checks pyproject.toml ``[project.scripts]`` and package.json ``"main"``,
    then falls back to common entry-point filenames.

    Args:
        root: Project root directory.
        config_contents: Already-read config file contents (avoids re-reading).

    Returns:
        Mapping of relative file path to its first N lines.
    """
    candidates: list[str] = []

    # --- pyproject.toml: [project.scripts] ---
    pyproject_text = config_contents.get("pyproject.toml", "")
    if pyproject_text:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:
            tomllib = None  # type: ignore[assignment]
        if tomllib is not None:
            try:
                data = tomllib.loads(pyproject_text)
                scripts = data.get("project", {}).get("scripts", {})
                for _cmd, ref in scripts.items():
                    # ref looks like "ag_cli.cli:app" → module is ag_cli/cli.py
                    mod = ref.split(":")[0].replace(".", "/") + ".py"
                    candidates.append(mod)
            except Exception:
                pass

    # --- package.json: "main" ---
    pkg_text = config_contents.get("package.json", "")
    if pkg_text:
        try:
            data = json.loads(pkg_text)
            main = data.get("main")
            if main:
                candidates.append(main)
        except Exception:
            pass

    # --- Fallback: common filenames ---
    candidates.extend(_COMMON_ENTRY_FILES)

    entry_points: dict[str, str] = {}
    for rel in candidates:
        path = root / rel
        if not path.is_file():
            continue
        if rel in entry_points:
            continue
        text = _read_file_head(path, _ENTRY_POINT_LINE_LIMIT)
        if text is not None:
            entry_points[rel] = text
        if len(entry_points) >= 5:
            break

    return entry_points


def _extract_git_summary(root: Path) -> str:
    """Extract recent git history as a plain-text summary.

    Args:
        root: Project root directory.

    Returns:
        Multi-line string with recent commits and contributor activity,
        or an empty string if git is unavailable.
    """
    parts: list[str] = []

    # Recent commits
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("Recent commits:\n" + result.stdout.strip())
    except FileNotFoundError:
        return ""

    # Contributor activity (last 3 months)
    try:
        result = subprocess.run(
            ["git", "shortlog", "-sn", "--since=3 months ago"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("Contributors (last 3 months):\n" + result.stdout.strip())
    except FileNotFoundError:
        pass

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Structure extraction — code skeleton for Router's area map
# ---------------------------------------------------------------------------

# Max total size of the generated structure text.
_STRUCTURE_LIMIT = 50_000
# Max summary lines per file.
_PER_FILE_LIMIT = 15


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


# Regex patterns for non-Python languages: (regex, display_prefix)
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
_REGEX_LANG_MAP: dict[str, list[tuple[str, str]]] = {
    ".js": _JS_TS_PATTERNS,
    ".jsx": _JS_TS_PATTERNS,
    ".ts": _JS_TS_PATTERNS,
    ".tsx": _JS_TS_PATTERNS,
    ".go": _GO_PATTERNS,
    ".rs": _RUST_PATTERNS,
}


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
        if ext not in _LANG_MAP:
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
            elif ext in _REGEX_LANG_MAP:
                file_lines = _extract_regex_structure(fpath, _REGEX_LANG_MAP[ext])

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


def full_scan(root: Path) -> ScanReport:
    """Perform a full project scan.

    Args:
        root: Project root directory.

    Returns:
        ScanReport with project analysis.
    """
    report = ScanReport(root=root)
    lang_counts: dict[str, int] = {}

    # Detect venv directories by content (catches custom-named venvs)
    venv_dirs = _find_venv_dirs(root)
    skip_dirs = _SKIP_DIRS | venv_dirs

    # Detect frameworks from marker files
    for marker, name in _FRAMEWORK_MARKERS.items():
        if (root / marker).exists():
            report.frameworks.append(name)

    # Scan files
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        try:
            rel = item.relative_to(root)
        except ValueError:
            continue
        if _should_skip(rel, venv_dirs):
            continue

        report.file_count += 1
        ext = item.suffix.lower()
        if ext in _LANG_MAP:
            lang = _LANG_MAP[ext]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Sort languages by count
    report.languages = dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True))

    # Top-level directories (filter out hidden, skip dirs, egg-info, venvs)
    report.top_dirs = sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir()
        and not d.name.startswith(".")
        and d.name not in skip_dirs
        and not d.name.endswith(".egg-info")
    )

    # Detect tests (recursive — catches engine/tests, src/test, etc.)
    test_dir_names = {"tests", "test", "spec", "specs", "__tests__"}
    report.has_tests = any(
        d.is_dir() and d.name in test_dir_names
        for d in root.rglob("*")
        if d.is_dir()
        and not _should_skip(d.relative_to(root), venv_dirs)
    )

    # Detect pytest configuration
    report.has_pytest = any(
        (root / f).exists() for f in ("pytest.ini", "conftest.py")
    ) or any(
        d.is_file() and d.name in ("conftest.py", "pytest.ini")
        for d in root.rglob("*")
        if d.is_file()
        and not _should_skip(d.relative_to(root), venv_dirs)
        and d.name in ("conftest.py", "pytest.ini")
    )

    # CI and Docker detection
    report.has_ci = (root / ".github" / "workflows").exists() or (root / ".gitlab-ci.yml").exists()
    report.has_docker = (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists()

    # Read first few lines of README
    for name in ("README.md", "readme.md", "README.rst", "README"):
        readme = root / name
        if readme.exists():
            try:
                lines = readme.read_text(encoding="utf-8").splitlines()[:10]
                report.readme_snippet = "\n".join(lines)
            except OSError:
                pass
            break

    # --- Phase 1 enhancements: config files, entry points, git history ---
    report.config_contents = _read_config_files(root)
    report.entry_points = _read_entry_points(root, report.config_contents)
    report.git_summary = _extract_git_summary(root)

    return report


def detect_modules(root: Path) -> list[str]:
    """Detect top-level code modules in a project.

    A module is a top-level directory that contains source code files.
    Hidden directories, virtual environments, and common non-code
    directories are excluded.

    Args:
        root: Project root directory.

    Returns:
        List of module names (e.g. ["engine", "cli", "docs"]).
    """
    skip = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
        ".next", ".nuxt", "target", "vendor", ".antigravity", ".context",
        "artifacts", ".github", ".agent", ".agents",
    }
    venv_dirs = _find_venv_dirs(root)
    skip = skip | venv_dirs

    modules: list[str] = []
    try:
        for item in sorted(root.iterdir()):
            if not item.is_dir():
                continue
            if item.name.startswith(".") or item.name in skip:
                continue
            if item.name.endswith(".egg-info"):
                continue
            # Only count directories that contain at least one source file
            has_source = any(
                f.is_file() and f.suffix.lower() in _LANG_MAP
                for f in item.rglob("*")
                if f.is_file()
                and not _should_skip(f.relative_to(root), venv_dirs)
            )
            if has_source:
                modules.append(item.name)
    except OSError:
        pass

    return modules


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
        if ext not in _LANG_MAP:
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
            elif ext in _REGEX_LANG_MAP:
                file_lines = _extract_regex_structure(fpath, _REGEX_LANG_MAP[ext])

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


def extract_git_insights(root: Path) -> str:
    """Extract comprehensive git insights for the project.

    Generates a Markdown document with:
    - Recent commits (last 30)
    - Per-module change frequency (which modules change most)
    - Recent active files
    - Contributors

    Args:
        root: Project root directory.

    Returns:
        Markdown string with git analysis, or empty string if git
        is unavailable.
    """
    parts: list[str] = ["# Git Insights\n"]

    # Recent commits (last 30)
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-30", "--format=%h %ai %s"],
            capture_output=True, text=True, cwd=str(root), check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Recent Commits\n```\n" + result.stdout.strip() + "\n```")
    except FileNotFoundError:
        return ""

    # Per-module change frequency (last 3 months)
    modules = detect_modules(root)
    if modules:
        freq_lines: list[str] = []
        for mod in modules:
            try:
                result = subprocess.run(
                    ["git", "log", "--oneline", "--since=3 months ago", "--", f"{mod}/"],
                    capture_output=True, text=True, cwd=str(root), check=False,
                )
                if result.returncode == 0:
                    count = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
                    freq_lines.append(f"- **{mod}**: {count} commits")
            except FileNotFoundError:
                break
        if freq_lines:
            parts.append("## Module Change Frequency (3 months)\n" + "\n".join(freq_lines))

    # Recently modified files (last 20 unique)
    try:
        result = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "-20"],
            capture_output=True, text=True, cwd=str(root), check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = list(dict.fromkeys(
                f.strip() for f in result.stdout.splitlines() if f.strip()
            ))[:20]
            parts.append("## Recently Modified Files\n" + "\n".join(f"- {f}" for f in files))
    except FileNotFoundError:
        pass

    # Contributors (last 3 months)
    try:
        result = subprocess.run(
            ["git", "shortlog", "-sn", "--since=3 months ago"],
            capture_output=True, text=True, cwd=str(root), check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Contributors (3 months)\n```\n" + result.stdout.strip() + "\n```")
    except FileNotFoundError:
        pass

    return "\n\n".join(parts)


def quick_scan(root: Path, since_sha: str) -> ScanReport:
    """Perform a quick scan of files changed since a git commit.

    Args:
        root: Project root directory.
        since_sha: Git commit SHA to diff against.

    Returns:
        ScanReport with analysis of changed files only.
    """
    report = ScanReport(root=root)

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", since_sha, "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
        )
        if result.returncode != 0:
            return full_scan(root)

        changed_files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except FileNotFoundError:
        return full_scan(root)

    # Detect venv directories by content
    venv_dirs = _find_venv_dirs(root)

    lang_counts: dict[str, int] = {}
    for file_str in changed_files:
        filepath = root / file_str
        if not filepath.exists():
            continue
        rel = Path(file_str)
        if _should_skip(rel, venv_dirs):
            continue
        report.file_count += 1
        ext = filepath.suffix.lower()
        if ext in _LANG_MAP:
            lang = _LANG_MAP[ext]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    report.languages = dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True))

    # Always do framework detection
    for marker, name in _FRAMEWORK_MARKERS.items():
        if (root / marker).exists():
            report.frameworks.append(name)

    # --- Phase 1 enhancements (always run, even in quick mode) ---
    report.config_contents = _read_config_files(root)
    report.entry_points = _read_entry_points(root, report.config_contents)
    report.git_summary = _extract_git_summary(root)

    return report
