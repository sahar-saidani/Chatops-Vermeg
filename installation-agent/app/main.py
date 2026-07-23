import os
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from app.config.settings import settings
from app.core.logging_config import setup_logging
from app.core.pipeline import run_analysis_pipeline
from app.services.scanner.file_scanner import FileScanner
from app.services.validators.syntax_validator import SyntaxValidator
from app.models.schemas import ScanResults, ValidationReport, DeepAnalysisReport

# Setup logger before initializing app
logger = setup_logging(settings.log_level, settings.log_file)

app = FastAPI(
    title="DevOps Installation Discovery & Correlation Agent API",
    description="A microservice for discovery, parsing, validation, and risk analysis of installation artifacts.",
    version="1.0.0"
)

# Request schemas
class ScanRequest(BaseModel):
    path: Optional[str] = None

class AnalyzeRequest(BaseModel):
    path: Optional[str] = None

class ValidateRequest(BaseModel):
    path: Optional[str] = None

@app.post("/scan", response_model=ScanResults, tags=["Scanner"])
def scan_directory(request: Optional[ScanRequest] = None):
    """Recursively scans a target path for installer files, computing size, owners, and hashes."""
    target_path = None
    if request and request.path:
        target_path = Path(request.path)
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Target path '{request.path}' not found.")
            
    try:
        scanner = FileScanner(target_path)
        return scanner.scan()
    except Exception as e:
        logger.exception("Error during manual API scan")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/discover", tags=["Scanner"])
def discover_entrypoints(request: Optional[ScanRequest] = None):
    """Identifies deployment entrypoints (like install.sh, setup.exe, install.ps1) within the target path."""
    target_path = None
    if request and request.path:
        target_path = Path(request.path)
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Target path '{request.path}' not found.")
            
    try:
        scanner = FileScanner(target_path)
        results = scanner.scan()
        return {"entrypoints": results.entrypoints}
    except Exception as e:
        logger.exception("Error during manual API entrypoint discovery")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=DeepAnalysisReport, tags=["Analyzer"])
def analyze_project(request: Optional[AnalyzeRequest] = None):
    """Executes the full pipeline: scans target, parses configuration/scripts, maps dependency trees, and scores risks."""
    target_path = None
    if request and request.path:
        target_path = Path(request.path)
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Target path '{request.path}' not found.")
            
    try:
        return run_analysis_pipeline(target_path)
    except Exception as e:
        logger.exception("Error during API pipeline execution")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=ValidationReport, tags=["Validator"])
def validate_configurations(request: Optional[ValidateRequest] = None):
    """Performs individual file syntax validations (YAML, properties, JSON) and flags duplicate keys."""
    target_path = None
    if request and request.path:
        target_path = Path(request.path)
    else:
        target_path = settings.get_absolute_path(settings.fake_files_dir)
        
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Target path '{target_path}' not found.")
        
    try:
        scanner = FileScanner(target_path)
        results = scanner.scan()
        
        errors = []
        warnings = []
        
        for file in results.files:
            file_path = Path(file.absolute_path)
            val_rep = SyntaxValidator.validate_file(file_path)
            errors.extend(val_rep.errors)
            warnings.extend(val_rep.warnings)
            
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    except Exception as e:
        logger.exception("Error during API file validation")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph", tags=["Correlation"])
def get_correlation_graphs():
    """Generates and returns the latest package dependency tree and file correlation mappings."""
    try:
        # Run analysis to fetch latest graph
        report = run_analysis_pipeline()
        return {
            "dependencies": report.dependency_graph.model_dump(),
            "file_correlation": report.correlation_graph
        }
    except Exception as e:
        logger.exception("Error generating graphs")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports", tags=["Reporting"])
def get_reports_inventory():
    """Returns absolute paths and content summaries of generated JSON, Markdown, and HTML reports."""
    reports_dir = settings.get_absolute_path(settings.reports_dir)
    if not reports_dir.exists():
        return {"reports": []}
        
    inventory = []
    try:
        for file in reports_dir.glob("*"):
            if file.is_file():
                inventory.append({
                    "name": file.name,
                    "extension": file.suffix,
                    "size_bytes": file.stat().st_size,
                    "absolute_path": file.resolve().as_posix()
                })
        return {"reports": inventory}
    except Exception as e:
        logger.exception("Error scanning reports directory")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", tags=["System"])
def get_system_status():
    """Returns agent service health checks, logging paths, and target directories."""
    return {
        "status": "HEALTHY",
        "agent": "DevOps Installation Discovery & Correlation Agent",
        "version": "1.0.0",
        "workspace": Path(settings.workspace_dir).as_posix(),
        "fake_files_directory": Path(settings.get_absolute_path(settings.fake_files_dir)).as_posix(),
        "logs_path": Path(settings.get_absolute_path(settings.log_file)).as_posix()
    }
