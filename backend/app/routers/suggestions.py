from fastapi import APIRouter
from pydantic import BaseModel

from app.db import get_supabase
from app.services.suggestion_service import generate_suggestions_with_criteria

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


class SuggestionCriteriaRequest(BaseModel):
    type: str | None = None
    priority: str | None = None
    complexity: str | None = None
    tags: list[str] | None = None


class SimpleSuggestion(BaseModel):
    id: str
    text: str


@router.post("", response_model=list[dict])
async def get_suggestions_with_criteria(body: SuggestionCriteriaRequest):
    """Return suggestions from the DB filtered by custom criteria."""
    db = get_supabase()
    result = db.table("feature_suggestions").select("*").execute()
    suggestions = result.data or []

    criteria = body.model_dump(exclude_none=True)
    if criteria:
        suggestions = generate_suggestions_with_criteria(suggestions, criteria)

    return suggestions


@router.post("/criteria", response_model=list[SimpleSuggestion])
async def get_suggestions_by_structured_criteria(body: SuggestionCriteriaRequest):
    """Return simplified suggestions filtered by structured criteria."""
    db = get_supabase()
    result = db.table("feature_suggestions").select("*").execute()
    suggestions = result.data or []

    criteria = body.model_dump(exclude_none=True)
    if criteria:
        suggestions = generate_suggestions_with_criteria(suggestions, criteria)

    return [{"id": str(s["id"]), "text": s["name"]} for s in suggestions]
