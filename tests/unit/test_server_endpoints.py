"""Unit tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch
import json

from agentlint.server.app import create_app

client = TestClient(create_app())

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("agentlint.server.routers.artifacts.Path.cwd")
def test_get_findings(mock_cwd, tmp_path):
    mock_cwd.return_value = tmp_path
    
    agentlint_dir = tmp_path / ".agentlint"
    agentlint_dir.mkdir()
    findings_file = agentlint_dir / "findings.json"
    findings_file.write_text(json.dumps([{"id": "test_finding"}]), encoding="utf-8")
    
    response = client.get("/artifacts/findings")
    assert response.status_code == 200
    assert response.json() == [{"id": "test_finding"}]

@patch("agentlint.server.routers.artifacts.Path.cwd")
def test_get_artifacts_404(mock_cwd, tmp_path):
    mock_cwd.return_value = tmp_path
    
    response = client.get("/artifacts/findings")
    assert response.status_code == 404
