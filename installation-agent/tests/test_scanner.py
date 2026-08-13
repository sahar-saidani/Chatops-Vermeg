import os
import pytest
from pathlib import Path
from app.services.scanner.file_scanner import FileScanner
from app.config.settings import settings

def test_file_scanner_scan():
    scanner = FileScanner()
    results = scanner.scan()
    
    # Assertions
    assert results.total_files > 0
    assert results.total_size_bytes > 0
    assert len(results.files) == results.total_files
    
    # Verify entrypoints are detected
    entrypoint_names = [Path(e).name for e in results.entrypoints]
    assert "start.sh" in entrypoint_names
    assert "setup.exe" in entrypoint_names
    assert "install.ps1" in entrypoint_names
    
    # Verify duplicates check
    # Check that it identifies duplicate files if any
    for h, file_paths in results.duplicates.items():
        assert len(file_paths) > 1
        
    # Check that individual file metadata has valid hashes, sizes, extensions
    for f in results.files:
        assert f.sha256 != ""
        assert f.md5 != ""
        assert f.size_bytes >= 0
        assert f.extension in ("", ".txt", ".env", ".yml", ".sh", ".xml", ".properties", ".service", ".json", ".exe", ".ps1", ".ini", ".reg", ".conf", ".yaml")


def _make_tree(root: Path, depth: int, files_per_level: int = 2) -> None:
    current = root
    for level in range(depth):
        current = current / f"level_{level}"
        current.mkdir(parents=True, exist_ok=True)
        for index in range(files_per_level):
            (current / f"file_{index}.txt").write_text(f"level {level} file {index}")


def test_scan_stops_at_max_depth(tmp_path, monkeypatch):
    """A tree deeper than max_scan_depth is cut off instead of walked whole."""
    _make_tree(tmp_path, depth=8)
    monkeypatch.setattr(settings, "max_scan_depth", 3)

    results = FileScanner(tmp_path).scan()

    depths = {Path(f.relative_path).parent.parts for f in results.files}
    assert depths, "expected the scan to index something"
    assert max(len(parts) for parts in depths) <= 3


def test_scan_stops_at_max_files(tmp_path, monkeypatch):
    """The file cap ends the walk early and marks the report as truncated."""
    _make_tree(tmp_path, depth=5, files_per_level=6)
    monkeypatch.setattr(settings, "max_scan_files", 7)

    results = FileScanner(tmp_path).scan()

    assert results.total_files == 7
    assert results.truncated is True
    assert "file limit" in (results.truncation_reason or "")


def test_scan_terminates_on_symlink_cycle(tmp_path, monkeypatch):
    """
    The original scanner walked with followlinks=True and no cycle detection,
    so a link pointing back at an ancestor never terminated. This is the case
    that outlived the orchestrator's 300s subprocess timeout.
    """
    inner = tmp_path / "a" / "b"
    inner.mkdir(parents=True)
    (inner / "real.txt").write_text("payload")

    loop = inner / "loop"
    try:
        os.symlink(tmp_path / "a", loop, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks is not permitted in this environment")

    # Even with following explicitly enabled, the walk must terminate.
    monkeypatch.setattr(settings, "follow_symlinks", True)
    monkeypatch.setattr(settings, "max_scan_seconds", 20)

    results = FileScanner(tmp_path).scan()

    assert any(f.filename == "real.txt" for f in results.files)
    assert results.total_files < 50, "cycle detection failed; the walk repeated the tree"


def test_oversized_files_are_indexed_without_hashes(tmp_path, monkeypatch):
    """Large artifacts are still listed, just not hashed twice end to end."""
    (tmp_path / "big.bin").write_bytes(b"x" * 4096)
    (tmp_path / "small.txt").write_text("hi")
    monkeypatch.setattr(settings, "max_hash_file_size_bytes", 1024)

    results = FileScanner(tmp_path).scan()

    by_name = {f.filename: f for f in results.files}
    assert by_name["big.bin"].sha256 == ""
    assert by_name["small.txt"].sha256 != ""
