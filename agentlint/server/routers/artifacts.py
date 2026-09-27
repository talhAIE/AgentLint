"""Router for reading artifacts from .agentlint/"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
import yaml

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

def _read_json_artifact(filename: str) -> dict | list:
    path = Path.cwd() / ".agentlint" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found")
    return json.loads(path.read_text(encoding="utf-8"))

def _read_yaml_artifact(filename: str) -> dict:
    path = Path.cwd() / ".agentlint" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found")
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def _read_text_artifact(filename: str) -> str:
    path = Path.cwd() / ".agentlint" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found")
    return path.read_text(encoding="utf-8")

@router.get("/findings")
def get_findings() -> dict | list:
    return _read_json_artifact("findings.json")

@router.get("/evidence")
def get_evidence() -> dict | list:
    return _read_json_artifact("evidence.json")

@router.get("/policy")
def get_policy() -> dict:
    return _read_yaml_artifact("policy.yaml")

@router.get("/repair")
def get_repair() -> dict:
    return {"content": _read_text_artifact("repair-plan.md")}

@router.get("/verification")
def get_verification() -> dict | list:
    return _read_json_artifact("verification.json")

@router.get("/sources")
def get_sources() -> dict | list:
    return _read_json_artifact("scan.json")
