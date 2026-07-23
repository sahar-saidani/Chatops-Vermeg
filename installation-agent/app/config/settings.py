from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_", case_sensitive=False)
    
    # Core directories
    workspace_dir: Path = Path("c:/Users/ASUS/Desktop/installation-agent")
    fake_files_dir: Path = Path("fake_files")
    reports_dir: Path = Path("reports")
    logs_dir: Path = Path("logs")
    
    # Scanner Settings
    ignored_folders: List[str] = [
        ".git", 
        ".venv", 
        "venv", 
        "__pycache__", 
        "node_modules", 
        ".pytest_cache", 
        ".idea", 
        ".vscode",
        "dist",
        "build"
    ]
    follow_symlinks: bool = True
    
    # Watcher Settings
    watch_directory: Path = Path("fake_files")
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/installation_agent.log"

    def get_absolute_path(self, path: Path | str) -> Path:
        """Returns absolute path, relative to workspace if not absolute already."""
        p = Path(path)
        if p.is_absolute():
            return p
        return (Path(self.workspace_dir) / p).resolve()

settings = Settings()
