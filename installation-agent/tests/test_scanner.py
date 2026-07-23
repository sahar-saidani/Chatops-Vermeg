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
