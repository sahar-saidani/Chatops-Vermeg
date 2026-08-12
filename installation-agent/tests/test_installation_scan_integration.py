"""End-to-end tests for the production scan path: real files on disk ->
run_analysis_pipeline -> build_canonical_result.

Unlike tests/test_analyzer.py & co (which exercise the individual services
against the fake_files/ fixture), these drive the exact pipeline main.py
--scan uses, against small real temp directories, and assert on the
published/CLI-facing result - the one place secrets must never leak.
"""

from __future__ import annotations

import json

import pytest

from app.config.machine_identity import MachineIdentity
from app.core.pipeline import run_analysis_pipeline
from app.services.reporting.canonical_result_builder import build_canonical_result


@pytest.fixture
def identity_env(monkeypatch):
    monkeypatch.setenv("TENANT_NAME", "MAIF")
    monkeypatch.setenv("ENVIRONMENT_NAME", "DEV")
    monkeypatch.setenv("ENVIRONMENT_TYPE", "STANDALONE")
    monkeypatch.setenv("MACHINE_REFERENCE", "windows-local")
    monkeypatch.delenv("NODE_ROLE", raising=False)
    return MachineIdentity.from_env()


def _build_result(tmp_path, identity, operating_system="WINDOWS"):
    report = run_analysis_pipeline(target_dir=tmp_path)
    return build_canonical_result(
        report,
        tenant=identity.tenant_name,
        environment=identity.environment_name,
        environment_type=identity.environment_type,
        machine_reference=identity.machine_reference,
        operating_system=operating_system,
        config_path=str(tmp_path),
        scan_status="COMPLETED",
    )


# Test 1: scanning a real folder with .env / install.sh / application.yml
def test_scans_real_config_directory(tmp_path, identity_env):
    (tmp_path / ".env").write_text("DATABASE_HOST=localhost\nAPI_TOKEN=secret-value\n")
    (tmp_path / "install.sh").write_text("#!/bin/bash\nmkdir -p /opt/app\ncp app.yml /opt/app/app.yml\n")
    (tmp_path / "application.yml").write_text("server:\n  port: 8080\n")

    result = _build_result(tmp_path, identity_env)

    assert result["files_scanned"] == 3
    assert result["scan_status"] == "COMPLETED"


# Test 2: a plain variable is detected and its value is visible (not sensitive)
def test_detects_plain_environment_variable(tmp_path, identity_env):
    (tmp_path / ".env").write_text("DATABASE_HOST=localhost\n")

    result = _build_result(tmp_path, identity_env)

    matches = [v for v in result["environment_variables"] if v["name"] == "DATABASE_HOST"]
    assert len(matches) == 1
    assert matches[0]["value"] == "localhost"
    assert matches[0]["sensitive"] is False


# Test 3: a secret is detected and its value is never returned anywhere
def test_detects_secret_without_leaking_value(tmp_path, identity_env):
    (tmp_path / ".env").write_text("API_TOKEN=secret-value\n")

    result = _build_result(tmp_path, identity_env)

    assert len(result["secrets_detected"]) == 1
    secret = result["secrets_detected"][0]
    assert secret["name"] == "API_TOKEN"
    assert "value" not in secret
    assert secret["value_redacted"] == "********"

    # The raw value must not appear anywhere in the published payload.
    serialized = json.dumps(result)
    assert "secret-value" not in serialized


# Test 4: an installation script is detected
def test_detects_installation_script(tmp_path, identity_env):
    (tmp_path / "install.sh").write_text("#!/bin/bash\nmkdir -p /opt/app\n")

    result = _build_result(tmp_path, identity_env)

    assert result["files_by_type"]["scripts"] == 1
    assert result["installation_scripts"][0]["file"] == "install.sh"
    # Raw command text is never included, only structured/aggregated fields.
    assert "commands" not in result["installation_scripts"][0]


# Test 5: a file produced by an install script is flagged as generated
def test_detects_generated_file(tmp_path, identity_env):
    (tmp_path / "install.sh").write_text("#!/bin/bash\necho done > runtime.env\n")
    (tmp_path / "runtime.env").write_text("APP_READY=true\n")

    result = _build_result(tmp_path, identity_env)

    generated_names = {g["file"] for g in result["generated_files"]}
    assert "runtime.env" in generated_names
    generated_entry = next(g for g in result["generated_files"] if g["file"] == "runtime.env")
    assert generated_entry["confidence"] in {"HIGH", "MEDIUM", "LOW"}


# Test 6: paths in the result are portable (forward-slash, plain strings)
def test_relative_paths_are_portable_posix_style(tmp_path, identity_env):
    nested = tmp_path / "generated"
    nested.mkdir()
    (nested / "app.conf").write_text("port=8080\n")

    report = run_analysis_pipeline(target_dir=tmp_path)

    for file_meta in report.scan_results.files:
        assert "\\" not in file_meta.relative_path


# Test 7: config_path in the result is always a plain, JSON-serializable string
def test_config_path_is_plain_string(tmp_path, identity_env):
    result = _build_result(tmp_path, identity_env)
    assert isinstance(result["config_path"], str)
    json.dumps(result)  # must not raise


# Test 8: an empty config directory scans cleanly with zero findings
def test_empty_directory_scans_cleanly(tmp_path, identity_env):
    result = _build_result(tmp_path, identity_env)

    assert result["files_scanned"] == 0
    assert result["secrets_detected"] == []
    assert result["risk_level"] == "LOW"


# Test 9: an unreadable file does not crash the pipeline
def test_unreadable_file_does_not_crash_pipeline(tmp_path, identity_env, monkeypatch):
    bad_file = tmp_path / "broken.env"
    bad_file.write_text("KEY=value\n")

    from pathlib import Path

    original_read_text = Path.read_text

    def failing_read_text(self, *args, **kwargs):
        if self.name == "broken.env":
            raise PermissionError("simulated unreadable file")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read_text)

    result = _build_result(tmp_path, identity_env)
    assert result["scan_status"] == "COMPLETED"
    assert result["files_scanned"] == 1


# Test 10: a file with an unknown extension does not crash the pipeline
def test_unknown_extension_is_handled(tmp_path, identity_env):
    (tmp_path / "notes.xyz123").write_text("some: value\n")

    result = _build_result(tmp_path, identity_env)
    assert result["files_scanned"] == 1
    assert result["scan_status"] == "COMPLETED"


# Test 11: tenant / environment / machine / os are present in the result
def test_result_contains_identity_fields(tmp_path, identity_env):
    result = _build_result(tmp_path, identity_env, operating_system="WINDOWS")

    assert result["tenant"] == "MAIF"
    assert result["environment"] == "DEV"
    assert result["machine_reference"] == "windows-local"
    assert result["os"] == "WINDOWS"


# Test 12: the agent identity is always "installation"
def test_result_agent_identity(tmp_path, identity_env):
    result = _build_result(tmp_path, identity_env)
    assert result["agent"] == "installation"
