# Installation Discovery & Correlation Agent Report
**Generated at:** 2026-07-12T17:43:28.475292Z

## 1. Executive Summary
- **Total Scanned Files:** 17
- **Total Workspace Size:** 3603 bytes
- **Duplicate Files Found:** 0
- **Detected Install Entrypoints:** 3
- **Risk Rating:** 75/100
- **System Risk Profile Status:** **CRITICAL**

## 2. Risk & Vulnerability Analysis
### Score Card: 75 / 100
| Risk Code | Category | Impact | Reason |
| --- | --- | --- | --- |
| `UNSIGNED_EXECUTABLES` | Unsigned Executables / Scripts | +20 | Discovered 2 executable assets in path (e.g. ['install.ps1', 'setup.exe']) |
| `HARDCODED_SECRETS` | Hardcoded Secrets Detected | +25 | Found password, token, or private key values written in text. Example in application.properties: key 'spring.datasource.password' |
| `UNKNOWN_VENDOR` | Unknown Project Ownership | +10 | No vendor, creator, or license properties were found in configuration files. |
| `VALIDATION_ERRORS` | Syntactic Validation Issues | +20 | Detected 5 syntax validation errors in project configurations. |

### Recommendations
- Verify and digitally sign all installation executables, scripts, and helper binaries.
- Migrate plain secrets out of code/configs. Retrieve them dynamically via Environment variables or KMS stores.
- Incorporate vendor headers and license files inside the deployment structure.
- Resolve all syntax and broken cross-file dependencies before launching.

## 3. Discovered Installers & Entrypoints
- `start.sh` (Location: `C:/Users/ASUS/Desktop/installation-agent/fake_files/project_python/start.sh`)
- `install.ps1` (Location: `C:/Users/ASUS/Desktop/installation-agent/fake_files/project_windows/install.ps1`)
- `setup.exe` (Location: `C:/Users/ASUS/Desktop/installation-agent/fake_files/project_windows/setup.exe`)

## 4. Configuration Inventory
### Configuration: `corrupted_config.json`
- **Application Name:** N/A
- **Version:** N/A
- **Ports Exposed:** None
### Configuration: `application.properties`
- **Application Name:** dbuser
- **Version:** N/A
- **Ports Exposed:** 8080
- **Database Connection:** `dbuser@postgres-db:5432/javadb`
### Configuration: `pom.xml`
- **Application Name:** N/A
- **Version:** 4.0.0
- **Ports Exposed:** None
### Configuration: `nginx.conf`
- **Application Name:** localhost
- **Version:** N/A
- **Ports Exposed:** None
### Configuration: `package.json`
- **Application Name:** node-devops-app
- **Version:** 2.0.0
- **Ports Exposed:** None
### Configuration: `.env`
- **Application Name:** python_app_db
- **Version:** N/A
- **Ports Exposed:** 8000, 5432
- **Database Connection:** `postgres@localhost:5432/python_app_db`
### Configuration: `application.yml`
- **Application Name:** postgres
- **Version:** N/A
- **Ports Exposed:** 8000, 5432
- **Database Connection:** `postgres@localhost:5432/localhost`
### Configuration: `docker-compose.yml`
- **Application Name:** N/A
- **Version:** 3.8
- **Ports Exposed:** 8000, 5432
- **Docker Images Referenced:** `postgres:12`
### Configuration: `config.ini`
- **Application Name:** N/A
- **Version:** N/A
- **Ports Exposed:** 1433
### Configuration: `registry.reg`
- **Application Name:** N/A
- **Version:** N/A
- **Ports Exposed:** 1433

## 5. Dependency Graph Findings
- **Total Unique Dependencies Listed:** 14
- **Missing Packages/Runtimes:** 0
- **Duplicate Package Names:** 0
- **Version Conflict Detections:** 0
- **Unsupported Versions Found:** 3

### Unsupported Runtime Versions
- Node.js version 16-alpine in Dockerfile is unsupported. Minimum required is 18.
- Node.js version 3.0.1 in package.json is unsupported. Minimum required is 18.
- PostgreSQL version 12 in docker-compose.yml is unsupported. Minimum required is 13.

## 6. Validation Report Summary
- **Overall Project Valid:** **False**
- **Total Errors:** 5
- **Total Warnings:** 4

### Critical Errors
- **[syntax]** in `corrupted_config.json`: Invalid JSON syntax: Expecting ',' delimiter: line 7 column 3 (char 138) (Severity: `ERROR`)
- **[integrity]** in `corrupted_config.json`: Simulated file corruption detected ('corrupted' marker found). (Severity: `ERROR`)
- **[broken_reference]** in `start.sh`: Script references missing file: './config.yml' (Severity: `ERROR`)
- **[broken_reference]** in `install.ps1`: Script references missing file: '"C:\Program' (Severity: `ERROR`)
- **[broken_reference]** in `install.ps1`: Script references missing file: '".\config.ini"' (Severity: `ERROR`)

### Validation Warnings
- **[duplicate_key]** in `corrupted_config.json`: Duplicate JSON key found: 'duplicate_key'
- **[missing_value]** in `.env`: Sensitive credential key 'API_KEY' has empty/blank value on line 7
- **[duplicate_key]** in `application.yml`: Duplicate YAML key found: 'port'
- **[duplicate_key]** in `docker-compose.yml`: Duplicate YAML key found: 'ports'