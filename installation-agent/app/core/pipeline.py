from datetime import datetime
from pathlib import Path
import logging
from app.config.settings import settings
from app.models.schemas import DeepAnalysisReport, ValidationReport
from app.services.scanner.file_scanner import FileScanner
from app.services.parser.script_parser import ScriptParser
from app.services.parser.config_parser import ConfigParser
from app.services.validators.syntax_validator import SyntaxValidator
from app.services.analyzer.installer_analyzer import InstallerAnalyzer
from app.services.graph.correlation_graph import CorrelationGraphBuilder
from app.services.reporting.report_generator import ReportGenerator
from app.services.analyzer.installation_metadata_collector import InstallationMetadataCollector
from app.watchers.event_store import get_watchdog_events
from app.core.file_classification import is_probable_config_file

logger = logging.getLogger("installation_agent")

def run_analysis_pipeline(target_dir: Path | None = None) -> DeepAnalysisReport:
    """
    Executes the full pipeline:
    1. Scan directory files and entrypoints.
    2. Validate syntax on configurations.
    3. Statically parse scripts for commands and dependencies.
    4. Validate cross-references.
    5. Build Package dependency graph (NetworkX) and correlation graph.
    6. Run risk calculations.
    7. Generate HTML/JSON/Markdown reports.
    """
    logger.info("=========================================")
    logger.info("Executing Pipeline Discovery & Correlation")
    logger.info("=========================================")
    
    # Resolve target directory
    resolved_target = target_dir or settings.get_absolute_path(settings.fake_files_dir)
    
    # 1. Scan directory
    scanner = FileScanner(resolved_target)
    scan_results = scanner.scan()
    
    # 2. Statically parse and validate files
    scripts_analysis = {}
    configs_analysis = {}
    validation_errors = []
    validation_warnings = []
    
    for f in scan_results.files:
        file_path = Path(f.absolute_path)
        ext = f.extension
        filename = file_path.name.lower()
        
        # Run syntax validation on each config file
        val_rep = SyntaxValidator.validate_file(file_path)
        validation_errors.extend(val_rep.errors)
        validation_warnings.extend(val_rep.warnings)
        
        # Parse scripts if script extension matched
        if ext in (".sh", ".ps1", ".bat", ".cmd", ".service") or filename.endswith(".service"):
            scripts_analysis[f.absolute_path] = ScriptParser.parse(file_path)
            
        # Parse configuration parameters. Extensible on purpose: real
        # deployments (e.g. Vermeg *.tokens files) use custom extensions a
        # fixed allowlist would never anticipate - see file_classification.
        is_config = is_probable_config_file(filename, ext)
        if is_config:
            configs_analysis[f.absolute_path] = ConfigParser.parse(file_path)
            
    # Check broken file references
    cross_ref_issues = SyntaxValidator.validate_cross_references(scan_results, scripts_analysis)
    validation_errors.extend(cross_ref_issues)
    
    # Construct complete validation report
    validation_report = ValidationReport(
        is_valid=len(validation_errors) == 0,
        errors=validation_errors,
        warnings=validation_warnings
    )
    
    # 3. Dependency and Correlation Graph Construction
    graph_builder = CorrelationGraphBuilder(scan_results)
    dep_graph = graph_builder.build_dependency_graph()
    correlation_graph = graph_builder.build_installation_correlation(scripts_analysis, configs_analysis)

    # 4. Collect installation metadata artifacts
    watchdog_events = get_watchdog_events()
    metadata_collection = InstallationMetadataCollector.collect(
        scan_results=scan_results,
        scripts_analysis=scripts_analysis,
        configs_analysis=configs_analysis,
        watchdog_events=watchdog_events,
        target_dir=resolved_target,
    )
    
    # 5. Risk Profile Score calculations (legacy compatibility only)
    risk_report = InstallerAnalyzer.analyze_risk(
        scan_results=scan_results,
        scripts_analysis=scripts_analysis,
        configs_analysis=configs_analysis,
        validation_report=validation_report
    )
    
    # 5. Compile Deep Analysis master response
    summary = {
        "scanned_files_count": scan_results.total_files,
        "entrypoints_count": len(scan_results.entrypoints),
        "dependency_nodes_count": len(dep_graph.nodes),
        "unsupported_runtimes_count": len(dep_graph.unsupported_versions),
        "validation_errors_count": len(validation_errors),
        "validation_warnings_count": len(validation_warnings),
        "risk_score": risk_report.score,
        "installation_packages_count": metadata_collection.installation_metadata.installation_packages_count,
        "installation_scripts_count": metadata_collection.installation_metadata.installation_scripts_count,
        "configuration_files_count": metadata_collection.installation_metadata.configuration_files_count,
        "generated_files_count": metadata_collection.installation_metadata.generated_files_count,
        "watchdog_events_count": metadata_collection.installation_metadata.watchdog_events_count,
    }
    
    report = DeepAnalysisReport(
        timestamp=datetime.utcnow().isoformat() + "Z",
        summary=summary,
        scan_results=scan_results,
        scripts_analysis=scripts_analysis,
        configs_analysis=configs_analysis,
        dependency_graph=dep_graph,
        validation_report=validation_report,
        risk_report=risk_report,
        correlation_graph=correlation_graph,
        installation_packages=metadata_collection.installation_packages,
        installation_scripts=metadata_collection.installation_scripts,
        configuration_files=metadata_collection.configuration_files,
        environment_templates=metadata_collection.environment_templates,
        generated_configuration_files=metadata_collection.generated_configuration_files,
        generated_environment_files=metadata_collection.generated_environment_files,
        final_environment_variables=metadata_collection.final_environment_variables,
        generated_files=metadata_collection.generated_files,
        watchdog_events=watchdog_events,
        installation_metadata=metadata_collection.installation_metadata,
    )
    
    # 6. Export report files
    ReportGenerator.generate(report)
    
    logger.info("Pipeline execution finished successfully.")
    logger.info("=========================================")
    return report
