# Installation Discovery & Correlation Agent Report
**Generated at:** 2026-08-15T11:39:45.757765Z

## 1. Executive Summary
- **Total Scanned Files:** 1
- **Total Workspace Size:** 24775 bytes
- **Duplicate Files Found:** 0
- **Detected Install Entrypoints:** 0
- **Risk Rating:** 25/100
- **System Risk Profile Status:** **SECURE**

## 2. Risk & Vulnerability Analysis
### Score Card: 25 / 100
| Risk Code | Category | Impact | Reason |
| --- | --- | --- | --- |
| `HARDCODED_SECRETS` | Hardcoded Secrets Detected | +25 | Found password, token, or private key values written in text. Example in install.tokens: key 'tokens.solife.consumers.concurrent' |

### Recommendations
- Migrate plain secrets out of code/configs. Retrieve them dynamically via Environment variables or KMS stores.

## 3. Discovered Installers & Entrypoints
*No installer entrypoints found.*

## 4. Configuration Inventory
### Configuration: `install.tokens`
- **Application Name:** default
- **Version:** 7.6.13.35-SNAPSHOT
- **Ports Exposed:** 31745, 9, 10, 11, 528, 529, 31, 161, 546, 545, 31010, 162, 555, 300, 943, 565, 443, 444, 445, 446, 447, 448, 575, 2500, 712, 200, 714, 457, 80, 8787, 90, 93, 990, 98, 99, 100, 31845, 999, 7020, 8686, 1521
- **Database Connection:** `jboss.mdb.configuration=Standard Message Driven Bean@localhost:1521/solife.server.java.home=/dll/soft/solife/jdk-11.0.12`
- **Docker Images Referenced:** `/com/bsb/is/config/gui/vermeg-life.png`

## 5. Dependency Graph Findings
- **Total Unique Dependencies Listed:** 0
- **Missing Packages/Runtimes:** 0
- **Duplicate Package Names:** 0
- **Version Conflict Detections:** 0
- **Unsupported Versions Found:** 0

## 6. Validation Report Summary
- **Overall Project Valid:** **True**
- **Total Errors:** 0
- **Total Warnings:** 0