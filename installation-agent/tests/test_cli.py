import pytest
from typer.testing import CliRunner
from cli import cli

runner = CliRunner()

def test_cli_status():
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Workspace Path" in result.stdout

def test_cli_scan():
    result = runner.invoke(cli, ["scan"])
    assert result.exit_code == 0
    assert "Scanned Files" in result.stdout

def test_cli_discover():
    result = runner.invoke(cli, ["discover"])
    assert result.exit_code == 0
    assert "installation entrypoints" in result.stdout or "No installation entrypoints" in result.stdout

def test_cli_analyze():
    result = runner.invoke(cli, ["analyze"])
    assert result.exit_code == 0
    assert "Risk Score" in result.stdout

def test_cli_graph():
    result = runner.invoke(cli, ["graph"])
    assert result.exit_code == 0
    assert "Dependencies Graph" in result.stdout

def test_cli_report():
    result = runner.invoke(cli, ["report"])
    assert result.exit_code == 0
    assert "generated reports" in result.stdout
