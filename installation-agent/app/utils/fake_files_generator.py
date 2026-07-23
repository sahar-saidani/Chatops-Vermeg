import os
import logging
from pathlib import Path
from app.config.settings import settings

logger = logging.getLogger("installation_agent")

class FakeFilesGenerator:
    """Generates four distinct test directories with realistic fake configurations and installer entrypoints."""
    
    @staticmethod
    def generate_all(target_dir: Path | None = None):
        root = target_dir or settings.get_absolute_path(settings.fake_files_dir)
        root.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating simulated projects in path: {root}")
        
        # ----------------------------------------------------
        # Project 1: Python application
        # ----------------------------------------------------
        p1 = root / "project_python"
        p1.mkdir(exist_ok=True)
        
        (p1 / "requirements.txt").write_text(
            "fastapi>=0.110.0\n"
            "uvicorn==0.28.0\n"
            "pydantic>=2.6.0\n"
            "requests==2.28.1\n"
            "pyyaml>=6.0.1\n"
            "# conflict version package trigger\n"
            "urllib3==1.26.15\n",
            encoding="utf-8"
        )
        
        (p1 / ".env").write_text(
            "PORT=8000\n"
            "DB_HOST=localhost\n"
            "DB_PORT=5432\n"
            "DB_NAME=python_app_db\n"
            "DB_USER=postgres\n"
            "DB_PASSWORD=my_super_secret_hardcoded_pass_123\n"  # Vulnerability Check
            "API_KEY=\n",  # Empty secret warning
            encoding="utf-8"
        )
        
        (p1 / "application.yml").write_text(
            "server:\n"
            "  port: 8000\n"
            "database:\n"
            "  host: localhost\n"
            "  port: 5432\n"
            "  username: postgres\n"
            "  password: ${DB_PASSWORD}\n"
            "  name: python_app_db\n"
            "logging:\n"
            "  level: INFO\n"
            "  file: app.log\n",
            encoding="utf-8"
        )
        
        (p1 / "start.sh").write_text(
            "#!/bin/bash\n"
            "# Startup script for Python application\n"
            "echo \"Starting Python container environment...\"\n"
            "export APP_ENV=production\n"
            "mkdir -p ./logs\n"
            "cp ./application.yml ./config.yml\n"
            "pip install -r requirements.txt\n"
            "python -m uvicorn main:app --host 0.0.0.0 --port 8000\n",
            encoding="utf-8"
        )
        
        (p1 / "Dockerfile").write_text(
            "FROM python:3.9-slim\n"  # Deprecated runtime version trigger
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE 8000\n"
            "CMD [\"python\", \"main.py\"]\n",
            encoding="utf-8"
        )
        
        (p1 / "docker-compose.yml").write_text(
            "version: '3.8'\n"
            "services:\n"
            "  web:\n"
            "    build: .\n"
            "    ports:\n"
            "      - \"8000:8000\"\n"
            "    env_file:\n"
            "      - .env\n"
            "  db:\n"
            "    image: postgres:12\n"  # Deprecated DB runtime version trigger
            "    environment:\n"
            "      POSTGRES_DB: python_app_db\n"
            "      POSTGRES_PASSWORD: my_super_secret_hardcoded_pass_123\n"
            "    ports:\n"
            "      - \"5432:5432\"\n",
            encoding="utf-8"
        )
        
        # ----------------------------------------------------
        # Project 2: Java Spring Boot
        # ----------------------------------------------------
        p2 = root / "project_java"
        p2.mkdir(exist_ok=True)
        
        (p2 / "pom.xml").write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n"
            "    <modelVersion>4.0.0</modelVersion>\n"
            "    <groupId>com.devops</groupId>\n"
            "    <artifactId>spring-boot-app</artifactId>\n"
            "    <version>1.0.0</version>\n"
            "    <dependencies>\n"
            "        <dependency>\n"
            "            <groupId>org.springframework.boot</groupId>\n"
            "            <artifactId>spring-boot-starter-web</artifactId>\n"
            "            <version>3.1.2</version>\n"
            "        </dependency>\n"
            "        <dependency>\n"
            "            <groupId>org.postgresql</groupId>\n"
            "            <artifactId>postgresql</artifactId>\n"
            "            <version>42.6.0</version>\n"
            "        </dependency>\n"
            "    </dependencies>\n"
            "</project>\n",
            encoding="utf-8"
        )
        
        (p2 / "application.properties").write_text(
            "server.port=8080\n"
            "spring.datasource.url=jdbc:postgresql://postgres-db:5432/javadb\n"
            "spring.datasource.username=dbuser\n"
            "spring.datasource.password=java_pass_secret\n"  # Vulnerability check password
            "logging.level.org.springframework=WARN\n",
            encoding="utf-8"
        )
        
        (p2 / "spring-app.service").write_text(
            "[Unit]\n"
            "Description=Spring Boot DevOps Service\n"
            "After=network.target\n"
            "\n"
            "[Service]\n"
            "Type=simple\n"
            "User=root\n"  # Escalation check
            "ExecStart=/usr/bin/java -jar /opt/spring-boot-app.jar\n"
            "Restart=always\n"
            "\n"
            "[Install]\n"
            "WantedBy=multi-user.target\n",
            encoding="utf-8"
        )
        
        # ----------------------------------------------------
        # Project 3: Node.js
        # ----------------------------------------------------
        p3 = root / "project_node"
        p3.mkdir(exist_ok=True)
        
        (p3 / "package.json").write_text(
            "{\n"
            "  \"name\": \"node-devops-app\",\n"
            "  \"version\": \"2.0.0\",\n"
            "  \"dependencies\": {\n"
            "    \"express\": \"^4.18.2\",\n"
            "    \"pg\": \"^8.11.0\"\n"
            "  },\n"
            "  \"devDependencies\": {\n"
            "    \"nodemon\": \"^3.0.1\"\n"
            "  }\n"
            "}\n",
            encoding="utf-8"
        )
        
        (p3 / "Dockerfile").write_text(
            "FROM node:16-alpine\n"  # Deprecated runtime warning
            "WORKDIR /usr/src/app\n"
            "COPY package*.json ./\n"
            "RUN npm install\n"
            "COPY . .\n"
            "EXPOSE 3000\n"
            "CMD [\"node\", \"index.js\"]\n",
            encoding="utf-8"
        )
        
        (p3 / "nginx.conf").write_text(
            "events { worker_connections 1024; }\n"
            "http {\n"
            "    server {\n"
            "        listen 80;\n"
            "        server_name localhost;\n"
            "        location / {\n"
            "            proxy_pass http://node-app:3000;\n"
            "        }\n"
            "    }\n"
            "}\n",
            encoding="utf-8"
        )
        
        # ----------------------------------------------------
        # Project 4: Windows installer
        # ----------------------------------------------------
        p4 = root / "project_windows"
        p4.mkdir(exist_ok=True)
        
        (p4 / "setup.exe").write_text(
            "[Installer Binary Stub]\n"
            "Signature=Unsigned\n"
            "TargetOS=Windows\n"
            "Vendor=UnknownVendor\n",
            encoding="utf-8"
        )
        
        (p4 / "install.ps1").write_text(
            "# PowerShell Setup script\n"
            "Write-Output \"Configuring Windows installation...\"\n"
            "$env:DB_PORT = \"1433\"\n"
            "New-Item -ItemType Directory -Path \"C:\\Program Files\\WindowsDevOps\"\n"
            "Copy-Item -Path \".\\config.ini\" -Destination \"C:\\Program Files\\WindowsDevOps\\config.ini\"\n"
            "& .\\setup.exe /S\n",
            encoding="utf-8"
        )
        
        (p4 / "config.ini").write_text(
            "[Database]\n"
            "Port = 1433\n"
            "Server = localhost\n"
            "User = sa\n"
            "Password = sql_hardcoded_secret_999\n",  # Vulnerability check
            encoding="utf-8"
        )
        
        (p4 / "registry.reg").write_text(
            "Windows Registry Editor Version 5.00\n"
            "\n"
            "[HKEY_LOCAL_MACHINE\\SOFTWARE\\DevOpsAgent]\n"
            "\"InstallPath\"=\"C:\\\\Program Files\\\\WindowsDevOps\"\n"
            "\"Port\"=\"1433\"\n",
            encoding="utf-8"
        )
        
        # ----------------------------------------------------
        # 5. Malformed/Corrupted Config (for checking validator errors)
        # ----------------------------------------------------
        (root / "corrupted_config.json").write_text(
            "{\n"
            "  \"app\": \"Corrupted Application\",\n"
            "  \"version\": \"1.0.0\",\n"
            "  \"corrupted\": true,\n"
            "  \"duplicate_key\": \"value1\",\n"
            "  \"duplicate_key\": \"value2\"\n"
            "  # missing closing bracket or comma to simulate parsing failure\n",
            encoding="utf-8"
        )
        
        logger.info("Test workspace generated successfully.")
