"""Strategic future simulation — 3 divergent development branches."""

import json

from pydantic import BaseModel

from app.db import get_supabase
from app.services.llm_service import call_llm_structured


# ---------------------------------------------------------------------------
# Pydantic models for LLM structured output
# ---------------------------------------------------------------------------


class InitiativeItem(BaseModel):
    name: str
    description: str


class StrategicBranchItem(BaseModel):
    branch_name: str
    theme: str
    initiatives: list[InitiativeItem]
    architecture_impact: str
    scalability_impact: str
    risk_impact: str
    tradeoffs: str
    recommended_execution_order: list[str]
    narrative: str


class SimulationResponse(BaseModel):
    branches: list[StrategicBranchItem]


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


async def _call_llm_for_branches(
    digest: dict,
    features: list[dict],
    api_key: str | None = None,
) -> list[StrategicBranchItem]:
    """Call the LLM to generate exactly 3 philosophically distinct branches."""
    system_prompt = (
        "You are a senior product strategist and software architect. "
        "Given a repository's structure, framework, and inferred features, "
        "generate exactly 3 strategic future development branches that differ philosophically.\n\n"
        "Return a JSON object with key 'branches' containing exactly 3 items. "
        "Each branch must have:\n"
        "- branch_name (string): short memorable name\n"
        "- theme (string): one-line philosophy (e.g. 'Expansion-focused', 'Stability/refactor-focused', 'Strategic pivot')\n"
        "- initiatives (list): 3 to 6 objects, each with name (string) and description (string)\n"
        "- architecture_impact (string): 1-2 sentences on how this branch affects architecture\n"
        "- scalability_impact (string): 1-2 sentences on scalability implications\n"
        "- risk_impact (string): 1-2 sentences on risk profile\n"
        "- tradeoffs (string): 1-2 sentences on what you gain vs lose\n"
        "- recommended_execution_order (list[string]): ordered list of initiative names to implement first\n"
        "- narrative (string): 2-4 sentence readable explanation of this branch\n\n"
        "The 3 branches must be:\n"
        "1. Expansion-focused: prioritize new features, growth, user-facing additions\n"
        "2. Stability/refactor-focused: prioritize technical debt, tests, refactoring, reliability\n"
        "3. Strategic pivot: explore a different direction, new tech, or market shift\n\n"
        "Be concrete and reference the actual features and tech stack. "
        "Initiatives should map to or extend the inferred features where sensible."
    )

    feature_summary = "\n".join(
        f"- {f['name']}: {f.get('description', '')[:100]}"
        for f in features[:30]
    )

    user_content = (
        f"Repository context:\n"
        f"Framework: {digest.get('framework', 'unknown')}\n"
        f"Dependencies: {json.dumps(digest.get('dependencies', {}))}\n"
        f"Scripts: {json.dumps(digest.get('scripts', {}))}\n"
        f"File tree (first 80):\n{chr(10).join(digest.get('file_tree', [])[:80])}\n\n"
        f"Inferred features:\n{feature_summary or '(none)'}\n\n"
        f"Generate exactly 3 strategic branches."
    )

    response = await call_llm_structured(
        system_prompt=system_prompt,
        user_prompt=user_content,
        response_model=SimulationResponse,
        api_key=api_key,
    )

    if len(response.branches) != 3:
        raise ValueError(
            f"LLM returned {len(response.branches)} branches; expected exactly 3"
        )

    return response.branches


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def generate_strategic_branches(
    repo_id: str, api_key: str | None = None
) -> list[dict]:
    """Generate exactly 3 philosophically distinct future branches.

    Fetches repo, latest analysis run, digest, and feature nodes from Supabase.
    Calls the LLM to generate 3 branches, stores them, and returns the rows.
    """
    db = get_supabase()

    # Fetch repo
    repo_result = db.table("repos").select("*").eq("id", repo_id).execute()
    if not repo_result.data:
        raise ValueError(f"Repo {repo_id} not found")

    # Fetch latest completed analysis run
    run_result = (
        db.table("analysis_runs")
        .select("*")
        .eq("repo_id", repo_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    if not run_result.data:
        raise ValueError(f"No completed analysis run found for repo {repo_id}")

    run = run_result.data[0]
    digest = run.get("digest_json", {}) or {}

    # Fetch feature nodes for this run
    nodes_result = (
        db.table("feature_nodes")
        .select("id, name, description, anchor_files")
        .eq("analysis_run_id", run["id"])
        .execute()
    )
    features = nodes_result.data or []

    # Call LLM for branches
    raw_branches = await _call_llm_for_branches(
        digest=digest,
        features=features,
        api_key=api_key,
    )

    # Delete existing branches for this repo (replace on new simulation)
    db.table("strategic_branches").delete().eq("repo_id", repo_id).execute()

    # Map to DB row format and insert
    rows = []
    for b in raw_branches:
        initiatives_json = [
            {"name": i.name, "description": i.description}
            for i in b.initiatives
        ]
        execution_order = b.recommended_execution_order or []

        row = {
            "repo_id": repo_id,
            "branch_name": b.branch_name,
            "theme": b.theme,
            "initiatives_json": initiatives_json,
            "architecture_impact": b.architecture_impact,
            "scalability_impact": b.scalability_impact,
            "risk_impact": b.risk_impact,
            "tradeoffs": b.tradeoffs,
            "execution_order": execution_order,
            "narrative": b.narrative,
        }
        rows.append(row)

    insert_result = db.table("strategic_branches").insert(rows).execute()
    return insert_result.data
