"""Tests for hub.scanner — pure Python, no LLM needed."""
from pathlib import Path

from antigravity_engine.hub.scanner import ScanReport, full_scan, quick_scan


def test_full_scan_empty_dir(tmp_path: Path) -> None:
    report = full_scan(tmp_path)
    assert isinstance(report, ScanReport)
    assert report.file_count == 0
    assert report.languages == {}
    assert report.frameworks == []


def test_full_scan_detects_languages(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('hi')", encoding="utf-8")
    (tmp_path / "style.css").write_text("body{}", encoding="utf-8")

    report = full_scan(tmp_path)
    assert "Python" in report.languages
    assert "JavaScript" in report.languages
    assert report.file_count >= 3


def test_full_scan_detects_frameworks(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12", encoding="utf-8")

    report = full_scan(tmp_path)
    assert any("pyproject" in fw.lower() for fw in report.frameworks)
    assert report.has_docker


def test_full_scan_detects_tests(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    report = full_scan(tmp_path)
    assert report.has_tests


def test_full_scan_reads_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# My Project\nGreat stuff.", encoding="utf-8")
    report = full_scan(tmp_path)
    assert "My Project" in report.readme_snippet


def test_full_scan_skips_node_modules(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "index.js").write_text("module.exports = {}", encoding="utf-8")
    (tmp_path / "app.js").write_text("hi", encoding="utf-8")

    report = full_scan(tmp_path)
    # node_modules files should not be counted
    assert report.file_count == 1


def test_full_scan_top_dirs(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".hidden").mkdir()

    report = full_scan(tmp_path)
    assert "src" in report.top_dirs
    assert "tests" in report.top_dirs
    assert ".hidden" not in report.top_dirs


def test_full_scan_skips_custom_venv(tmp_path: Path) -> None:
    """Custom-named venvs (detected by pyvenv.cfg) are excluded."""
    venv = tmp_path / "my_custom_venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr/bin", encoding="utf-8")
    (venv / "lib").mkdir()
    (venv / "lib" / "site.py").write_text("# site", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")

    report = full_scan(tmp_path)
    assert report.file_count == 1  # only app.py
    assert "my_custom_venv" not in report.top_dirs


def test_full_scan_excludes_egg_info_from_top_dirs(tmp_path: Path) -> None:
    """egg-info directories are excluded from top_dirs."""
    (tmp_path / "mypackage.egg-info").mkdir()
    (tmp_path / "src").mkdir()

    report = full_scan(tmp_path)
    assert "src" in report.top_dirs
    assert "mypackage.egg-info" not in report.top_dirs


def test_full_scan_detects_nested_tests(tmp_path: Path) -> None:
    """Tests inside subdirectories (engine/tests/) are detected."""
    engine_tests = tmp_path / "engine" / "tests"
    engine_tests.mkdir(parents=True)
    (engine_tests / "test_foo.py").write_text("def test_foo(): pass", encoding="utf-8")

    report = full_scan(tmp_path)
    assert report.has_tests is True


def test_full_scan_detects_pytest(tmp_path: Path) -> None:
    """has_pytest is set when conftest.py or pytest.ini exists."""
    (tmp_path / "conftest.py").write_text("# conftest", encoding="utf-8")

    report = full_scan(tmp_path)
    assert report.has_pytest is True


def test_quick_scan_falls_back_to_full(tmp_path: Path) -> None:
    """quick_scan falls back to full_scan when git fails."""
    (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
    report = quick_scan(tmp_path, "nonexistent-sha")
    # Should still produce a valid report via fallback
    assert isinstance(report, ScanReport)
