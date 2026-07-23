import pytest
from pathlib import Path
from app.core.pipeline import run_analysis_pipeline
from app.config.settings import settings

def test_report_generation():
    # Execute full pipeline which automatically triggers ReportGenerator
    report = run_analysis_pipeline()
    
    reports_dir = settings.get_absolute_path(settings.reports_dir)
    assert reports_dir.exists()
    
    # Assert presence of key reports
    json_rep = reports_dir / "installation_report.json"
    md_rep = reports_dir / "installation_report.md"
    html_rep = reports_dir / "installation_report.html"
    configs_rep = reports_dir / "configuration_inventory.json"
    risk_rep = reports_dir / "risk_report.json"
    
    assert json_rep.exists()
    assert md_rep.exists()
    assert html_rep.exists()
    assert configs_rep.exists()
    assert risk_rep.exists()
    
    # Check that contents are non-empty
    assert json_rep.stat().st_size > 0
    assert md_rep.stat().st_size > 0
    assert html_rep.stat().st_size > 0
