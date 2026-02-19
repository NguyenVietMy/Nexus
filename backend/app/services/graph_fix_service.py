"""LLM-powered graph structural fix service.

User describes desired changes in natural language.
LLM returns a structured diff that is applied to feature_nodes / feature_edges.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.db import get_supabase
from app.services.llm_service import call_llm_structured


# ---------------------------------------------------------------------------
# Diff models
# ---------------------------------------------------------------------------


class AddNodeItem(BaseModel):
    name: str
    description: str
    parent_node_id: str | None = None


class ReparentItem(BaseModel):
    node_id: str
    new_parent_id: str | None = None  # None = promote to root


class GraphFixDiff(BaseModel):
    add_nodes: list[AddNodeItem] = []
    remove_node_ids: list[str] = []
    reparent: list[ReparentItem] = []
    explanation: str


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def _build_tree_context(nodes: list[dict]) -> str:
    lines = []
    for n in nodes:
        parent = n.get("parent_feature_id") or "root"
        lines.append(
            f"ID: {n['id']} | Name: {n['name']!r} | Parent: {parent} | Desc: {n.get('description','')[:80]}"
        )
    return "\n".join(lines)


async def _call_llm_for_diff(
    nodes: list[dict],
    user_message: str,
    api_key: str | None,
) -> GraphFixDiff:
    system_prompt = (
        "You are a software architect helping restructure a product feature graph.\n"
        "The graph is a tree of software features with parent-child relationships.\n\n"
        "The user will describe changes they want. Return a JSON object with:\n"
        "- add_nodes: list of {name, description, parent_node_id (str or null for root)}\n"
        "- remove_node_ids: list of node IDs to delete (including their subtrees)\n"
        "- reparent: list of {node_id, new_parent_id (str or null to make root)}\n"
        "- explanation: short human-readable summary of what you are doing\n\n"
        "Rules:\n"
        "- Only reference node IDs that exist in the provided list.\n"
        "- If remove_node_ids includes a node, also include all its descendant IDs.\n"
        "- If the user's request cannot be fulfilled with these operations, return an empty diff "
        "and explain why in the explanation field.\n"
        "- Be conservative: only make the changes explicitly requested."
    )

    tree_context = _build_tree_context(nodes)
    user_prompt = (
        f"Current feature graph:\n{tree_context}\n\n"
        f"Requested change: {user_message}"
    )

    return await call_llm_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=GraphFixDiff,
        api_key=api_key,
    )


# ---------------------------------------------------------------------------
# Diff application
# ---------------------------------------------------------------------------


def _collect_descendants(node_id: str, child_map: dict[str, list[str]]) -> list[str]:
    result = []
    stack = [node_id]
    while stack:
        current = stack.pop()
        children = child_map.get(current, [])
        result.extend(children)
        stack.extend(children)
    return result


async def apply_graph_fix(
    repo_id: str,
    user_message: str,
    api_key: str | None = None,
) -> dict:
    """Generate and apply a graph fix diff. Returns updated graph dict."""
    from app.services.graph_version_service import save_snapshot
    from app.services.graph_cache import invalidate_graph_cache

    db = get_supabase()

    # Fetch latest analysis run
    run_result = (
        db.table("analysis_runs")
        .select("id")
        .eq("repo_id", repo_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    if not run_result.data:
        raise ValueError("No completed analysis run found")

    run_id = run_result.data[0]["id"]

    # Fetch current nodes
    nodes_result = (
        db.table("feature_nodes").select("*").eq("analysis_run_id", run_id).execute()
    )
    nodes = nodes_result.data or []

    if not nodes:
        raise ValueError("Graph has no nodes to fix")

    # Build child map for descendant resolution
    child_map: dict[str, list[str]] = {}
    for n in nodes:
        pid = n.get("parent_feature_id")
        if pid:
            child_map.setdefault(pid, []).append(n["id"])

    # Call LLM
    diff = await _call_llm_for_diff(nodes, user_message, api_key)

    # Expand remove_node_ids to include all descendants
    all_remove_ids: set[str] = set()
    for nid in diff.remove_node_ids:
        all_remove_ids.add(nid)
        all_remove_ids.update(_collect_descendants(nid, child_map))

    # Block if any node to remove has existing execution runs
    if all_remove_ids:
        exec_result = (
            db.table("execution_runs")
            .select("id, feature_suggestion_id")
            .execute()
        )
        exec_runs = exec_result.data or []

        # Get suggestion IDs for affected nodes
        sugg_result = (
            db.table("feature_suggestions")
            .select("id, feature_node_id")
            .in_("feature_node_id", list(all_remove_ids))
            .execute()
        )
        affected_suggestion_ids = {s["id"] for s in (sugg_result.data or [])}
        runs_for_affected = [
            r for r in exec_runs if r["feature_suggestion_id"] in affected_suggestion_ids
        ]
        if runs_for_affected:
            node_names = {n["id"]: n["name"] for n in nodes}
            blocked_names = [
                node_names.get(nid, nid)
                for nid in all_remove_ids
                if any(
                    r["feature_suggestion_id"] in affected_suggestion_ids
                    for r in runs_for_affected
                )
            ]
            raise ValueError(
                f"Cannot remove nodes with existing builds: {', '.join(blocked_names)}"
            )

    # Save snapshot before mutating
    save_snapshot(repo_id, run_id)

    # --- Apply removes ---
    if all_remove_ids:
        remove_list = list(all_remove_ids)
        # Delete suggestions for removed nodes
        db.table("feature_suggestions").delete().in_("feature_node_id", remove_list).execute()
        # Delete edges involving removed nodes
        db.table("feature_edges").delete().in_("source_node_id", remove_list).execute()
        db.table("feature_edges").delete().in_("target_node_id", remove_list).execute()
        # Delete nodes (children first via ordering — nodes without children first)
        # Sort so leaves are deleted before parents
        node_id_set = {n["id"] for n in nodes}
        ordered = [nid for nid in remove_list if nid in node_id_set]
        ordered.sort(key=lambda nid: -len(_collect_descendants(nid, child_map)))
        for nid in ordered:
            db.table("feature_nodes").delete().eq("id", nid).execute()

    # --- Apply reparents ---
    for rp in diff.reparent:
        if rp.node_id in all_remove_ids:
            continue
        db.table("feature_nodes").update(
            {"parent_feature_id": rp.new_parent_id}
        ).eq("id", rp.node_id).execute()
        # Replace tree edge
        db.table("feature_edges").delete().eq("target_node_id", rp.node_id).eq("edge_type", "tree").execute()
        if rp.new_parent_id:
            db.table("feature_edges").insert({
                "analysis_run_id": run_id,
                "source_node_id": rp.new_parent_id,
                "target_node_id": rp.node_id,
                "edge_type": "tree",
            }).execute()

    # --- Apply adds ---
    for add in diff.add_nodes:
        new_id = str(uuid.uuid4())
        db.table("feature_nodes").insert({
            "id": new_id,
            "analysis_run_id": run_id,
            "name": add.name,
            "description": add.description,
            "parent_feature_id": add.parent_node_id,
            "anchor_files": [],
        }).execute()
        if add.parent_node_id:
            db.table("feature_edges").insert({
                "analysis_run_id": run_id,
                "source_node_id": add.parent_node_id,
                "target_node_id": new_id,
                "edge_type": "tree",
            }).execute()

    # Invalidate cache and return fresh graph
    invalidate_graph_cache(repo_id)

    updated_nodes = (
        db.table("feature_nodes").select("*").eq("analysis_run_id", run_id).execute()
    )
    node_ids = [n["id"] for n in (updated_nodes.data or [])]
    updated_edges = (
        db.table("feature_edges")
        .select("*")
        .in_("source_node_id", node_ids)
        .execute()
    )
    tree_edges = [e for e in (updated_edges.data or []) if e.get("edge_type") == "tree"]

    return {
        "explanation": diff.explanation,
        "nodes": updated_nodes.data or [],
        "edges": tree_edges,
    }
