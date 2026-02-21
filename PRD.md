PRODUCT REQUIREMENTS DOCUMENT
Product Evolution Engine (PEE)
Hackathon v1 — LLM-First + Claude Code Autonomous Execution

1. Product Definition
   Product Evolution Engine is an AI-native developer tool that:
   Analyzes a GitHub repository

Reconstructs it into a tree-like feature graph

Suggests related feature expansions when a node is clicked

Simulates three global future development branches with tradeoffs

Automatically implements selected features in a sandbox using Claude Code

Opens a deploy-ready pull request without manual prompting

Target user: Solo indie developer.
Core identity:
Feature topology visualizer + strategic simulator + autonomous feature builder

2. Scope Constraints
   Single GitHub repo

Max 100k LOC

Full re-ingest per analysis

No AST parsing

LLM-only structural reasoning

Filesystem sandbox only

Fully autonomous Claude Code execution (headless)

Optional live log streaming

3. System Architecture
   3.1 Components
   Frontend:
   React

React Flow (feature graph)

Side panel (suggestions + branch view)

Execution status modal

Backend:
API server

Worker process for analysis + execution

Postgres for persistence

GitHub API integration

Claude Code CLI integration (local)

LLM Provider:
Hosted model for analysis + suggestions + branches

Claude Code CLI for autonomous implementation

4. Core Functional Modules

Module A — Repository Analysis
Step 1: Clone Repo
Clone into working directory

Reject if LOC > 100k

Step 2: Generate Repository Digest
Collect:
File tree

Detected framework

Key files (routes, pages, schema, README)

Dependencies list

Package.json scripts

Step 3: File Summaries
LLM summarizes relevant files into structured metadata.
Step 4: Feature Inference (Unlimited)
LLM generates feature nodes:
Each node includes:
name

short description

anchor files

parent_feature (optional)

related_features

Unlimited nodes allowed.
UI must:
Collapse subtrees by default

Support expand/collapse interactions

Graph is tree-primary with optional secondary relations.

Module B — Feature Node Interaction
When user clicks a node:
System generates:
3–8 related feature expansions

Risk hotspots for that feature

Each suggestion includes:
Name

Why it fits

Estimated complexity

Impacted files (approximate)

Suggested test cases

Implementation sketch

Module C — Strategic Future Simulation
User clicks “Simulate Futures”.
System generates exactly 3 branches.
Each branch includes:
Structured JSON:
branch_name

theme

initiatives (3–6)

architecture_impact

scalability_impact

risk_impact

tradeoffs

recommended_execution_order

Plus:
Readable narrative explanation.
Branches must differ philosophically:
Expansion-focused

Stability/refactor-focused

Strategic pivot

Module D — Autonomous Feature Implementation
This is the core differentiator.
When user clicks “Auto Build”:
Execution Flow
Create sandbox:
/sandboxes/{repo}/{run_id}

Clone repo into sandbox

Create new branch

Generate Plan.md

Generate tests (tests-first requirement)

Invoke Claude Code (headless)

Claude Code receives:
Plan

Test files

Strict scope boundaries

File change limit

Prohibited directories

Verification Loop
System runs:
npm test or detected test script

npm run lint if exists

npm run typecheck if exists

If failure:
Generate fix prompt

Reinvoke Claude Code

Max 2 iterations

Success Path
Commit changes

Push branch

Open PR via GitHub API

PR includes:
Plan summary

Test results

Files changed

LLM self-review summary

5. Claude Code Execution Model
   Mode: Fully autonomous headless
   Constraints:
   Max 25 files changed

Cannot modify:

.env

deployment configs

CI configs

Must stay within feature-related scope

Must not delete unrelated files

Prompt design must explicitly encode constraints.

6. Optional Enhancement — Live Log Streaming
   Although headless by default, system can:
   Stream stdout/stderr from:

Claude Code

Test commands

Git operations

UI shows:
“Analyzing…”

“Writing tests…”

“Fix iteration 1…”

“Running lint…”

Logs displayed in collapsible terminal panel.
This increases demo impact significantly.
Nice-to-have, not blocking.

7. Risk Engine
   Each feature node receives:
   Risk score (0–100) based on:
   File size

Test presence

Dependency age

LLM structural reasoning

Badge colors:
Green / Yellow / Red
Risk also influences:
Branch reasoning

Suggestion prioritization

8. Data Model (Postgres)
   Tables:
   users
   repos
   analysis_runs
   feature_nodes
   feature_edges
   feature_risks
   feature_suggestions
   strategic_branches
   execution_runs
   execution_logs
   No raw source code stored.

9. Guardrails Against Chaos
   Since LLM-only + autonomous code is volatile:
   Strict JSON schema validation

Retry malformed LLM outputs

Hard iteration cap (2 fix loops)

Max runtime cap per execution

Scope-bound prompts

File change limit enforcement

10. Demo Success Criteria
    Project is considered successful if:
    Repo → graph generated

Click feature → related suggestions appear

Click “Auto Build Wishlist”

Claude Code runs

Tests pass

PR opens automatically

That moment sells the entire system.
