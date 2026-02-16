from fastapi import APIRouter, Depends, HTTPException
from app.schemas.branches import StrategicBranchResponse
from app.db import get_supabase
from app.dependencies import get_openai_key

router = APIRouter(prefix="/api/repos", tags=["branches"])


@router.post("/{repo_id}/simulate", response_model=list[StrategicBranchResponse])
async def simulate_futures(
    repo_id: str,
    openai_key: str | None = Depends(get_openai_key),
):
    """Generate 3 strategic future branches for a repo."""
    from app.services.simulation_service import generate_strategic_branches

    branches = await generate_strategic_branches(repo_id, api_key=openai_key)
    return branches


@router.get("/{repo_id}/branches", response_model=list[StrategicBranchResponse])
async def get_branches(repo_id: str):
    """Retrieve previously generated strategic branches."""
    db = get_supabase()
    result = (
        db.table("strategic_branches")
        .select("*")
        .eq("repo_id", repo_id)
        .execute()
    )
    return result.data
