from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from app.models.schemas import (
    ConfigAnalysisResult,
    ConfigurationFileInfo,
    DeepAnalysisReport,
    EnvironmentTemplateInfo,
    FileMetadata,
    GeneratedFileInfo,
    InstallationMetadata,
    InstallationPackageInfo,
    InstallationScriptInfo,
    ScanResults,
    ScriptAnalysisResult,
    WatchdogEvent,
)

PACKAGE_NAMES = {
    "setup.exe",
    "installer.exe",
    "setup.msi",
    "install.ps1",
    "install.bat",
    "install.sh",
    "setup.sh",
    "bootstrap.sh",
    "configure.sh",
    "postinstall.sh",
    "preinstall.sh",
}
PACKAGE_EXTENSIONS = {".msi", ".rpm", ".deb", ".bin"}
SCRIPT_EXTENSIONS = {".sh", ".ps1", ".bat", ".cmd", ".service"}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".xml", ".properties", ".conf", ".cfg", ".ini", ".toml", ".reg", ".config"}
TEMPLATE_NAMES = {
    ".env",
    ".env.example",
    ".env.template",
    "environment.conf",
    "application.env.template",
    "application.env.example",
}
GENERATED_ENV_NAMES = {
    "application.env",
    "runtime.env",
    "generated.env",
}
GENERATED_CONFIG_NAMES = {
    "generated.properties",
    "runtime.yml",
    "runtime.yaml",
    "runtime.json",
    "config.ini",
}


@dataclass
class MetadataCollection:
    installation_packages: List[InstallationPackageInfo]
    installation_scripts: List[InstallationScriptInfo]
    configuration_files: List[ConfigurationFileInfo]
    environment_templates: List[EnvironmentTemplateInfo]
    generated_configuration_files: List[GeneratedFileInfo]
    generated_environment_files: List[GeneratedFileInfo]
    final_environment_variables: Dict[str, Any]
    generated_files: List[GeneratedFileInfo]
    installation_metadata: InstallationMetadata


class InstallationMetadataCollector:
    @staticmethod
    def collect(
        scan_results: ScanResults,
        scripts_analysis: Dict[str, ScriptAnalysisResult],
        configs_analysis: Dict[str, ConfigAnalysisResult],
        watchdog_events: List[WatchdogEvent],
        target_dir: Path,
    ) -> MetadataCollection:
        metadata_by_path = {file.absolute_path: file for file in scan_results.files}
        generated_targets = InstallationMetadataCollector._collect_generated_targets(scripts_analysis)

        installation_packages: List[InstallationPackageInfo] = []
        installation_scripts: List[InstallationScriptInfo] = []
        configuration_files: List[ConfigurationFileInfo] = []
        environment_templates: List[EnvironmentTemplateInfo] = []
        generated_configuration_files: List[GeneratedFileInfo] = []
        generated_environment_files: List[GeneratedFileInfo] = []
        generated_files: List[GeneratedFileInfo] = []
        final_environment_variables: Dict[str, Any] = {}

        for file in scan_results.files:
            metadata = file
            filename = file.filename.lower()
            extension = file.extension.lower()
            is_package = InstallationMetadataCollector._is_package(filename, extension)
            is_script = InstallationMetadataCollector._is_script(filename, extension)
            is_config = InstallationMetadataCollector._is_config(filename, extension)
            is_template = InstallationMetadataCollector._is_environment_template(filename, extension)
            is_generated = InstallationMetadataCollector._is_generated_file(filename, extension, generated_targets)

            if is_package:
                installation_packages.append(
                    InstallationPackageInfo(metadata=metadata, package_type=InstallationMetadataCollector._package_type(filename, extension))
                )

            if is_script:
                script_res = scripts_analysis.get(file.absolute_path, ScriptAnalysisResult())
                installation_scripts.append(
                    InstallationScriptInfo(
                        metadata=metadata,
                        script_type=InstallationMetadataCollector._script_type(filename, extension),
                        referenced_config_files=script_res.configuration_files,
                        referenced_environment_files=script_res.referenced_environment_files,
                        copied_files=script_res.copied_files,
                        generated_files=script_res.generated_files,
                        installation_directories=script_res.created_directories,
                        referenced_executables=script_res.referenced_executables,
                        referenced_services=script_res.referenced_services,
                        commands=script_res.commands_run,
                    )
                )

            if is_config:
                config_res = configs_analysis.get(file.absolute_path)
                if config_res is not None:
                    configuration_files.append(
                        ConfigurationFileInfo(
                            metadata=metadata,
                            config_type=InstallationMetadataCollector._config_type(filename, extension),
                            sections=config_res.sections,
                            keys=config_res.keys,
                            values=config_res.raw_values,
                            referenced_paths=config_res.referenced_paths,
                            syntax_valid=config_res.syntax_valid,
                        )
                    )
                    final_environment_variables.update(InstallationMetadataCollector._extract_final_values(config_res))

            if is_template:
                config_res = configs_analysis.get(file.absolute_path)
                declared_vars = list(config_res.raw_values.keys()) if config_res else []
                template_values = InstallationMetadataCollector._extract_template_variables(config_res.raw_values if config_res else {})
                environment_templates.append(
                    EnvironmentTemplateInfo(
                        metadata=metadata,
                        template_type=InstallationMetadataCollector._template_type(filename, extension),
                        declared_variables=declared_vars,
                        values=template_values,
                    )
                )
                if config_res is not None:
                    final_environment_variables.update(InstallationMetadataCollector._extract_final_values(config_res))

            if is_generated:
                config_res = configs_analysis.get(file.absolute_path)
                generated_info = GeneratedFileInfo(
                    metadata=metadata,
                    generated_kind=InstallationMetadataCollector._generated_kind(filename, extension),
                    final_values=InstallationMetadataCollector._extract_final_values(config_res) if config_res else {},
                    source=InstallationMetadataCollector._generated_source(file.absolute_path, generated_targets),
                )
                generated_files.append(generated_info)
                if generated_info.generated_kind == "environment":
                    generated_environment_files.append(generated_info)
                else:
                    generated_configuration_files.append(generated_info)
                if config_res is not None:
                    final_environment_variables.update(InstallationMetadataCollector._extract_final_values(config_res))

        installation_metadata = InstallationMetadata(
            scanned_files=scan_results.total_files,
            total_size_bytes=scan_results.total_size_bytes,
            installation_packages_count=len(installation_packages),
            installation_scripts_count=len(installation_scripts),
            configuration_files_count=len(configuration_files),
            environment_templates_count=len(environment_templates),
            generated_configuration_files_count=len(generated_configuration_files),
            generated_environment_files_count=len(generated_environment_files),
            generated_files_count=len(generated_files),
            watchdog_events_count=len(watchdog_events),
            source_directories=[str(target_dir.resolve())],
            notes=InstallationMetadataCollector._build_notes(installation_packages, installation_scripts, generated_files, watchdog_events),
        )

        return MetadataCollection(
            installation_packages=installation_packages,
            installation_scripts=installation_scripts,
            configuration_files=configuration_files,
            environment_templates=environment_templates,
            generated_configuration_files=generated_configuration_files,
            generated_environment_files=generated_environment_files,
            final_environment_variables=final_environment_variables,
            generated_files=generated_files,
            installation_metadata=installation_metadata,
        )

    @staticmethod
    def _collect_generated_targets(scripts_analysis: Dict[str, ScriptAnalysisResult]) -> Set[str]:
        targets: Set[str] = set()
        for script_res in scripts_analysis.values():
            for generated in script_res.generated_files:
                targets.add(Path(generated).name.lower())
                targets.add(Path(generated).as_posix().lower())
            for copied in script_res.copied_files:
                parts = copied.split("->")
                if len(parts) == 2:
                    targets.add(Path(parts[1].strip()).name.lower())
                    targets.add(Path(parts[1].strip()).as_posix().lower())
        return targets

    @staticmethod
    def _generated_source(path: str, targets: Set[str]) -> str | None:
        name = Path(path).name.lower()
        if name in targets or Path(path).as_posix().lower() in targets:
            return "script-derived"
        return None

    @staticmethod
    def _is_package(filename: str, extension: str) -> bool:
        return filename in PACKAGE_NAMES or extension in PACKAGE_EXTENSIONS

    @staticmethod
    def _is_script(filename: str, extension: str) -> bool:
        return filename in PACKAGE_NAMES or extension in SCRIPT_EXTENSIONS

    @staticmethod
    def _is_config(filename: str, extension: str) -> bool:
        return extension in CONFIG_EXTENSIONS or filename in TEMPLATE_NAMES or filename in GENERATED_CONFIG_NAMES or filename in GENERATED_ENV_NAMES

    @staticmethod
    def _is_environment_template(filename: str, extension: str) -> bool:
        return filename in TEMPLATE_NAMES or filename.endswith(".env.template") or filename.endswith(".env.example")

    @staticmethod
    def _is_generated_file(filename: str, extension: str, generated_targets: Set[str]) -> bool:
        normalized = filename.lower()
        return normalized in GENERATED_CONFIG_NAMES or normalized in GENERATED_ENV_NAMES or normalized in generated_targets

    @staticmethod
    def _package_type(filename: str, extension: str) -> str:
        if extension == ".rpm":
            return "rpm-package"
        if extension == ".deb":
            return "deb-package"
        if extension == ".bin":
            return "binary-installer"
        if extension == ".msi":
            return "windows-msi"
        if filename.endswith(".exe"):
            return "windows-executable-installer"
        return "installer-package"

    @staticmethod
    def _script_type(filename: str, extension: str) -> str:
        if extension == ".ps1":
            return "powershell"
        if extension == ".bat":
            return "batch"
        if extension == ".service":
            return "systemd-service"
        return "shell"

    @staticmethod
    def _config_type(filename: str, extension: str) -> str:
        if extension in {".yaml", ".yml"}:
            return "yaml"
        if extension == ".json":
            return "json"
        if extension in {".xml", ".config"}:
            return "xml"
        if extension == ".ini":
            return "ini"
        if extension == ".properties":
            return "properties"
        if extension in {".conf", ".cfg"}:
            return "conf"
        if extension == ".reg":
            return "registry"
        return "configuration"

    @staticmethod
    def _template_type(filename: str, extension: str) -> str:
        if filename.endswith(".env.template") or filename.endswith(".env.example") or filename == ".env":
            return "environment-template"
        if filename == "environment.conf":
            return "environment-template"
        return "template"

    @staticmethod
    def _generated_kind(filename: str, extension: str) -> str:
        if filename in GENERATED_ENV_NAMES or filename.endswith(".env"):
            return "environment"
        return "configuration"

    @staticmethod
    def _extract_template_variables(values: Dict[str, Any]) -> Dict[str, str]:
        template_variables: Dict[str, str] = {}
        for key, value in values.items():
            value_str = str(value).strip()
            if value_str == "" or value_str in {"${VAR}", "${VALUE}", "<value>", "__PLACEHOLDER__"}:
                template_variables[key] = value_str
            elif value_str.startswith("${") or value_str.startswith("$"):
                template_variables[key] = value_str
        return template_variables

    @staticmethod
    def _extract_final_values(config_res: ConfigAnalysisResult | None) -> Dict[str, Any]:
        if config_res is None:
            return {}
        final_values: Dict[str, Any] = {}
        final_values.update(config_res.raw_values)
        final_values.update(config_res.env_vars)
        return final_values

    @staticmethod
    def _build_notes(
        installation_packages: List[InstallationPackageInfo],
        installation_scripts: List[InstallationScriptInfo],
        generated_files: List[GeneratedFileInfo],
        watchdog_events: List[WatchdogEvent],
    ) -> List[str]:
        notes: List[str] = []
        if installation_packages:
            notes.append(f"Detected {len(installation_packages)} installation packages.")
        if installation_scripts:
            notes.append(f"Detected {len(installation_scripts)} installation scripts.")
        if generated_files:
            notes.append(f"Detected {len(generated_files)} generated files.")
        if watchdog_events:
            notes.append(f"Captured {len(watchdog_events)} watchdog events.")
        return notes
