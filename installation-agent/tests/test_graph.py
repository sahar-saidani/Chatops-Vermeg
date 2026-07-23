import pytest
from pathlib import Path
from app.services.scanner.file_scanner import FileScanner
from app.services.graph.correlation_graph import CorrelationGraphBuilder
from app.models.schemas import ScriptAnalysisResult, ConfigAnalysisResult

def test_correlation_graph_builder():
    scanner = FileScanner()
    scan_res = scanner.scan()
    
    builder = CorrelationGraphBuilder(scan_res)
    dep_model = builder.build_dependency_graph()
    
    # Assertions on package dependencies
    assert len(dep_model.nodes) > 0
    package_names = {node.name for node in dep_model.nodes}
    assert "fastapi" in package_names
    assert "express" in package_names
    
    # Verify version conflicts check (e.g. mock conflict check)
    # requirements.txt has urllib3, base image has other etc.
    # Check that unsupported runtimes is loaded (e.g. node 16 is old (<18))
    assert len(dep_model.unsupported_versions) > 0
    assert any("node" in v.lower() for v in dep_model.unsupported_versions)

def test_installation_file_correlations():
    scanner = FileScanner()
    scan_res = scanner.scan()
    
    # Resolve actual paths from scan registry
    start_sh_path = None
    env_path = None
    yml_path = None
    for f in scan_res.files:
        if f.filename == "start.sh":
            start_sh_path = f.absolute_path
        elif f.filename == ".env":
            env_path = f.absolute_path
        elif f.filename == "application.yml":
            yml_path = f.absolute_path
            
    assert start_sh_path is not None
    assert env_path is not None
    assert yml_path is not None
    
    builder = CorrelationGraphBuilder(scan_res)
    
    # Provide simple script and config parses linked to actual workspace paths
    mock_scripts = {
        start_sh_path: ScriptAnalysisResult(referenced_files=[env_path, yml_path])
    }
    mock_configs = {
        env_path: ConfigAnalysisResult(raw_values={"PORT": "8000"}),
        yml_path: ConfigAnalysisResult(raw_values={"server.port": 8000})
    }
    
    # Run builder - it should find matched files from scanned registry
    adj = builder.build_installation_correlation(mock_scripts, mock_configs)
    
    assert start_sh_path in adj
    linked_names = {Path(f).name for f in adj[start_sh_path]}
    assert ".env" in linked_names
    assert "application.yml" in linked_names
