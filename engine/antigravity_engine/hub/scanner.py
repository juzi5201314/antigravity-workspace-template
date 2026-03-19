"""Project scanner — pure Python, no LLM dependency."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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

    return report


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

    return report
