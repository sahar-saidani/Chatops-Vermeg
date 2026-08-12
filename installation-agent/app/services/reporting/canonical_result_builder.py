"""Builds the safe, canonical-event-shaped JSON result published by the
Installation Agent and printed on the CLI.

Takes the rich DeepAnalysisReport produced by the existing scan/analyze
pipeline (app/core/pipeline.py) and reduces it to the structure described in
the Installation Agent spec, redacting every secret/token value along the
way via app.services.security.secret_redactor. This is the only place that
decides what leaves the process (RabbitMQ, canonical_events, stdout) - the
richer DeepAnalysisReport itself keeps flowing into the existing local
report files (reports/*.json/html), unaffected.
"""

from __future__ import annotations

from typing import Any

from app.models.schemas import DeepAnalysisReport
from app.services.security.secret_redactor import (
    collect_secrets,
    evaluate_variable,
    redact_text,
)

# Risk score (0-100, from the existing InstallerAnalyzer) bucketed into a
# deterministic, explainable level.
_RISK_THRESHOLDS = (
    (80, "CRITICAL"),
    (60, "HIGH"),
    (30, "MEDIUM"),
)


def _risk_level(score: int, secrets_detected: list[dict[str, Any]]) -> str:
    # A CRITICAL-sensitivity secret (private key, live cloud credential...)
    # always forces a CRITICAL level, regardless of the aggregate score.
    if any(s.get("sensitivity") == "CRITICAL" for s in secrets_detected):
        return "CRITICAL"
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return "LOW"


def _collect_environment_variables(report: DeepAnalysisReport) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []

    for config_file in report.configuration_files:
        file_name = config_file.metadata.relative_path
        for key, value in config_file.values.items():
            variables.append(evaluate_variable(key, value, file_name))

    for template in report.environment_templates:
        file_name = template.metadata.relative_path
        for key, value in template.values.items():
            variables.append(evaluate_variable(key, value, file_name))

    return variables


def _installation_scripts_summary(report: DeepAnalysisReport) -> list[dict[str, Any]]:
    # Deliberately excludes InstallationScriptInfo.metadata (hashes/owner)
    # and any raw command text - scripts are analyzed, never echoed
    # verbatim, since a command line can itself carry an inline secret
    # (e.g. `curl -H "Authorization: Bearer ..."`).
    summary = []
    for script in report.installation_scripts:
        summary.append(
            {
                "file": script.metadata.relative_path,
                "script_type": script.script_type,
                "referenced_config_files": script.referenced_config_files,
                "referenced_environment_files": script.referenced_environment_files,
                "installation_directories": script.installation_directories,
                "referenced_executables": script.referenced_executables,
                "referenced_services": script.referenced_services,
                "command_count": len(script.commands),
            }
        )
    return summary


def _generated_files_summary(report: DeepAnalysisReport) -> list[dict[str, Any]]:
    summary = []
    for generated in report.generated_files:
        if generated.source == "script-derived":
            confidence = "HIGH"
        elif "generated" in generated.metadata.relative_path.replace("\\", "/").lower():
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        summary.append(
            {
                "file": generated.metadata.relative_path,
                "generated_kind": generated.generated_kind,
                "confidence": confidence,
                "source": generated.source,
            }
        )
    return summary


def _issues_summary(report: DeepAnalysisReport) -> list[dict[str, Any]]:
    issues = []
    for item in [*report.validation_report.errors, *report.validation_report.warnings]:
        issues.append(
            {
                "file": item.file_path,
                "type": item.type,
                "severity": item.severity,
                "message": redact_text(item.message),
            }
        )
    return issues


def build_canonical_result(
    report: DeepAnalysisReport | None,
    *,
    tenant: str,
    environment: str,
    environment_type: str,
    machine_reference: str,
    operating_system: str,
    config_path: str,
    scan_status: str,
) -> dict[str, Any]:
    """Reduce a DeepAnalysisReport into the safe, publishable JSON result."""

    if report is None:
        return {
            "agent": "installation",
            "tenant": tenant,
            "environment": environment,
            "environment_type": environment_type,
            "machine_reference": machine_reference,
            "os": operating_system,
            "config_path": config_path,
            "scan_status": scan_status,
            "files_scanned": 0,
            "files_by_type": {"scripts": 0, "environment": 0, "configuration": 0, "generated": 0},
            "environment_variables": [],
            "secrets_detected": [],
            "installation_scripts": [],
            "generated_files": [],
            "dependencies": {"nodes": [], "edges": [], "missing_dependencies": []},
            "issues": [],
            "risk_score": 0,
            "risk_level": "LOW",
        }

    environment_variables = _collect_environment_variables(report)
    secrets_detected = collect_secrets(environment_variables)

    dependency_graph = report.dependency_graph
    dependencies = {
        "nodes": [node.model_dump() for node in dependency_graph.nodes],
        "edges": [list(edge) for edge in dependency_graph.edges],
        "missing_dependencies": dependency_graph.missing_dependencies,
        "duplicate_dependencies": dependency_graph.duplicate_dependencies,
        "version_conflicts": dependency_graph.version_conflicts,
    }

    risk_score = report.risk_report.score

    return {
        "agent": "installation",
        "tenant": tenant,
        "environment": environment,
        "environment_type": environment_type,
        "machine_reference": machine_reference,
        "os": operating_system,
        "config_path": config_path,
        "scan_status": scan_status,
        "files_scanned": report.scan_results.total_files,
        "files_by_type": {
            "scripts": len(report.installation_scripts),
            "environment": len(report.environment_templates),
            "configuration": len(report.configuration_files),
            "generated": len(report.generated_files),
        },
        "environment_variables": environment_variables,
        "secrets_detected": secrets_detected,
        "installation_scripts": _installation_scripts_summary(report),
        "generated_files": _generated_files_summary(report),
        "dependencies": dependencies,
        "issues": _issues_summary(report),
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score, secrets_detected),
        "risk_factors": report.risk_report.risk_factors,
        "recommendations": report.risk_report.recommendations,
    }
