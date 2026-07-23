import logging
from pathlib import Path
from typing import Dict, Any, List
from app.models.schemas import RiskScoreCard, ScanResults

logger = logging.getLogger("installation_agent")

class InstallerAnalyzer:
    """Computes a risk profile score (0-100) and provides recommendations based on static code indicators."""
    
    @staticmethod
    def analyze_risk(
        scan_results: ScanResults,
        scripts_analysis: Dict[str, Any],
        configs_analysis: Dict[str, Any],
        validation_report: Any = None
    ) -> RiskScoreCard:
        score = 0
        risk_factors = []
        reasons = []
        recommendations = []
        
        # 1. Flag unsigned / scripts executable
        executables = [f for f in scan_results.files if f.extension in (".exe", ".msi", ".bat", ".cmd", ".ps1")]
        if executables:
            deduction = min(len(executables) * 10, 30)
            score += deduction
            risk_factors.append("UNSIGNED_EXECUTABLES")
            reasons.append({
                "factor": "Unsigned Executables / Scripts",
                "impact": deduction,
                "detail": f"Discovered {len(executables)} executable assets in path (e.g. {[Path(e.absolute_path).name for e in executables[:3]]})"
            })
            recommendations.append("Verify and digitally sign all installation executables, scripts, and helper binaries.")

        # 2. Flag sudo / root privilege scripts
        sudo_commands = []
        for script_path, script_res in scripts_analysis.items():
            for cmd in script_res.commands_run:
                if "sudo " in cmd or "root" in cmd:
                    sudo_commands.append((script_path, cmd))
        if sudo_commands:
            score += 20
            risk_factors.append("PRIVILEGE_ESCALATION")
            reasons.append({
                "factor": "Privileged Execution Required",
                "impact": 20,
                "detail": f"Script leverages 'sudo' or validates root environment. Example in {Path(sudo_commands[0][0]).name}: '{sudo_commands[0][1]}'"
            })
            recommendations.append("Avoid scripting 'sudo' executions; invoke dependencies using granular permission constraints.")

        # 3. Flag dangerous bash/shell/PS commands
        dangerous_cmds = []
        for script_path, script_res in scripts_analysis.items():
            for cmd in script_res.commands_run:
                if any(x in cmd for x in ("rm -rf", "chmod 777", "curl", "wget")):
                    dangerous_cmds.append((script_path, cmd))
        if dangerous_cmds:
            score += 15
            risk_factors.append("DANGEROUS_COMMANDS")
            reasons.append({
                "factor": "Dangerous Shell Invocations",
                "impact": 15,
                "detail": f"Script contains potential system modifications (e.g. rm -rf, chmod 777, or raw curls). Example: '{dangerous_cmds[0][1]}'"
            })
            recommendations.append("Do not deploy scripts using wide privileges (like chmod 777) or pipe network downloads directly to shells.")

        # 4. Flag hardcoded secrets
        hardcoded_secrets = []
        for config_path, config_res in configs_analysis.items():
            for key, val in config_res.security_settings.items():
                val_str = str(val).strip()
                # Check if it has a value and doesn't look like an env substitution variable
                if val_str and not (val_str.startswith("$") or val_str.startswith("{") or "env" in val_str.lower()):
                    if any(x in key.lower() for x in ("password", "secret", "token", "key")):
                        hardcoded_secrets.append((config_path, key))
        if hardcoded_secrets:
            score += 25
            risk_factors.append("HARDCODED_SECRETS")
            reasons.append({
                "factor": "Hardcoded Secrets Detected",
                "impact": 25,
                "detail": f"Found password, token, or private key values written in text. Example in {Path(hardcoded_secrets[0][0]).name}: key '{hardcoded_secrets[0][1]}'"
            })
            recommendations.append("Migrate plain secrets out of code/configs. Retrieve them dynamically via Environment variables or KMS stores.")

        # 5. Flag unknown vendor / missing licensing info
        vendor_found = False
        for config_res in configs_analysis.values():
            raw_keys = [k.lower() for k in config_res.raw_values.keys()]
            if any("vendor" in k or "manufacturer" in k or "author" in k or "license" in k for k in raw_keys):
                vendor_found = True
                break
        if not vendor_found:
            score += 10
            risk_factors.append("UNKNOWN_VENDOR")
            reasons.append({
                "factor": "Unknown Project Ownership",
                "impact": 10,
                "detail": "No vendor, creator, or license properties were found in configuration files."
            })
            recommendations.append("Incorporate vendor headers and license files inside the deployment structure.")

        # 6. Flag syntax/validation errors
        if validation_report and not getattr(validation_report, "is_valid", True):
            error_count = len(getattr(validation_report, "errors", []))
            if error_count > 0:
                deduction = min(error_count * 5, 20)
                score += deduction
                risk_factors.append("VALIDATION_ERRORS")
                reasons.append({
                    "factor": "Syntactic Validation Issues",
                    "impact": deduction,
                    "detail": f"Detected {error_count} syntax validation errors in project configurations."
                })
                recommendations.append("Resolve all syntax and broken cross-file dependencies before launching.")
                
        # Limit score bounds
        score = min(max(score, 0), 100)
        
        if score == 0:
            recommendations.append("Audit parameters verify clean risk checks. Ready to plan next stages.")
            
        logger.info(f"Risk analysis complete. Calculated score: {score}")
        
        return RiskScoreCard(
            score=score,
            risk_factors=risk_factors,
            reasons=reasons,
            recommendations=recommendations
        )
