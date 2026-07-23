import pytest
from pathlib import Path
from app.services.validators.syntax_validator import SyntaxValidator
from app.services.scanner.file_scanner import FileScanner
from app.config.settings import settings

def test_syntax_validator_valid_files():
    valid_yml = settings.get_absolute_path(settings.fake_files_dir) / "project_python" / "application.yml"
    result = SyntaxValidator.validate_file(valid_yml)
    assert result.is_valid
    assert len(result.errors) == 0

def test_syntax_validator_corrupted_json():
    corrupted_json = settings.get_absolute_path(settings.fake_files_dir) / "corrupted_config.json"
    assert corrupted_json.exists()
    
    result = SyntaxValidator.validate_file(corrupted_json)
    
    # Assertions
    assert not result.is_valid
    assert len(result.errors) > 0
    # Checks that either JSON syntax error or simulated corruption is captured
    error_types = [e.type for e in result.errors]
    assert "syntax" in error_types or "integrity" in error_types

def test_syntax_validator_duplicate_keys():
    # .env in project_python has duplicate keys or similar checked by warnings
    # let's assert warnings are generated for corrupted_config.json duplicate keys
    corrupted_json = settings.get_absolute_path(settings.fake_files_dir) / "corrupted_config.json"
    result = SyntaxValidator.validate_file(corrupted_json)
    
    warning_types = [w.type for w in result.warnings]
    assert "duplicate_key" in warning_types

def test_validator_cross_references():
    # If a script references a file that is not scanned, validation_cross_references should raise broken_reference
    scanner = FileScanner()
    scan_res = scanner.scan()
    
    # Create mock scripts analysis referencing non_existent.conf
    from app.models.schemas import ScriptAnalysisResult
    mock_scripts = {
        "start.sh": ScriptAnalysisResult(referenced_files=["non_existent.conf"])
    }
    
    issues = SyntaxValidator.validate_cross_references(scan_res, mock_scripts)
    assert len(issues) > 0
    assert issues[0].type == "broken_reference"
