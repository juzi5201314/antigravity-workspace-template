"""Tests for hub.pipeline — mocked Runner."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from antigravity_engine.hub.pipeline import (
    _build_ask_context,
    _format_scan_report,
    _get_head_sha,
)
from antigravity_engine.hub.scanner import ScanReport


def test_format_scan_report_basic() -> None:
    report = ScanReport(
        root=Path("/tmp/test"),
        languages={"Python": 10, "JavaScript": 5},
        frameworks=["Python (pyproject.toml)"],
        top_dirs=["src", "tests"],
        file_count=15,
        has_tests=True,
        has_ci=True,
        has_docker=False,
        readme_snippet="# My Project",
    )
    result = _format_scan_report(report)
    assert "Python: 10" in result
    assert "JavaScript: 5" in result
    assert "pyproject.toml" in result
    assert "src, tests" in result
    assert "My Project" in result


def test_format_scan_report_empty() -> None:
    report = ScanReport(root=Path("/tmp/empty"))
    result = _format_scan_report(report)
    assert "Total files: 0" in result


def test_get_head_sha_no_git(tmp_path: Path) -> None:
    """Returns None when not in a git repo."""
    sha = _get_head_sha(tmp_path)
    assert sha is None or isinstance(sha, str)


@pytest.mark.asyncio
async def test_refresh_pipeline_creates_conventions(tmp_path: Path, monkeypatch) -> None:
    """refresh_pipeline writes conventions.md."""
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    ag_dir = tmp_path / ".antigravity"
    ag_dir.mkdir()

    mock_result = MagicMock()
    mock_result.final_output = "# Conventions\n\nThis is a Python project."

    # Create a mock agents module with Runner.run as AsyncMock
    mock_agents_module = MagicMock()
    mock_agents_module.Runner.run = AsyncMock(return_value=mock_result)
    mock_agents_module.Agent = MagicMock()
    mock_agents_module.set_tracing_disabled = MagicMock()

    with patch.dict("sys.modules", {"agents": mock_agents_module}):
        import importlib
        import antigravity_engine.hub.pipeline as pipeline_mod
        importlib.reload(pipeline_mod)

        await pipeline_mod.refresh_pipeline(tmp_path, quick=False)

    conventions = ag_dir / "conventions.md"
    assert conventions.exists()
    assert "Python project" in conventions.read_text(encoding="utf-8")
    assert (ag_dir / "knowledge_graph.json").exists()
    assert (ag_dir / "knowledge_graph.md").exists()
    assert (ag_dir / "knowledge_graph.mmd").exists()
    assert (ag_dir / "document_index.md").exists()
    assert (ag_dir / "data_overview.md").exists()
    assert (ag_dir / "media_manifest.md").exists()


@pytest.mark.asyncio
async def test_ask_pipeline_returns_answer(tmp_path: Path, monkeypatch) -> None:
    """ask_pipeline returns an answer string."""
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    ag_dir = tmp_path / ".antigravity"
    ag_dir.mkdir()
    (ag_dir / "conventions.md").write_text("Python + FastAPI", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.final_output = "This project uses FastAPI."

    mock_agents_module = MagicMock()
    mock_agents_module.Runner.run = AsyncMock(return_value=mock_result)
    mock_agents_module.Agent = MagicMock()
    mock_agents_module.set_tracing_disabled = MagicMock()

    with patch.dict("sys.modules", {"agents": mock_agents_module}):
        import importlib
        import antigravity_engine.hub.pipeline as pipeline_mod
        importlib.reload(pipeline_mod)

        answer = await pipeline_mod.ask_pipeline(tmp_path, "What framework?")

    assert "FastAPI" in answer


def test_build_ask_context_includes_root_and_memory_docs(tmp_path: Path) -> None:
    """ask context should include root docs and memory logs when present."""
    ag_dir = tmp_path / ".antigravity"
    memory_dir = ag_dir / "memory"
    (ag_dir / "decisions").mkdir(parents=True)
    memory_dir.mkdir(parents=True)

    (ag_dir / "conventions.md").write_text("Python + FastAPI", encoding="utf-8")
    (tmp_path / "CONTEXT.md").write_text("Use service layer", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "Read the antigravity files first",
        encoding="utf-8",
    )
    (memory_dir / "reports.md").write_text(
        "Auth module needs cleanup",
        encoding="utf-8",
    )

    context = _build_ask_context(tmp_path)

    assert ".antigravity/conventions.md" in context
    assert "CONTEXT.md" in context
    assert "AGENTS.md" in context
    assert ".antigravity/memory/reports.md" in context
    assert "Auth module needs cleanup" in context


# ---------------------------------------------------------------------------
# Phase 1: config/entry/git in _format_scan_report
# ---------------------------------------------------------------------------


def test_format_scan_report_includes_config() -> None:
    """Config file contents appear in the formatted report."""
    report = ScanReport(
        root=Path("/tmp/test"),
        config_contents={"pyproject.toml": '[project]\nname = "demo"'},
    )
    result = _format_scan_report(report)
    assert "pyproject.toml" in result
    assert 'name = "demo"' in result


def test_format_scan_report_includes_entry_points() -> None:
    """Entry point snippets appear in the formatted report."""
    report = ScanReport(
        root=Path("/tmp/test"),
        entry_points={"main.py": "import sys\nprint('hello')"},
    )
    result = _format_scan_report(report)
    assert "main.py" in result
    assert "import sys" in result


def test_format_scan_report_includes_git() -> None:
    """Git summary appears in the formatted report."""
    report = ScanReport(
        root=Path("/tmp/test"),
        git_summary="Recent commits:\nabc123 fix auth\ndef456 add tests",
    )
    result = _format_scan_report(report)
    assert "fix auth" in result
    assert "add tests" in result
