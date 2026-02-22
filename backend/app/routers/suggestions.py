from fastapi import APIRouter
from pydantic import BaseModel

from app.services.suggestion_service import generate_suggestions_with_criteria

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


class GenerateRequest(BaseModel):
    criteria: str


class CriteriaRequest(BaseModel):
    priority: str = ""
    complexity: str = ""
    tags: list[str] = []


@router.post("/generate")
async def generate_suggestions_endpoint(body: GenerateRequest):
    return generate_suggestions_with_criteria([], {"custom": body.criteria})


@router.post("/criteria")
async def filter_suggestions_by_criteria(body: CriteriaRequest):
    return generate_suggestions_with_criteria(
        [],
        {"priority": body.priority, "complexity": body.complexity, "tags": body.tags},
    )
