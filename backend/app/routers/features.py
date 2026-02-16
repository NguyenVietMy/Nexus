from fastapi import APIRouter, Depends, HTTPException
from app.schemas.features import FeatureSuggestionResponse
from app.db import get_supabase
from app.dependencies import get_openai_key

router = APIRouter(prefix="/api/features", tags=["features"])


@router.get("/{node_id}/suggestions", response_model=list[FeatureSuggestionResponse])
async def get_suggestions(
    node_id: str,
    openai_key: str | None = Depends(get_openai_key),
):
    """Generate or retrieve feature expansion suggestions for a node."""
    db = get_supabase()

    # Check if suggestions already exist
    existing = (
        db.table("feature_suggestions")
        .select("*")
        .eq("feature_node_id", node_id)
        .execute()
    )
    if existing.data:
        return existing.data

    # Generate suggestions via LLM
    from app.services.suggestion_service import generate_suggestions

    suggestions = await generate_suggestions(node_id, api_key=openai_key)
    return suggestions
