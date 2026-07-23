import re
import json
import yaml
import logging
import configparser
import xml.etree.ElementTree as ET
from pathlib import Path
from app.models.schemas import ConfigAnalysisResult

logger = logging.getLogger("installation_agent")

class ConfigParser:
    """Statically parses and indexes diverse configuration formats without execution."""
    
    @staticmethod
    def parse(file_path: Path) -> ConfigAnalysisResult:
        ext = file_path.suffix.lower()
        filename = file_path.name.lower()
        
        logger.info(f"Parsing configuration file: {file_path}")
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error reading configuration file {file_path}: {e}")
            return ConfigAnalysisResult()
            
        raw_values = {}
        sections = []
        keys = []
        referenced_paths = []
        syntax_valid = True
        
        # Route parsing by filename/extension
        if filename == ".env" or filename == ".env.example" or filename.endswith(".env.template") or filename.endswith(".env.example") or filename == "environment.conf" or filename == "application.env.template" or ext == ".env":
            raw_values = ConfigParser._parse_env(content)
            keys = list(raw_values.keys())
        elif ext == ".properties":
            raw_values = ConfigParser._parse_properties(content)
            keys = list(raw_values.keys())
        elif ext in (".yaml", ".yml"):
            raw_values = ConfigParser._parse_yaml(content)
            keys = list(raw_values.keys())
        elif ext == ".json":
            raw_values = ConfigParser._parse_json(content)
            keys = list(raw_values.keys())
        elif ext == ".ini":
            raw_values = ConfigParser._parse_ini(content)
            keys = list(raw_values.keys())
            sections = ConfigParser._parse_ini_sections(content)
        elif ext in (".xml", ".config") or filename == "web.config":
            raw_values = ConfigParser._parse_xml(content)
            keys = list(raw_values.keys())
        elif filename == "nginx.conf" or filename == "apache.conf" or ext in (".conf", ".cfg"):
            raw_values = ConfigParser._parse_conf(content)
            keys = list(raw_values.keys())
        elif ext == ".reg":
            raw_values = ConfigParser._parse_reg(content)
            keys = list(raw_values.keys())
        else:
            raw_values = ConfigParser._parse_fallback(content)
            keys = list(raw_values.keys())

        referenced_paths = ConfigParser._extract_referenced_paths(content, raw_values)
        syntax_valid = bool(raw_values) or not content.strip()
            
        result = ConfigParser._analyze_raw_values(raw_values, content)
        result.sections = sections
        result.keys = keys
        result.referenced_paths = referenced_paths
        result.syntax_valid = syntax_valid
        return result

    @staticmethod
    def _parse_env(content: str) -> dict:
        data = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                data[key.strip()] = val.strip().strip('"').strip("'")
        return data

    @staticmethod
    def _parse_properties(content: str) -> dict:
        data = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                data[key.strip()] = val.strip()
            elif ':' in line:
                key, val = line.split(':', 1)
                data[key.strip()] = val.strip()
        return data

    @staticmethod
    def _parse_yaml(content: str) -> dict:
        try:
            # Safe load supports multi-document or standard dicts
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return ConfigParser._flatten_dict(data)
            return {"yaml_content": str(data)}
        except Exception as e:
            logger.warning(f"YAML parsing error: {e}")
            return {}

    @staticmethod
    def _parse_json(content: str) -> dict:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return ConfigParser._flatten_dict(data)
            return {"json_content": str(data)}
        except Exception as e:
            logger.warning(f"JSON parsing error: {e}")
            return {}

    @staticmethod
    def _parse_ini(content: str) -> dict:
        data = {}
        parser = configparser.ConfigParser()
        try:
            parser.read_string(content)
            for section in parser.sections():
                for key, val in parser.items(section):
                    data[f"{section}.{key}"] = val
        except Exception as e:
            logger.warning(f"INI parsing error: {e}")
        return data

    @staticmethod
    def _parse_ini_sections(content: str) -> list:
        sections = []
        parser = configparser.ConfigParser()
        try:
            parser.read_string(content)
            sections.extend(parser.sections())
        except Exception:
            pass
        return sections

    @staticmethod
    def _parse_xml(content: str) -> dict:
        data = {}
        try:
            root = ET.fromstring(content)
            for child in root.iter():
                # Supports web.config <add key="x" value="y" /> style and standard <tag>val</tag>
                if child.tag == "add" and "key" in child.attrib and "value" in child.attrib:
                    data[child.attrib["key"]] = child.attrib["value"]
                elif child.text and child.text.strip() and len(child) == 0:
                    data[child.tag] = child.text.strip()
        except Exception as e:
            logger.warning(f"XML parsing error: {e}")
        return data

    @staticmethod
    def _parse_conf(content: str) -> dict:
        data = {}
        # Parse statements of type `listen 80;` or `server_name example.com;`
        statements = re.findall(r'\b(\w+)\s+([^;]+);', content)
        for key, val in statements:
            data[key.strip()] = val.strip()
        return data

    @staticmethod
    def _parse_reg(content: str) -> dict:
        data = {}
        current_key = "Registry"
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                current_key = line[1:-1]
            elif '=' in line:
                name, val = line.split('=', 1)
                data[f"{current_key}\\{name.strip().strip('\"')}"] = val.strip().strip('\"')
        return data

    @staticmethod
    def _parse_fallback(content: str) -> dict:
        data = {}
        matches = re.findall(r'\b([a-zA-Z0-9_\-\.]+)\s*[:=]\s*([^\n]+)', content)
        for key, val in matches:
            data[key.strip()] = val.strip().strip('"').strip("'")
        return data

    @staticmethod
    def _flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ConfigParser._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def _extract_referenced_paths(content: str, raw_values: dict) -> list:
        referenced_paths = set()
        path_pattern = re.compile(r'(?:(?:[A-Za-z]:\\)|/)[^\s"\']+')
        for match in path_pattern.findall(content):
            referenced_paths.add(match.rstrip('),;'))
        for value in raw_values.values():
            value_str = str(value)
            if any(sep in value_str for sep in ('/', '\\')):
                for match in path_pattern.findall(value_str):
                    referenced_paths.add(match.rstrip('),;'))
        return sorted(referenced_paths)

    @staticmethod
    def _analyze_raw_values(raw_values: dict, full_content: str) -> ConfigAnalysisResult:
        app_name = None
        version = None
        ports = []
        db_host = None
        db_port = None
        db_name = None
        username = None
        env_vars = {}
        api_urls = []
        filesystem_paths = []
        volumes = []
        mounts = []
        services = []
        logging_configuration = {}
        security_settings = {}
        docker_images = []
        kubernetes_resources = []
        
        # Regex to scan for API/Web endpoints URLs
        url_regex = re.compile(r'https?:\/\/[a-zA-Z0-9_\-\.\/:]+')
        for val in raw_values.values():
            val_str = str(val)
            for url in url_regex.findall(val_str):
                if url not in api_urls:
                    api_urls.append(url)
                    
        # Loop to classify settings
        for key, val in raw_values.items():
            key_lower = key.lower()
            val_str = str(val)
            val_lower = val_str.lower()
            
            # Application Identity
            if any(x in key_lower for x in ("app.name", "application.name", "appname", "name")) and not app_name:
                app_name = val_str
            if any(x in key_lower for x in ("version", "app.version")) and not version:
                version = val_str
                
            # Networking Ports
            if any(x in key_lower for x in ("port", "listen", "addr")) or key_lower == "ports":
                ports_found = re.findall(r'\b\d{2,5}\b', val_str)
                for p in ports_found:
                    p_int = int(p)
                    if p_int not in ports:
                        ports.append(p_int)
                        
            # DB Info extraction
            if any(x in key_lower for x in ("db.host", "database.host", "db_host", "datasource.url", "db.url", "connectionstring")):
                if "jdbc:" in val_lower or "postgresql://" in val_lower or "mysql://" in val_lower:
                    match = re.search(r'//([^/:]+)(?::(\d+))?/([^?]+)', val_str)
                    if match:
                        db_host = match.group(1)
                        if match.group(2):
                            db_port = int(match.group(2))
                        db_name = match.group(3)
                else:
                    db_host = val_str
            if any(x in key_lower for x in ("db.port", "database.port", "db_port")):
                try:
                    db_port = int(val_str)
                except ValueError:
                    pass
            if any(x in key_lower for x in ("db.name", "database.name", "db_name", "db.database", "database")):
                if not db_name:
                    db_name = val_str
            if any(x in key_lower for x in ("db.username", "db.user", "db_user", "username", "user")):
                username = val_str
                
            # Environment variables
            if key.isupper():
                env_vars[key] = val_str
                
            # Logging Configurations
            if any(x in key_lower for x in ("log", "logging", "level", "logger")):
                logging_configuration[key] = val_str
                
            # Security configuration
            if any(x in key_lower for x in ("security", "ssl", "tls", "key", "cert", "token", "secret", "password", "auth")):
                security_settings[key] = val_str
                
            # Docker parameters
            if key_lower.endswith(".image") or key_lower == "image":
                docker_images.append(val_str)
            if key_lower.endswith(".volumes") or key_lower == "volumes":
                volumes.append(val_str)
            if key_lower.endswith(".services") or key_lower == "services":
                services.append(val_str)
                
        # Parse docker compose specifically
        if "services:" in full_content and ("version:" in full_content or "networks:" in full_content or "volumes:" in full_content):
            try:
                compose_data = yaml.safe_load(full_content)
                if isinstance(compose_data, dict) and "services" in compose_data:
                    for svc_name, svc_conf in compose_data["services"].items():
                        if svc_name not in services:
                            services.append(svc_name)
                        if isinstance(svc_conf, dict):
                            if "image" in svc_conf:
                                docker_images.append(str(svc_conf["image"]))
                            if "ports" in svc_conf:
                                for p_entry in svc_conf["ports"]:
                                    p_str = str(p_entry)
                                    p_match = re.search(r'(\d+):', p_str)
                                    if p_match:
                                        ports.append(int(p_match.group(1)))
                                    else:
                                        p_match2 = re.search(r'\b\d+\b', p_str)
                                        if p_match2:
                                            ports.append(int(p_match2.group(0)))
            except Exception:
                pass
                
        # Kubernetes manifests detection
        if "apiVersion:" in full_content and "kind:" in full_content:
            try:
                k8s_docs = yaml.safe_load_all(full_content)
                for doc in k8s_docs:
                    if isinstance(doc, dict) and "kind" in doc:
                        name = doc.get("metadata", {}).get("name", "unnamed")
                        kubernetes_resources.append(f"{doc['kind']}/{name}")
            except Exception:
                pass
                
        return ConfigAnalysisResult(
            application_name=app_name,
            version=version,
            ports=list(set(ports)),
            database_host=db_host,
            database_port=db_port,
            database_name=db_name,
            username=username,
            env_vars=env_vars,
            api_urls=api_urls,
            filesystem_paths=filesystem_paths,
            volumes=volumes,
            mounts=mounts,
            services=services,
            logging_configuration=logging_configuration,
            security_settings=security_settings,
            docker_images=list(set(docker_images)),
            kubernetes_resources=list(set(kubernetes_resources)),
            raw_values=raw_values
        )
