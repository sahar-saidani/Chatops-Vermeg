import re
import logging
from pathlib import Path
from app.models.schemas import ScriptAnalysisResult

logger = logging.getLogger("installation_agent")

class ScriptParser:
    """Statically parses shell scripts, PowerShell scripts, and batch files without executing them."""
    
    @staticmethod
    def parse(file_path: Path) -> ScriptAnalysisResult:
        logger.info(f"Parsing script statically: {file_path}")
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error reading script file {file_path}: {e}")
            return ScriptAnalysisResult()
            
        referenced_files = set()
        copied_files = []
        created_directories = []
        generated_files = []
        env_vars = {}
        executed_binaries = set()
        configuration_files = set()
        referenced_environment_files = set()
        referenced_executables = set()
        referenced_services = set()
        docker_commands = []
        systemctl_commands = []
        service_creation = []
        commands_run = []
        
        lines = content.splitlines()
        
        # Regex patterns
        config_file_pattern = re.compile(
            r'([a-zA-Z0-9_\-\.\/]+\.(?:env|properties|yaml|yml|json|ini|conf|config|reg|service))', 
            re.IGNORECASE
        )
        cp_pattern_bash = re.compile(r'\bcp\s+([^\s]+)\s+([^\s]+)')
        cp_pattern_ps = re.compile(r'\bCopy-Item\s+(?:-Path\s+)?([^\s]+)\s+(?:-Destination\s+)?([^\s]+)', re.IGNORECASE)
        redirect_pattern = re.compile(r'(?:>\s*|Set-Content\s+|Out-File\s+|tee\s+)([A-Za-z0-9_\-\./\\]+\.(?:env|properties|yaml|yml|json|ini|conf|cfg|xml|txt|service))', re.IGNORECASE)
        touch_pattern = re.compile(r'\b(?:touch|New-Item)\b.*?([A-Za-z0-9_\-\./\\]+\.(?:env|properties|yaml|yml|json|ini|conf|cfg|xml|txt|service))', re.IGNORECASE)
        install_dir_pattern = re.compile(r'\b(?:/opt/[^\s;]+|/usr/local/[^\s;]+|/etc/[^\s;]+|[A-Za-z]:\\[^\s;]+)')
        
        mkdir_pattern_bash = re.compile(r'\bmkdir\s+(?:-p\s+)?([^\s;]+)')
        mkdir_pattern_ps = re.compile(r'\bNew-Item\s+.*-ItemType\s+["\']?Directory["\']?.*-Path\s+([^\s;]+)', re.IGNORECASE)
        
        env_pattern_bash = re.compile(r'\b(?:export\s+)?([a-zA-Z_0-9]+)=[\'"]?([^\'"\s;&\n]+)[\'"]?')
        env_pattern_ps = re.compile(r'\$env:([a-zA-Z_0-9]+)\s*=\s*[\'"]?([^\s;\'"\n]+)[\'"]?', re.IGNORECASE)
        
        binaries_to_check = [
            "python", "node", "npm", "pip", "docker", "docker-compose", 
            "kubectl", "java", "systemctl", "yarn", "pnpm", "dotnet", 
            "chmod", "curl", "wget", "tar", "unzip", "bash", "sh", "powershell", "pwsh"
        ]
        
        for line in lines:
            line_stripped = line.strip()
            # Ignore comment lines
            if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('::') or line_stripped.startswith('//'):
                continue
                
            # Configuration file references
            for match in config_file_pattern.findall(line_stripped):
                configuration_files.add(Path(match).name)
                referenced_files.add(match)
                if Path(match).suffix.lower() in {".env", ".example"} or ".env" in Path(match).name.lower():
                    referenced_environment_files.add(match)
                
            # Copied files detection
            cp_bash = cp_pattern_bash.search(line_stripped)
            if cp_bash:
                copied_files.append(f"{cp_bash.group(1)} -> {cp_bash.group(2)}")
                referenced_files.add(cp_bash.group(1))
                referenced_files.add(cp_bash.group(2))
            cp_ps = cp_pattern_ps.search(line_stripped)
            if cp_ps:
                copied_files.append(f"{cp_ps.group(1)} -> {cp_ps.group(2)}")
                referenced_files.add(cp_ps.group(1))
                referenced_files.add(cp_ps.group(2))

            # Generated file detection
            for generated_match in redirect_pattern.findall(line_stripped):
                generated_files.append(generated_match)
                referenced_files.add(generated_match)
            for generated_match in touch_pattern.findall(line_stripped):
                generated_files.append(generated_match)
                referenced_files.add(generated_match)
                
            # Directory creations detection
            mkdir_bash = mkdir_pattern_bash.search(line_stripped)
            if mkdir_bash:
                created_directories.append(mkdir_bash.group(1))
            mkdir_ps = mkdir_pattern_ps.search(line_stripped)
            if mkdir_ps:
                created_directories.append(mkdir_ps.group(1))
                
            # Environment variables detection
            for name, val in env_pattern_bash.findall(line_stripped):
                env_vars[name] = val
            for name, val in env_pattern_ps.findall(line_stripped):
                env_vars[name] = val
                
            # Executed binaries detection
            for binary in binaries_to_check:
                if re.search(rf'\b{binary}\b', line_stripped):
                    executed_binaries.add(binary)
                    commands_run.append(line_stripped)
                    referenced_executables.add(binary)
                    
            # Docker commands specific detection
            if "docker" in line_stripped or "docker-compose" in line_stripped:
                docker_commands.append(line_stripped)
                
            # systemctl command detection
            if "systemctl" in line_stripped:
                systemctl_commands.append(line_stripped)
                referenced_services.add("systemctl")
                
            # service creation detection
            if ".service" in line_stripped or "/etc/systemd/system" in line_stripped:
                service_creation.append(line_stripped)
                referenced_services.add(line_stripped)

            for path_match in install_dir_pattern.findall(line_stripped):
                if path_match not in created_directories:
                    created_directories.append(path_match)
                
        return ScriptAnalysisResult(
            referenced_files=list(referenced_files),
            copied_files=copied_files,
            created_directories=created_directories,
            environment_variables=env_vars,
            executed_binaries=list(executed_binaries),
            configuration_files=list(configuration_files),
            referenced_environment_files=list(referenced_environment_files),
            generated_files=generated_files,
            referenced_executables=list(referenced_executables),
            referenced_services=list(referenced_services),
            docker_commands=docker_commands,
            systemctl_commands=systemctl_commands,
            service_creation=service_creation,
            commands_run=commands_run
        )
