"""Tests for hub agent ImportError handling and area detection."""
import sys
from pathlib import Path

import pytest
from unittest.mock import patch


def test_build_refresh_swarm_import_error():
    """build_refresh_swarm raises ImportError with helpful message when agents SDK missing."""
    from antigravity_engine.hub.agents import build_refresh_swarm

    with patch.dict(sys.modules, {"agents": None}):
        with pytest.raises(ImportError, match="OpenAI Agent SDK not found"):
            build_refresh_swarm("test-model")


def test_build_ask_swarm_import_error():
    """build_ask_swarm raises ImportError with helpful message when agents SDK missing."""
    from antigravity_engine.hub.agents import build_ask_swarm

    with patch.dict(sys.modules, {"agents": None}):
        with pytest.raises(ImportError, match="OpenAI Agent SDK not found"):
            build_ask_swarm("test-model")


def test_detect_areas_finds_source_dirs(tmp_path: Path) -> None:
    """_detect_areas finds directories containing source files."""
    from antigravity_engine.hub.agents import _detect_areas

    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "main.py").write_text("x = 1")
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli" / "app.py").write_text("y = 2")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# docs")

    areas = _detect_areas(tmp_path)
    assert "engine" in areas
    assert "cli" in areas
    assert "docs" in areas


def test_detect_areas_skips_hidden_and_skip_dirs(tmp_path: Path) -> None:
    """_detect_areas ignores .git, node_modules, etc."""
    from antigravity_engine.hub.agents import _detect_areas

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("x")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1")

    areas = _detect_areas(tmp_path)
    assert ".git" not in areas
    assert "node_modules" not in areas
    assert "src" in areas
