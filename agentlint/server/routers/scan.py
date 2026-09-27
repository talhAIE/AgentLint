"""Router for trigger scans."""

from fastapi import APIRouter
import asyncio

router = APIRouter(prefix="/scan", tags=["scan"])

@router.post("")
async def start_scan(repo_path: str):
    # MVP: Return mock job ID
    return {"job_id": "job-1"}
    
@router.get("/status/{job_id}")
async def get_scan_status(job_id: str):
    return {"status": "done"}
