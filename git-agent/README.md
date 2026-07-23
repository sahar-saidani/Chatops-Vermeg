# Installation

## 1. Clone the repository

```bash
git clone https://github.com/<username>/git-agent.git
cd git-agent
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
```

or

```bash
py -m venv .venv
```

---

## 3. Activate the virtual environment

### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Command Prompt (CMD)

```cmd
.venv\Scripts\activate.bat
```

### Git Bash

```bash
source .venv/Scripts/activate
```

---

## 4. Upgrade pip (recommended)

```bash
python -m pip install --upgrade pip
```

---

## 5. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 6. Verify installation

```bash
python --version
pip --version
```

---

# Configuration

## GitHub Personal Access Token (Optional)

To analyze GitHub repositories without API rate limits, create a Personal Access Token and set it as an environment variable.

### PowerShell

```powershell
$env:GITHUB_TOKEN="your_token_here"
```

### CMD

```cmd
set GITHUB_TOKEN=your_token_here
```

### Linux / macOS

```bash
export GITHUB_TOKEN="your_token_here"
```

---

# Usage

## Analyze a local repository

```bash
python main.py analyze --path "C:\Projects\MyRepo"
```

or

```bash
python main.py analyze --repo-path "C:\Projects\MyRepo"
```

(depending on your CLI arguments)

---

## Analyze a GitHub repository

```bash
python main.py analyze --repo owner/repository
```

Example:

```bash
python main.py analyze --repo sahar-saidani/ToDoList
```

---

## Specify an output directory

```bash
python main.py analyze --repo sahar-saidani/ToDoList --output reports
```

---

# Running Tests

Run all unit tests:

```bash
python -m pytest tests
```

Run with verbose output:

```bash
python -m pytest -v tests
```

Run a specific test file:

```bash
python -m pytest tests/test_github_client.py
```

---

# Generated Reports

After execution, reports are generated inside the `reports/` directory.

Example:

```
reports/
├── analysis.json
├── analysis.md
└── summary.txt
```

---

# Deactivate the virtual environment

```bash
deactivate
```

---

# Troubleshooting

### Missing dependencies

```bash
pip install -r requirements.txt
```

### Install a missing package

Example:

```bash
pip install python-dotenv
```

### Upgrade all dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Verify installed packages

```bash
pip list
```

### Check Python interpreter

```bash
python -c "import sys; print(sys.executable)"
```

---

# Clean Python Cache

### Windows

```bash
rmdir /s /q __pycache__
```

### Linux / macOS

```bash
find . -name "__pycache__" -type d -exec rm -rf {} +
```