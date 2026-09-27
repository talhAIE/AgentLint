"""Router for demo mode features."""

import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/demo", tags=["demo"])

_DEMO_REPOS_DIR = Path(__file__).parent.parent.parent.parent / "demo_repos"

@router.get("/repos")
def list_demo_repos() -> list[str]:
    if not _DEMO_REPOS_DIR.exists():
        return []
    repos = [p.name for p in _DEMO_REPOS_DIR.iterdir() if p.is_dir()]
    return repos

@router.post("/load/{repo_name}")
def load_demo(repo_name: str) -> dict[str, str]:
    source_dir = _DEMO_REPOS_DIR / repo_name / ".agentlint"
    if not source_dir.exists():
        raise HTTPException(status_code=404, detail=f"Demo repo {repo_name} artifacts not found")
    
    target_dir = Path.cwd() / ".agentlint"
    if target_dir.exists():
        shutil.rmtree(target_dir)
        
    shutil.copytree(source_dir, target_dir)
    return {"status": "ok", "repo": repo_name}
