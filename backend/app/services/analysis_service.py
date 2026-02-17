"""Repository analysis: digest generation, file summaries, feature inference."""

import json
import os
from pathlib import Path

from pydantic import BaseModel

from app.db import get_supabase
from app.middleware.auth_middleware import require_auth
from app.services.llm_service import call_llm_structured_list

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "vendor",
    "__pycache__", ".venv", "venv", ".turbo", ".cache", "coverage",
}

CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".css",
    ".scss", ".html", ".md", ".yaml", ".yml", ".toml", ".prisma",
    ".graphql", ".gql", ".sql", ".env.example",
}

KEY_FILE_PATTERNS = {
    "package.json", "tsconfig.json", "README.md", "readme.md",
    ".env.example", "docker-compose.yml", "Dockerfile",
    "next.config.ts", "next.config.js", "next.config.mjs",
    "vite.config.ts", "vite.config.js",
    "tailwind.config.ts", "tailwind.config.js",
}

KEY_DIR_NAMES = {"pages", "routes", "api", "schema", "prisma", "models", "lib"}

FRAMEWORK_MARKERS = {
    "next": ["next"],
    "nuxt": ["nuxt"],
    "remix": ["@remix-run/react"],
    "gatsby": ["gatsby"],
    "vite": ["vite"],
    "express": ["express"],
    "fastify": ["fastify"],
    "nestjs": ["@nestjs/core"],
    "sveltekit": ["@sveltejs/kit"],
    "astro": ["astro"],
}

MAX_FILE_READ_BYTES = 30_000  # Cap individual file reads for LLM context

# ---------------------------------------------------------------------------
# Pydantic models for LLM structured output
# ---------------------------------------------------------------------------


class FileSummary(BaseModel):
    file_path: str
    summary: str
    role: str  # e.g. "page", "component", "api", "schema", "config", "util"


class InferredFeature(BaseModel):
    name: str
    description: str
    anchor_files: list[str] = []
    parent_feature: str | None = None
    related_features: list[str] = []


# ---------------------------------------------------------------------------
# Step 2: Generate Repo Digest (pure filesystem, no LLM)
# ---------------------------------------------------------------------------


async def generate_repo_digest(repo_path: str) -> dict:
    """Scan the repo and produce a structured digest.

    Returns a dict with:
      - file_tree: list of relative file paths
      - framework: detected framework name or None
      - dependencies: dict of dependency name -> version
      - dev_dependencies: dict of devDependency name -> version
      - scripts: dict of script name -> command
      - key_files: list of relative paths to important files
    """
    root = Path(repo_path)
    file_tree: list[str] = []
    key_files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune vendor directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        rel_dir = Path(dirpath).relative_to(root)

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in CODE_EXTENSIONS and fname not in KEY_FILE_PATTERNS:
                continue

            rel_path = str(rel_dir / fname).replace("\\", "/")
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]

            file_tree.append(rel_path)

            # Identify key files
            if fname in KEY_FILE_PATTERNS:
                key_files.append(rel_path)
            elif rel_dir.parts and rel_dir.parts[-1] in KEY_DIR_NAMES:
                key_files.append(rel_path)
            elif fname.endswith((".prisma", ".graphql", ".gql")):
                key_files.append(rel_path)

    # Parse package.json if it exists
    dependencies: dict[str, str] = {}
    dev_dependencies: dict[str, str] = {}
    scripts: dict[str, str] = {}
    framework: str | None = None

    pkg_path = root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            dependencies = pkg.get("dependencies", {})
            dev_dependencies = pkg.get("devDependencies", {})
            scripts = pkg.get("scripts", {})

            all_deps = {**dependencies, **dev_dependencies}
            for fw_name, markers in FRAMEWORK_MARKERS.items():
                if any(m in all_deps for m in markers):
                    framework = fw_name
                    break
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "file_tree": sorted(file_tree),
        "framework": framework,
        "dependencies": dependencies,
        "dev_dependencies": dev_dependencies,
        "scripts": scripts,
        "key_files": sorted(set(key_files)),
    }


# ---------------------------------------------------------------------------
# Step 3: File Summaries (LLM-powered)
# ---------------------------------------------------------------------------


async def _call_llm_for_summaries(
    file_contents: list[dict], api_key: str | None = None
) -> list[dict]:
    """Call the LLM to generate structured summaries for a batch of files."""
    system_prompt = (
        "You are a senior software engineer analyzing a codebase. "
        "For each file provided, produce a concise structured summary. "
        "Return a JSON object with a key 'summaries' containing a list. "
        "Each item must have: file_path (string), summary (1-2 sentence description), "
        "role (one of: page, component, api, schema, config, util, test, style, entry, other)."
    )

    user_content = "Summarize these files:\n\n"
    for fc in file_contents:
        user_content += f"--- {fc['path']} ---\n{fc['content'][:MAX_FILE_READ_BYTES]}\n\n"

    items = await call_llm_structured_list(
        system_prompt=system_prompt,
        user_prompt=user_content,
        item_model=FileSummary,
        list_key="summaries",
        api_key=api_key,
    )
    return [item.model_dump() for item in items]


async def summarize_files(
    repo_path: str, digest: dict, api_key: str | None = None
) -> list[dict]:
    """LLM-summarize relevant files into structured metadata.

    Reads each key file from disk, sends them in batches to the LLM,
    and returns a list of {file_path, summary, role} dicts.
    """
    key_files = digest.get("key_files", [])
    if not key_files:
        return []

    root = Path(repo_path)

    # Read file contents
    file_contents: list[dict] = []
    for rel_path in key_files:
        abs_path = root / rel_path
        if not abs_path.is_file():
            continue
        try:
            content = abs_path.read_text(encoding="utf-8", errors="ignore")
            file_contents.append({"path": rel_path, "content": content})
        except OSError:
            continue

    if not file_contents:
        return []

    # Batch into chunks of ~15 files to stay within context limits
    batch_size = 15
    all_summaries: list[dict] = []
    for i in range(0, len(file_contents), batch_size):
        batch = file_contents[i : i + batch_size]
        summaries = await _call_llm_for_summaries(batch, api_key=api_key)
        all_summaries.extend(summaries)

    return all_summaries


# ---------------------------------------------------------------------------
# Step 4: Feature Inference (LLM-powered, stores to Supabase)
# ---------------------------------------------------------------------------


async def _call_llm_for_features(
    digest: dict, file_summaries: list[dict], api_key: str | None = None
) -> list[dict]:
    """Call the LLM to infer feature nodes from the repo digest + summaries."""
    system_prompt = (
        "You are a senior software architect analyzing a codebase to identify "
        "its feature topology. Given the file tree, framework, dependencies, "
        "and file summaries, identify all distinct features in the codebase.\n\n"
        "Return a JSON object with key 'features' containing a list. "
        "Each feature must have:\n"
        "- name (string): concise feature name\n"
        "- description (string): 1-2 sentence explanation\n"
        "- anchor_files (list[string]): relative file paths most related to this feature\n"
        "- parent_feature (string|null): name of parent feature if this is a sub-feature\n"
        "- related_features (list[string]): names of related features\n\n"
        "Generate as many features as the codebase warrants. "
        "Organize them hierarchically where appropriate. "
        "Top-level features should have parent_feature = null."
    )

    user_content = (
        f"Framework: {digest.get('framework', 'unknown')}\n"
        f"Dependencies: {json.dumps(digest.get('dependencies', {}))}\n"
        f"Scripts: {json.dumps(digest.get('scripts', {}))}\n"
        f"File tree:\n{chr(10).join(digest.get('file_tree', []))}\n\n"
        f"File summaries:\n"
    )
    for s in file_summaries:
        user_content += f"- {s['file_path']}: {s['summary']} (role: {s['role']})\n"

    items = await call_llm_structured_list(
        system_prompt=system_prompt,
        user_prompt=user_content,
        item_model=InferredFeature,
        list_key="features",
        api_key=api_key,
    )
    return [item.model_dump() for item in items]


async def infer_features(
    run_id: str, digest: dict, file_summaries: list[dict],
    api_key: str | None = None,
) -> dict:
    """LLM-infer feature nodes and edges, then store them in Supabase.

    Returns {"nodes": [...], "edges": [...]}.
    """
    raw_features = await _call_llm_for_features(digest, file_summaries, api_key=api_key)

    if not raw_features:
        return {"nodes": [], "edges": []}

    db = get_supabase()

    # --- Insert feature nodes ---
    # First pass: insert all nodes without parent refs to get their IDs
    name_to_id: dict[str, str] = {}
    all_nodes: list[dict] = []

    node_rows = [
        {
            "analysis_run_id": run_id,
            "name": f["name"],
            "description": f["description"],
            "anchor_files": f["anchor_files"],
        }
        for f in raw_features
    ]

    result = db.table("feature_nodes").insert(node_rows).execute()
    inserted = result.data

    for row in inserted:
        name_to_id[row["name"]] = row["id"]
        all_nodes.append(row)

    # Second pass: set parent_feature_id where applicable
    for f in raw_features:
        if f["parent_feature"] and f["parent_feature"] in name_to_id:
            child_id = name_to_id.get(f["name"])
            parent_id = name_to_id[f["parent_feature"]]
            if child_id:
                db.table("feature_nodes").update(
                    {"parent_feature_id": parent_id}
                ).eq("id", child_id).execute()

    # --- Insert edges ---
    edges_to_insert: list[dict] = []

    for f in raw_features:
        node_id = name_to_id.get(f["name"])
        if not node_id:
            continue

        # Tree edge to parent
        if f["parent_feature"] and f["parent_feature"] in name_to_id:
            parent_id = name_to_id[f["parent_feature"]]
            edges_to_insert.append({
                "source_node_id": parent_id,
                "target_node_id": node_id,
                "edge_type": "tree",
            })

        # Related edges
        for related_name in f.get("related_features", []):
            related_id = name_to_id.get(related_name)
            if related_id and related_id != node_id:
                edges_to_insert.append({
                    "source_node_id": node_id,
                    "target_node_id": related_id,
                    "edge_type": "related",
                })

    all_edges: list[dict] = []
    if edges_to_insert:
        # Deduplicate edges
        seen = set()
        unique_edges = []
        for e in edges_to_insert:
            key = (e["source_node_id"], e["target_node_id"], e["edge_type"])
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)

        edge_result = db.table("feature_edges").insert(unique_edges).execute()
        all_edges = edge_result.data

    return {"nodes": all_nodes, "edges": all_edges}
