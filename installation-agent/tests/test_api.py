import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "agent" in data

def test_api_scan():
    response = client.post("/scan", json={})
    assert response.status_code == 200
    data = response.json()
    assert "total_files" in data
    assert "files" in data

def test_api_discover():
    response = client.post("/discover", json={})
    assert response.status_code == 200
    data = response.json()
    assert "entrypoints" in data
    assert isinstance(data["entrypoints"], list)

def test_api_analyze():
    response = client.post("/analyze", json={})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "risk_report" in data

def test_api_validate():
    response = client.post("/validate", json={})
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "errors" in data
    assert "warnings" in data

def test_api_graph():
    response = client.get("/graph")
    assert response.status_code == 200
    data = response.json()
    assert "dependencies" in data
    assert "file_correlation" in data

def test_api_reports():
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
