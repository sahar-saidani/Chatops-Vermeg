import pytest
from pathlib import Path
from app.services.parser.script_parser import ScriptParser
from app.services.parser.config_parser import ConfigParser
from app.config.settings import settings

def test_script_parser():
    script_path = settings.get_absolute_path(settings.fake_files_dir) / "project_python" / "start.sh"
    assert script_path.exists()
    
    result = ScriptParser.parse(script_path)
    
    # Assertions
    assert "application.yml" in result.configuration_files
    assert "./application.yml -> ./config.yml" in result.copied_files
    assert "./logs" in result.created_directories
    assert "pip" in result.executed_binaries
    assert "python" in result.executed_binaries
    assert result.environment_variables.get("APP_ENV") == "production"

def test_config_parser_env():
    env_path = settings.get_absolute_path(settings.fake_files_dir) / "project_python" / ".env"
    assert env_path.exists()
    
    result = ConfigParser.parse(env_path)
    
    # Assertions
    assert result.env_vars.get("PORT") == "8000"
    assert result.env_vars.get("DB_HOST") == "localhost"
    assert result.database_host == "localhost"
    assert result.database_name == "python_app_db"
    assert result.database_port == 5432
    assert result.username == "postgres"

def test_config_parser_yaml():
    yml_path = settings.get_absolute_path(settings.fake_files_dir) / "project_python" / "application.yml"
    assert yml_path.exists()
    
    result = ConfigParser.parse(yml_path)
    
    # Assertions
    assert result.raw_values.get("server.port") == 8000
    assert result.raw_values.get("database.host") == "localhost"
    assert set(result.ports) == {8000, 5432}

def test_config_parser_properties():
    props_path = settings.get_absolute_path(settings.fake_files_dir) / "project_java" / "application.properties"
    assert props_path.exists()
    
    result = ConfigParser.parse(props_path)
    
    # Assertions
    assert result.ports == [8080]
    assert result.database_host == "postgres-db"
    assert result.database_port == 5432
    assert result.database_name == "javadb"
    assert result.username == "dbuser"
