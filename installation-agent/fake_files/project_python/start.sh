#!/bin/bash
# Startup script for Python application
echo "Starting Python container environment..."
export APP_ENV=production
mkdir -p ./logs
cp ./application.yml ./config.yml
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
