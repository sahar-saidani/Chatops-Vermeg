import re
import json
import yaml
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple
import networkx as nx
from app.models.schemas import (
    DependencyNode, 
    DependencyGraphModel, 
    ScanResults, 
    ScriptAnalysisResult,
    ConfigAnalysisResult
)

logger = logging.getLogger("installation_agent")

class CorrelationGraphBuilder:
    """Discovers package dependencies and builds relationship correlation graphs using NetworkX."""
    
    def __init__(self, scan_results: ScanResults):
        self.scan_results = scan_results
        self.dep_graph = nx.DiGraph()
        self.file_graph = nx.DiGraph()

    def build_dependency_graph(self) -> DependencyGraphModel:
        """Parses packages, Docker files, and config files to build a dependency model."""
        nodes = []
        edges = []
        duplicate_dependencies = []
        version_conflicts = {}
        unsupported_versions = []
        missing_dependencies = []
        
        seen_packages = {}  # pkg_name -> list of (version, source_file)
        
        # Traverse scan results and parse dependencies
        for file in self.scan_results.files:
            file_path = Path(file.absolute_path)
            filename = file_path.name.lower()
            
            if filename == "requirements.txt":
                self._parse_requirements(file_path, seen_packages)
            elif filename == "package.json":
                self._parse_package_json(file_path, seen_packages)
            elif filename == "pom.xml":
                self._parse_pom_xml(file_path, seen_packages)
            elif filename == "build.gradle":
                self._parse_build_gradle(file_path, seen_packages)
            elif filename == "environment.yml" or filename == "environment.yaml":
                self._parse_environment_yml(file_path, seen_packages)
            elif filename == "dockerfile" or file.extension == ".dockerfile":
                self._parse_dockerfile(file_path, seen_packages)
            elif filename == "docker-compose.yml" or filename == "docker-compose.yaml":
                self._parse_docker_compose_images(file_path, seen_packages)
                
        # Register nodes in NetworkX Graph and search for conflicts/duplicates
        for pkg_name, occurrences in seen_packages.items():
            versions = {occ[0] for occ in occurrences}
            
            # Duplicates check (same package defined multiple times, even with same version)
            if len(occurrences) > 1:
                duplicate_dependencies.append(pkg_name)
                
            # Version conflict check (different versions found)
            if len(versions) > 1:
                version_conflicts[pkg_name] = list(versions)
                
            # Register occurrences as nodes
            for version, src in occurrences:
                node_id = f"{pkg_name}@{version}"
                nodes.append(DependencyNode(name=pkg_name, version=version, source_file=src))
                self.dep_graph.add_node(node_id, name=pkg_name, version=version, source=src)
                
                # Check for outdated / unsupported versions (simulated)
                self._check_unsupported_runtimes(pkg_name, version, src, unsupported_versions)
                
        # Create mock edges representing dependency trees
        # In a real environment, we'd query registers, but we can simulate parent-child edges based on file links
        # For example, docker-compose depends on Dockerfile base images
        for node1 in self.dep_graph.nodes:
            for node2 in self.dep_graph.nodes:
                # Dockerfile packages depend on base image
                if "dockerfile" in self.dep_graph.nodes[node1]['source'].lower() and "base-image" in node2.lower():
                    self.dep_graph.add_edge(node2, node1)
                    edges.append((node2, node1))

        # Check for missing dependencies
        # Example: Dockerfile contains python but requirements.txt is absent, or vice versa
        has_requirements = any("requirements.txt" in f.filename for f in self.scan_results.files)
        has_python_runtime = any("python" in k for k in seen_packages.keys())
        if has_python_runtime and not has_requirements:
            missing_dependencies.append("Python dependencies (requirements.txt missing for Python runtime)")
            
        has_package_json = any("package.json" in f.filename for f in self.scan_results.files)
        has_node_runtime = any("node" in k or "npm" in k for k in seen_packages.keys())
        if has_node_runtime and not has_package_json:
            missing_dependencies.append("Node.js dependencies (package.json missing for Node runtime)")

        return DependencyGraphModel(
            nodes=nodes,
            edges=edges,
            missing_dependencies=missing_dependencies,
            duplicate_dependencies=duplicate_dependencies,
            version_conflicts=version_conflicts,
            unsupported_versions=unsupported_versions
        )

    def build_installation_correlation(
        self, 
        scripts_analysis: Dict[str, ScriptAnalysisResult],
        configs_analysis: Dict[str, ConfigAnalysisResult]
    ) -> Dict[str, List[str]]:
        """Constructs and returns the Installation Correlation file reference map in memory."""
        # Reset NetworkX file correlation graph
        self.file_graph.clear()
        
        # Populate all files as nodes
        for f in self.scan_results.files:
            self.file_graph.add_node(f.absolute_path, name=f.filename, type="file")
            
        # Correlate files
        for file in self.scan_results.files:
            file_path = Path(file.absolute_path)
            filename = file_path.name.lower()
            abs_path = file.absolute_path
            
            # Script correlations
            if abs_path in scripts_analysis:
                analysis = scripts_analysis[abs_path]
                for ref_file in analysis.referenced_files:
                    target_path = self._find_scanned_file_path(ref_file)
                    if target_path:
                        self.file_graph.add_edge(abs_path, target_path, relation="references")
                        
            # Configuration correlations
            if abs_path in configs_analysis:
                analysis = configs_analysis[abs_path]
                # If a config references other files (e.g. docker-compose referencing env_file or Dockerfile)
                if filename in ("docker-compose.yml", "docker-compose.yaml"):
                    # links to .env or Dockerfile
                    for env_file in (".env", ".env.example", "Dockerfile"):
                        target_path = self._find_scanned_file_path(env_file)
                        if target_path:
                            self.file_graph.add_edge(abs_path, target_path, relation="configures")
                # Look inside raw values for file paths
                for val in analysis.raw_values.values():
                    val_str = str(val)
                    if "/" in val_str or "\\" in val_str:
                        target_path = self._find_scanned_file_path(Path(val_str).name)
                        if target_path:
                            self.file_graph.add_edge(abs_path, target_path, relation="points_to")
                            
        # Export as a simple adjacency list: source_path -> list of target_paths
        adjacency_dict = {}
        for node in self.file_graph.nodes:
            successors = list(self.file_graph.successors(node))
            if successors:
                adjacency_dict[node] = successors
        return adjacency_dict

    def _find_scanned_file_path(self, filename: str) -> str | None:
        """Helper to find the absolute path of a filename from the scan registry."""
        cleaned_name = Path(filename).name.lower()
        for f in self.scan_results.files:
            if f.filename.lower() == cleaned_name:
                return f.absolute_path
        return None

    def _parse_requirements(self, file_path: Path, seen: dict):
        try:
            content = file_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Split by operators
                parts = re.split(r'==|>=|<=|>|<|~=', line)
                pkg = parts[0].strip().lower()
                version = parts[1].strip() if len(parts) > 1 else "latest"
                seen.setdefault(pkg, []).append((version, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing requirements.txt at {file_path}: {e}")

    def _parse_package_json(self, file_path: Path, seen: dict):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            for dep_key in ("dependencies", "devDependencies"):
                if dep_key in data and isinstance(data[dep_key], dict):
                    for pkg, ver in data[dep_key].items():
                        cleaned_ver = str(ver).replace("^", "").replace("~", "")
                        seen.setdefault(pkg.lower(), []).append((cleaned_ver, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing package.json at {file_path}: {e}")

    def _parse_pom_xml(self, file_path: Path, seen: dict):
        try:
            content = file_path.read_text(encoding="utf-8")
            root = ET.fromstring(content)
            # Find dependencies namespace agnostically
            for elem in root.iter():
                if "dependency" in elem.tag.lower():
                    groupId = ""
                    artifactId = ""
                    version = "managed"
                    for child in elem:
                        tag = child.tag.lower()
                        if "groupid" in tag:
                            groupId = child.text.strip() if child.text else ""
                        elif "artifactid" in tag:
                            artifactId = child.text.strip() if child.text else ""
                        elif "version" in tag:
                            version = child.text.strip() if child.text else "managed"
                    if groupId and artifactId:
                        pkg = f"{groupId}:{artifactId}"
                        seen.setdefault(pkg, []).append((version, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing pom.xml at {file_path}: {e}")

    def _parse_build_gradle(self, file_path: Path, seen: dict):
        try:
            content = file_path.read_text(encoding="utf-8")
            # Parse lines like implementation 'group:name:version'
            matches = re.findall(r'\b(?:implementation|compile|api)\s+[\'"]([^\'"]+)[\'"]', content)
            for match in matches:
                parts = match.split(":")
                if len(parts) >= 2:
                    pkg = f"{parts[0]}:{parts[1]}"
                    version = parts[2] if len(parts) > 2 else "latest"
                    seen.setdefault(pkg, []).append((version, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing build.gradle at {file_path}: {e}")

    def _parse_environment_yml(self, file_path: Path, seen: dict):
        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "dependencies" in data:
                for dep in data["dependencies"]:
                    if isinstance(dep, str):
                        parts = dep.split("=")
                        pkg = parts[0].strip()
                        version = parts[1].strip() if len(parts) > 1 else "latest"
                        seen.setdefault(pkg, []).append((version, str(file_path)))
                    elif isinstance(dep, dict) and "pip" in dep:
                        for pip_dep in dep["pip"]:
                            parts = re.split(r'==|>=|<=|>|<|~=', pip_dep)
                            pkg = parts[0].strip().lower()
                            version = parts[1].strip() if len(parts) > 1 else "latest"
                            seen.setdefault(pkg, []).append((version, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing environment.yml at {file_path}: {e}")

    def _parse_dockerfile(self, file_path: Path, seen: dict):
        try:
            content = file_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().upper().startswith("FROM "):
                    parts = line.strip().split()
                    if len(parts) > 1:
                        img = parts[1]
                        img_parts = img.split(":")
                        img_name = img_parts[0]
                        img_ver = img_parts[1] if len(img_parts) > 1 else "latest"
                        seen.setdefault(f"base-image:{img_name}", []).append((img_ver, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing Dockerfile at {file_path}: {e}")

    def _parse_docker_compose_images(self, file_path: Path, seen: dict):
        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "services" in data:
                for svc, config in data["services"].items():
                    if isinstance(config, dict) and "image" in config:
                        img = str(config["image"])
                        img_parts = img.split(":")
                        img_name = img_parts[0]
                        img_ver = img_parts[1] if len(img_parts) > 1 else "latest"
                        seen.setdefault(f"docker-image:{img_name}", []).append((img_ver, str(file_path)))
        except Exception as e:
            logger.warning(f"Failed parsing docker-compose at {file_path}: {e}")

    def _check_unsupported_runtimes(self, name: str, version: str, src: str, unsupported: list):
        """Simulates checking runtime and library versions against unsupported thresholds."""
        # Match python
        if "python" in name.lower() or "base-image:python" in name.lower():
            # Check version
            ver_match = re.search(r'\b\d+\.\d+\b', version)
            if ver_match:
                v = float(ver_match.group(0))
                if v < 3.10:
                    unsupported.append(f"Python version {version} in {Path(src).name} is unsupported. Minimum required is 3.10.")
        # Match node
        if "node" in name.lower() or "base-image:node" in name.lower():
            ver_match = re.search(r'\b\d+\b', version)
            if ver_match:
                v = int(ver_match.group(0))
                if v < 18:
                    unsupported.append(f"Node.js version {version} in {Path(src).name} is unsupported. Minimum required is 18.")
        # Match postgres
        if "postgres" in name.lower() or "docker-image:postgres" in name.lower():
            ver_match = re.search(r'\b\d+\b', version)
            if ver_match:
                v = int(ver_match.group(0))
                if v < 13:
                    unsupported.append(f"PostgreSQL version {version} in {Path(src).name} is unsupported. Minimum required is 13.")
