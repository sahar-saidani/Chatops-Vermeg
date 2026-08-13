from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple

class FileMetadata(BaseModel):
    """Metadata of a scanned file."""
    absolute_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    creation_date: str
    modification_date: str
    sha256: str
    md5: str
    mime_type: str
    permissions: str
    owner: str
    is_symlink: bool


class InstallationPackageInfo(BaseModel):
    """Installer package metadata discovered during scanning."""
    metadata: FileMetadata
    package_type: str


class InstallationScriptInfo(BaseModel):
    """Static metadata extracted from installation scripts."""
    metadata: FileMetadata
    script_type: str
    referenced_config_files: List[str] = Field(default_factory=list)
    referenced_environment_files: List[str] = Field(default_factory=list)
    copied_files: List[str] = Field(default_factory=list)
    generated_files: List[str] = Field(default_factory=list)
    installation_directories: List[str] = Field(default_factory=list)
    referenced_executables: List[str] = Field(default_factory=list)
    referenced_services: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)


class ConfigurationFileInfo(BaseModel):
    """Parsed configuration file metadata and extracted values."""
    metadata: FileMetadata
    config_type: str
    sections: List[str] = Field(default_factory=list)
    keys: List[str] = Field(default_factory=list)
    values: Dict[str, Any] = Field(default_factory=dict)
    referenced_paths: List[str] = Field(default_factory=list)
    syntax_valid: bool = True


class EnvironmentTemplateInfo(BaseModel):
    """Environment template definitions and declared variables."""
    metadata: FileMetadata
    template_type: str
    declared_variables: List[str] = Field(default_factory=list)
    values: Dict[str, str] = Field(default_factory=dict)


class GeneratedFileInfo(BaseModel):
    """Generated installation artifact metadata."""
    metadata: FileMetadata
    generated_kind: str
    final_values: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


class WatchdogEvent(BaseModel):
    """Filesystem event captured while installation artifacts change."""
    timestamp: str
    event_type: str
    path: str
    is_directory: bool = False


class InstallationMetadata(BaseModel):
    """Aggregated installation metadata summary."""
    scanned_files: int = 0
    total_size_bytes: int = 0
    installation_packages_count: int = 0
    installation_scripts_count: int = 0
    configuration_files_count: int = 0
    environment_templates_count: int = 0
    generated_configuration_files_count: int = 0
    generated_environment_files_count: int = 0
    generated_files_count: int = 0
    watchdog_events_count: int = 0
    source_directories: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class ScanResults(BaseModel):
    """Full directory scan results."""
    timestamp: str
    total_files: int
    total_size_bytes: int
    files: List[FileMetadata] = Field(default_factory=list)
    duplicates: Dict[str, List[str]] = Field(default_factory=dict)  # SHA256 -> list of absolute paths
    entrypoints: List[str] = Field(default_factory=list)  # list of absolute paths
    # True when a scan bound (depth, file count or time budget) cut the walk
    # short. Consumers must not read a truncated scan as "this is everything".
    truncated: bool = False
    truncation_reason: Optional[str] = None

class ScriptAnalysisResult(BaseModel):
    """Results from parsing shell, powershell, or batch scripts."""
    referenced_files: List[str] = Field(default_factory=list)
    copied_files: List[str] = Field(default_factory=list)
    created_directories: List[str] = Field(default_factory=list)
    generated_files: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    executed_binaries: List[str] = Field(default_factory=list)
    configuration_files: List[str] = Field(default_factory=list)
    referenced_environment_files: List[str] = Field(default_factory=list)
    referenced_executables: List[str] = Field(default_factory=list)
    referenced_services: List[str] = Field(default_factory=list)
    docker_commands: List[str] = Field(default_factory=list)
    systemctl_commands: List[str] = Field(default_factory=list)
    service_creation: List[str] = Field(default_factory=list)
    commands_run: List[str] = Field(default_factory=list)

class ConfigAnalysisResult(BaseModel):
    """Extracted data from parsed configurations (env, yaml, json, etc.)."""
    application_name: Optional[str] = None
    version: Optional[str] = None
    ports: List[int] = Field(default_factory=list)
    database_host: Optional[str] = None
    database_port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    api_urls: List[str] = Field(default_factory=list)
    filesystem_paths: List[str] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    mounts: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    logging_configuration: Dict[str, str] = Field(default_factory=dict)
    security_settings: Dict[str, str] = Field(default_factory=dict)
    docker_images: List[str] = Field(default_factory=list)
    kubernetes_resources: List[str] = Field(default_factory=list)
    raw_values: Dict[str, Any] = Field(default_factory=dict)
    sections: List[str] = Field(default_factory=list)
    keys: List[str] = Field(default_factory=list)
    referenced_paths: List[str] = Field(default_factory=list)
    syntax_valid: bool = True

class DependencyNode(BaseModel):
    """Single dependency node details."""
    name: str
    version: str
    source_file: str

class DependencyGraphModel(BaseModel):
    """Serialized networkx dependency graph structure and analysis."""
    nodes: List[DependencyNode] = Field(default_factory=list)
    edges: List[Tuple[str, str]] = Field(default_factory=list) # parent, child
    missing_dependencies: List[str] = Field(default_factory=list)
    duplicate_dependencies: List[str] = Field(default_factory=list)
    version_conflicts: Dict[str, List[str]] = Field(default_factory=dict) # pkg_name -> versions
    unsupported_versions: List[str] = Field(default_factory=list)

class ValidationErrorItem(BaseModel):
    """Validation issue details."""
    file_path: str
    type: str # e.g. syntax, duplicate_key, missing_variable, broken_reference, integrity
    message: str
    severity: str # error, warning

class ValidationReport(BaseModel):
    """Syntax and sanity validation reports."""
    is_valid: bool
    errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationErrorItem] = Field(default_factory=list)

class RiskScoreCard(BaseModel):
    """Details of the security & operational risk assessment."""
    score: int # 0 - 100
    risk_factors: List[str] = Field(default_factory=list)
    reasons: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class DeepAnalysisReport(BaseModel):
    """The master installation report aggregating everything discovered."""
    timestamp: str
    summary: Dict[str, Any]
    scan_results: ScanResults
    scripts_analysis: Dict[str, ScriptAnalysisResult] = Field(default_factory=dict)
    configs_analysis: Dict[str, ConfigAnalysisResult] = Field(default_factory=dict)
    dependency_graph: DependencyGraphModel
    validation_report: ValidationReport
    risk_report: RiskScoreCard
    correlation_graph: Dict[str, List[str]] = Field(default_factory=dict) # file -> linked files
    installation_packages: List[InstallationPackageInfo] = Field(default_factory=list)
    installation_scripts: List[InstallationScriptInfo] = Field(default_factory=list)
    configuration_files: List[ConfigurationFileInfo] = Field(default_factory=list)
    environment_templates: List[EnvironmentTemplateInfo] = Field(default_factory=list)
    generated_configuration_files: List[GeneratedFileInfo] = Field(default_factory=list)
    generated_environment_files: List[GeneratedFileInfo] = Field(default_factory=list)
    final_environment_variables: Dict[str, Any] = Field(default_factory=dict)
    generated_files: List[GeneratedFileInfo] = Field(default_factory=list)
    watchdog_events: List[WatchdogEvent] = Field(default_factory=list)
    installation_metadata: InstallationMetadata = Field(default_factory=InstallationMetadata)
