# DevOps Installation Discovery & Correlation Agent

A production-ready standalone microservice prototype for **discovering, parsing, validating, and correlating** deployment scripts, dependencies, and configuration artifacts in a multi-agent DevOps environment.

This agent operates strictly through **deep static analysis** and **never executes installation files, shell scripts, or OS changes**.

---

## Architecture Overview

Built using Python 3.12, Clean Architecture, and SOLID principles:
- **FastAPI**: Exposes HTTP endpoints for remote agent integration.
- **Typer**: CLI helper tool for terminal execution.
- **NetworkX**: Builds dependency trees and cross-file linkage maps.
- **Watchdog**: Watches folder modifications and triggers updates.
- **Pydantic v2**: Handles schema models and validation rules.

---

## Directory Structure

```
installation-agent/
├── pyproject.toml
├── requirements.txt
├── main.py
├── cli.py
├── README.md
├── app/
│   ├── core/           # Pipeline configuration, logging details, exceptions
│   ├── config/         # App level global configuration settings
│   ├── models/         # Pydantic schema validation structures
│   ├── services/       # Scanners, static parsers, correlation graph, risk scoring
│   ├── watchers/       # Watchdog directory monitoring
│   └── utils/          # Mock environment setup data generator
├── tests/              # Full module pytest suite
├── fake_files/         # Automatically generated mock deployment projects
├── reports/            # Output reports (HTML, JSON, Markdown)
└── logs/               # Rotating file logs
```

---

## Setup & Local Execution

This project is configured for the `uv` toolchain.

### 1. Synchronize Dependencies
Install dependencies and set up the virtual environment:
```bash
uv sync
```

### 2. Generate Mock Test Workspace
Before running the agent, populate the `fake_files/` target directory with test projects:
```bash
uv run python cli.py generate-test-data
```
This generates four distinct layouts representing:
- **Project 1 (Python)**: with requirements.txt, .env, YAML configs, start.sh, Dockerfile, docker-compose.yml.
- **Project 2 (Java)**: with pom.xml, Spring boot properties, systemd services.
- **Project 3 (Node)**: with package.json, Docker configs, nginx.conf.
- **Project 4 (Windows)**: with setup.exe, install.ps1, config.ini, registry patches.
- **Malformed files**: with invalid JSON keys/brackets and corrupted tags.

### 3. Run the CLI Commands
Verify files indexing and scanning:
```bash
uv run python cli.py scan
```
Analyze dependencies, cross-references, and risk profiles:
```bash
uv run python cli.py analyze
```
Display graph relationships:
```bash
uv run python cli.py graph
```
Watch directories recursively:
```bash
uv run python cli.py watch
```

### 4. Start the API Server
Launch the FastAPI microservice:
```bash
uv run python main.py
```
Open your browser and navigate to `http://127.0.0.1:8000/docs` to access the interactive Swagger documentation.

---

## Running the Verification Suite
Execute the pytest suite to verify all modular service expectations:
```bash
uv run pytest -v
```
