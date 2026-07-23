import re
import json
import yaml
import logging
import xml.etree.ElementTree as ET
import configparser
from pathlib import Path
from typing import List
from app.models.schemas import ValidationReport, ValidationErrorItem, ScanResults

logger = logging.getLogger("installation_agent")

class SyntaxValidator:
    """Validates syntax integrity, duplicate keys, empty variables, and cross-file references."""
    
    @staticmethod
    def validate_file(file_path: Path) -> ValidationReport:
        errors = []
        warnings = []
        ext = file_path.suffix.lower()
        filename = file_path.name.lower()
        is_env_template = filename.endswith(".env.template") or filename.endswith(".env.example") or filename == ".env" or ext == ".env"
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            errors.append(ValidationErrorItem(
                file_path=str(file_path),
                type="read_error",
                message=f"Failed to read file: {e}",
                severity="error"
            ))
            return ValidationReport(is_valid=False, errors=errors, warnings=warnings)
            
        # 1. Route validator based on extension
        if ext == ".json":
            SyntaxValidator._validate_json(content, file_path, errors, warnings)
        elif ext in (".yaml", ".yml"):
            SyntaxValidator._validate_yaml(content, file_path, errors, warnings)
        elif ext in (".xml", ".config") or filename == "web.config":
            SyntaxValidator._validate_xml(content, file_path, errors, warnings)
        elif ext == ".ini":
            SyntaxValidator._validate_ini(content, file_path, errors, warnings)
        elif ext == ".properties" or filename == "application.properties":
            SyntaxValidator._validate_properties(content, file_path, errors, warnings)
        elif is_env_template:
            SyntaxValidator._validate_env(content, file_path, errors, warnings)
            
        # 2. Check for simulated corrupted flag
        if "corrupted" in content.lower():
            errors.append(ValidationErrorItem(
                file_path=str(file_path),
                type="integrity",
                message="Simulated file corruption detected ('corrupted' marker found).",
                severity="error"
            ))
            
        return ValidationReport(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    @staticmethod
    def validate_cross_references(scan_results: ScanResults, scripts_analysis: dict) -> List[ValidationErrorItem]:
        """Checks for referenced files in scripts that do not exist in the scan results."""
        issues = []
        # Get set of all scanned file names and paths (both relative and absolute)
        scanned_names = {Path(f.absolute_path).name for f in scan_results.files}
        scanned_paths = {f.absolute_path for f in scan_results.files}
        
        for script_path, analysis in scripts_analysis.items():
            for ref_file in analysis.referenced_files:
                ref_name = Path(ref_file).name
                
                # Check if referenced file exists in scanned database
                # Allow matching by base filename or exact path
                found = False
                if ref_name in scanned_names:
                    found = True
                else:
                    # check if path matches relative or absolute
                    for sp in scanned_paths:
                        if ref_file in sp:
                            found = True
                            break
                            
                if not found:
                    issues.append(ValidationErrorItem(
                        file_path=script_path,
                        type="broken_reference",
                        message=f"Script references missing file: '{ref_file}'",
                        severity="error"
                    ))
        return issues

    @staticmethod
    def _validate_json(content: str, path: Path, errors: list, warnings: list):
        # Regex check for duplicate keys first
        keys = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*:', content)
        seen = set()
        dupes = set()
        for k in keys:
            if k in seen:
                dupes.add(k)
            seen.add(k)
        for d in dupes:
            warnings.append(ValidationErrorItem(
                file_path=str(path),
                type="duplicate_key",
                message=f"Duplicate JSON key found: '{d}'",
                severity="warning"
            ))
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="syntax",
                message=f"Invalid JSON syntax: {e}",
                severity="error"
            ))

    @staticmethod
    def _validate_yaml(content: str, path: Path, errors: list, warnings: list):
        # Check duplicate keys inside same YAML scope using line prefix indentations first
        indent_keys = {}
        for line in content.splitlines():
            match = re.match(r'^(\s*)([a-zA-Z0-9_\-]+)\s*:', line)
            if match:
                indent = len(match.group(1))
                key = match.group(2)
                seen = indent_keys.setdefault(indent, set())
                if key in seen:
                    warnings.append(ValidationErrorItem(
                        file_path=str(path),
                        type="duplicate_key",
                        message=f"Duplicate YAML key found: '{key}'",
                        severity="warning"
                    ))
                seen.add(key)
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="syntax",
                message=f"Invalid YAML syntax: {e}",
                severity="error"
            ))

    @staticmethod
    def _validate_xml(content: str, path: Path, errors: list, warnings: list):
        try:
            ET.fromstring(content)
        except ET.ParseError as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="syntax",
                message=f"Invalid XML syntax: {e}",
                severity="error"
            ))

    @staticmethod
    def _validate_ini(content: str, path: Path, errors: list, warnings: list):
        parser = configparser.ConfigParser()
        try:
            parser.read_string(content)
        except configparser.DuplicateSectionError as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="duplicate_section",
                message=str(e),
                severity="error"
            ))
        except configparser.DuplicateOptionError as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="duplicate_key",
                message=str(e),
                severity="error"
            ))
        except configparser.Error as e:
            errors.append(ValidationErrorItem(
                file_path=str(path),
                type="syntax",
                message=f"Invalid INI syntax: {e}",
                severity="error"
            ))

    @staticmethod
    def _validate_properties(content: str, path: Path, errors: list, warnings: list):
        seen_keys = set()
        for i, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            if '=' in line or ':' in line:
                sep = '=' if '=' in line else ':'
                key = line.split(sep, 1)[0].strip()
                if key in seen_keys:
                    warnings.append(ValidationErrorItem(
                        file_path=str(path),
                        type="duplicate_key",
                        message=f"Duplicate properties key on line {i}: '{key}'",
                        severity="warning"
                    ))
                seen_keys.add(key)

    @staticmethod
    def _validate_env(content: str, path: Path, errors: list, warnings: list):
        seen_keys = set()
        for i, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    errors.append(ValidationErrorItem(
                        file_path=str(path),
                        type="invalid_variable_name",
                        message=f"Invalid environment variable name on line {i}: '{key}'",
                        severity="error"
                    ))
                if key in seen_keys:
                    warnings.append(ValidationErrorItem(
                        file_path=str(path),
                        type="duplicate_key",
                        message=f"Duplicate env key on line {i}: '{key}'",
                        severity="warning"
                    ))
                seen_keys.add(key)
                
                # Flag empty passwords/tokens/secrets
                if any(x in key.lower() for x in ("password", "secret", "token", "key")) and not val:
                    warnings.append(ValidationErrorItem(
                        file_path=str(path),
                        type="missing_value",
                        message=f"Sensitive credential key '{key}' has empty/blank value on line {i}",
                        severity="warning"
                    ))
