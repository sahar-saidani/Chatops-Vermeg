import os
import sys
import time
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
load_dotenv()

# Ensure app path is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.core.logging_config import setup_logging
from app.core.pipeline import run_analysis_pipeline
from app.services.scanner.file_scanner import FileScanner
from app.services.validators.syntax_validator import SyntaxValidator
from app.services.analyzer.installer_analyzer import InstallerAnalyzer
from app.services.graph.correlation_graph import CorrelationGraphBuilder
from app.utils.fake_files_generator import FakeFilesGenerator
from app.watchers.file_watcher import InstallerWatcher
from app.config.machine_identity import MachineIdentity

# Initialize Typer
cli = typer.Typer(
    name="DevOps Discovery & Correlation Agent CLI",
    help="CLI tool to statically discover, parse, validate, and correlate deployment scripts and configurations."
)

console = Console()
logger = setup_logging(settings.log_level, settings.log_file)


@cli.callback(invoke_without_command=False)
def startup_banner() -> None:
    identity = MachineIdentity.from_env()
    logger.info("%s", identity.startup_banner("installation-agent", os.getenv("RABBITMQ_URL")))

@cli.command()
def generate_test_data(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target path to generate fake files in.")
):
    """Populates the fake_files/ directory with realistic mock deployment projects."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    console.print(f"[bold blue]Generating test configurations in: {target_path}[/bold blue]")
    try:
        FakeFilesGenerator.generate_all(target_path)
        console.print("[bold green]Success: Mock projects populated successfully.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed generating files: {e}[/bold red]")
        raise typer.Exit(code=1)

@cli.command()
def scan(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target folder to scan.")
):
    """Recursively scans target directory to index files, sizes, owners, and duplicates."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    console.print(f"[bold blue]Scanning directory: {target_path}[/bold blue]")
    
    scanner = FileScanner(target_path)
    results = scanner.scan()
    
    # Render table of files
    table = Table(title=f"Scanned Files ({len(results.files)} found)")
    table.add_column("Relative Path", style="cyan")
    table.add_column("Size (Bytes)", style="magenta", justify="right")
    table.add_column("Permissions", style="green")
    table.add_column("Owner", style="yellow")
    
    for f in results.files[:30]:  # limit display to first 30
        table.add_row(f.relative_path, str(f.size_bytes), f.permissions, f.owner)
        
    console.print(table)
    
    if len(results.files) > 30:
        console.print(f"... and {len(results.files) - 30} more files.")
        
    # Render duplicates
    if results.duplicates:
        console.print("\n[bold yellow]Duplicate files detected by SHA256 content hashes:[/bold yellow]")
        for h, paths in results.duplicates.items():
            console.print(f"Hash: [cyan]{h}[/cyan]")
            for p in paths:
                console.print(f" - {p}")
    else:
        console.print("\n[bold green]No duplicate files found.[/bold green]")

@cli.command()
def discover(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target folder to scan.")
):
    """Lists all detected installer entrypoint scripts within the directory."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    scanner = FileScanner(target_path)
    results = scanner.scan()
    
    if results.entrypoints:
        console.print(f"[bold green]Discovered {len(results.entrypoints)} installation entrypoints:[/bold green]")
        for entry in results.entrypoints:
            console.print(f" - [cyan]{entry}[/cyan]")
    else:
        console.print("[bold yellow]No installation entrypoints discovered.[/bold yellow]")

@cli.command()
def validate(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target folder to validate.")
):
    """Validates configuration files syntax (JSON, YAML, properties) and checks credentials."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    scanner = FileScanner(target_path)
    results = scanner.scan()
    
    errors_count = 0
    warnings_count = 0
    
    table = Table(title="Syntax & Credentials Validation Report")
    table.add_column("File", style="cyan")
    table.add_column("Status/Issue", style="yellow")
    table.add_column("Severity", style="magenta")
    
    for file in results.files:
        file_path = Path(file.absolute_path)
        val_rep = SyntaxValidator.validate_file(file_path)
        
        if val_rep.is_valid and not val_rep.warnings:
            table.add_row(file.relative_path, "[green]Valid[/green]", "-")
        else:
            for err in val_rep.errors:
                table.add_row(file.relative_path, f"[red]{err.message}[/red]", "ERROR")
                errors_count += 1
            for wrn in val_rep.warnings:
                table.add_row(file.relative_path, f"[yellow]{wrn.message}[/yellow]", "WARNING")
                warnings_count += 1
                
    console.print(table)
    console.print(f"\nValidation completed: [red]{errors_count} errors[/red], [yellow]{warnings_count} warnings[/yellow]")
    if errors_count > 0:
        raise typer.Exit(code=1)

@cli.command()
def analyze(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target folder to analyze.")
):
    """Performs full scan, parses files, and prints the structured installation metadata report."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    
    try:
        report = run_analysis_pipeline(target_path)

        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if rabbitmq_url:
            from rabbitmq_publisher import RabbitMqPublisher

            identity = MachineIdentity.from_env()
            publisher = RabbitMqPublisher(url=rabbitmq_url)
            publisher.publish(agent_key="installation", data=report.model_dump(mode="json"), identity=identity)
            logger.info("Message successfully published.")

        metadata = report.installation_metadata
        panel_content = (
            f"Scanned files: [bold]{metadata.scanned_files}[/bold]\n"
            f"Installation packages: [bold]{metadata.installation_packages_count}[/bold]\n"
            f"Installation scripts: [bold]{metadata.installation_scripts_count}[/bold]\n"
            f"Configuration files: [bold]{metadata.configuration_files_count}[/bold]\n"
            f"Environment templates: [bold]{metadata.environment_templates_count}[/bold]\n"
            f"Generated files: [bold]{metadata.generated_files_count}[/bold]\n"
            f"Watchdog events: [bold]{metadata.watchdog_events_count}[/bold]\n"
            f"Final environment variables: [bold]{len(report.final_environment_variables)}[/bold]\n"
            f"Risk Score (legacy): [bold]{report.risk_report.score}/100[/bold]"
        )
        console.print(Panel(panel_content, title="Installation Metadata Summary", border_style="blue"))

        if report.final_environment_variables:
            console.print("\n[bold blue]Final Environment Variables:[/bold blue]")
            for key, value in sorted(report.final_environment_variables.items()):
                console.print(f" - [cyan]{key}[/cyan] = {value}")

        if metadata.notes:
            console.print("\n[bold blue]Metadata Notes:[/bold blue]")
            for note in metadata.notes:
                console.print(f" - {note}")
            
    except Exception as e:
        console.print(f"[bold red]Pipeline error: {e}[/bold red]")
        raise typer.Exit(code=1)

@cli.command()
def graph():
    """Prints dependencies tree and file correlation mappings."""
    try:
        report = run_analysis_pipeline()
        
        console.print("[bold blue]Discovered Package Dependencies Graph:[/bold blue]")
        dg = report.dependency_graph
        if dg.nodes:
            for node in dg.nodes:
                console.print(f" - [cyan]{node.name}@{node.version}[/cyan] (Defined in: {Path(node.source_file).name})")
        else:
            console.print(" - No packages indexed.")
            
        console.print("\n[bold blue]File Correlation Linkage Map:[/bold blue]")
        if report.correlation_graph:
            for source, targets in report.correlation_graph.items():
                s_name = Path(source).name
                console.print(f" - [green]{s_name}[/green]")
                for t in targets:
                    console.print(f"   └──> [cyan]{Path(t).name}[/cyan]")
        else:
            console.print(" - No linkages determined.")
    except Exception as e:
        console.print(f"[bold red]Graph resolution failed: {e}[/bold red]")
        raise typer.Exit(code=1)

@cli.command()
def watch(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Target folder to monitor.")
):
    """Launches directory Watchdog monitoring target changes in real-time."""
    target_path = Path(path) if path else settings.get_absolute_path(settings.fake_files_dir)
    watcher = InstallerWatcher(target_path)
    
    console.print(f"[bold blue]Starting File Watcher on: {target_path}[/bold blue]")
    console.print("[bold yellow]Press Ctrl+C to terminate.[/bold yellow]")
    
    try:
        watcher.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold red]Stopping file watcher...[/bold red]")
        watcher.stop()
    except Exception as e:
        console.print(f"[bold red]Watcher error: {e}[/bold red]")

@cli.command()
def report():
    """Lists current generated reports inside the output directory."""
    reports_dir = settings.get_absolute_path(settings.reports_dir)
    if not reports_dir.exists():
        console.print("[bold yellow]No reports directory found. Run 'analyze' first.[/bold yellow]")
        return
        
    console.print(f"[bold blue]Inventory of generated reports in: {reports_dir}[/bold blue]")
    for file in reports_dir.glob("*"):
        if file.is_file():
            size = file.stat().st_size
            console.print(f" - [cyan]{file.name}[/cyan] ({size} bytes)")

@cli.command()
def status():
    """Prints current directories configuration and log levels."""
    console.print(Panel(
        f"Workspace Path: {settings.workspace_dir}\n"
        f"Simulated Files Folder: {settings.get_absolute_path(settings.fake_files_dir)}\n"
        f"Reports Export Folder: {settings.get_absolute_path(settings.reports_dir)}\n"
        f"Logging level: {settings.log_level}\n"
        f"Log file location: {settings.get_absolute_path(settings.log_file)}",
        title="Discovery Agent Status Checks"
    ))

if __name__ == "__main__":
    cli()
