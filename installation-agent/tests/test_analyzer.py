import pytest
from app.services.scanner.file_scanner import FileScanner
from app.services.analyzer.installer_analyzer import InstallerAnalyzer
from app.models.schemas import ScriptAnalysisResult, ConfigAnalysisResult, ValidationReport

def test_risk_analyzer_calculation():
    scanner = FileScanner()
    scan_res = scanner.scan()
    
    # Simple scans with specific mock detections to evaluate score additions
    mock_scripts = {
        "/fake/start.sh": ScriptAnalysisResult(commands_run=["sudo apt-get update", "rm -rf /opt/temp"])
    }
    mock_configs = {
        "/fake/.env": ConfigAnalysisResult(
            security_settings={"DB_PASSWORD": "my_hardcoded_pass_value_123"},
            raw_values={"DB_PASSWORD": "my_hardcoded_pass_value_123"}
        )
    }
    
    report = InstallerAnalyzer.analyze_risk(
        scan_results=scan_res,
        scripts_analysis=mock_scripts,
        configs_analysis=mock_configs,
        validation_report=ValidationReport(is_valid=True, errors=[], warnings=[])
    )
    
    # Assertions
    assert report.score > 0
    assert "PRIVILEGE_ESCALATION" in report.risk_factors
    assert "DANGEROUS_COMMANDS" in report.risk_factors
    assert "HARDCODED_SECRETS" in report.risk_factors
    
    # Verify recommendations are populated
    assert len(report.recommendations) > 0
