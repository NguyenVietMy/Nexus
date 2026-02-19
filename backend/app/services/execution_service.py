"""Autonomous feature implementation via Claude Code CLI.

Orchestrates two phases:
  Phase 1 (plan): Clone, generate Plan.md + tests, await user approval
  Phase 2 (build): Invoke Claude Code, verify, retry, commit/push/PR
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from app.config import settings
from app.db import get_supabase
from app.services.github_service import (
    clone_repo,
    create_branch,
    commit_and_push,
    open_pull_request,
)
from app.services.llm_service import call_llm_structured

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for plan generation
# ---------------------------------------------------------------------------


class ImplementationPlan(BaseModel):
    plan: str
    test_code: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _update_status(run_id: str, status: str, **extra_fields) -> None:
    """Update execution run status in Supabase."""
    db = get_supabase()
    payload = {"status": status, **extra_fields}
    db.table("execution_runs").update(payload).eq("id", run_id).execute()


def _log(run_id: str, step: str, message: str, level: str = "info") -> None:
    """Write an execution log entry to Supabase."""
    db = get_supabase()
    db.table("execution_logs").insert(
        {
            "execution_run_id": run_id,
            "step": step,
            "message": message,
            "log_level": level,
        }
    ).execute()


def _slugify(name: str) -> str:
    """Convert a feature name to a branch-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return slug[:50]


# ---------------------------------------------------------------------------
# Step 1: Clone into sandbox
# ---------------------------------------------------------------------------


async def _clone_to_sandbox(
    github_url: str,
    repo_name: str,
    run_id: str,
    sandbox_base: str | None = None,
) -> str:
    """Clone the repo into a sandbox directory. Returns the sandbox path."""
    base = sandbox_base or settings.sandbox_base_dir
    sandbox_path = str(Path(base) / repo_name / run_id)
    os.makedirs(sandbox_path, exist_ok=True)
    clone_repo(github_url, target_dir=sandbox_path)
    return sandbox_path


# ---------------------------------------------------------------------------
# Step 2: Generate Plan.md + test file via OpenAI
# ---------------------------------------------------------------------------


async def _generate_plan(
    suggestion: dict,
    digest: dict | None,
    api_key: str | None = None,
) -> str:
    """Generate a Plan.md string for Claude Code to follow."""
    system_prompt = (
        "You are a senior engineer writing an implementation plan for an AI coding agent. "
        "Write a clear, step-by-step Plan.md that the agent will follow to implement the feature. "
        "Include:\n"
        "- Feature name and description\n"
        "- Files to create or modify\n"
        "- Step-by-step implementation instructions\n"
        "- Constraints: do NOT modify .env, CI configs, or deployment configs\n"
        "- Max 25 files changed\n\n"
        "Return a JSON object with key 'plan' containing the markdown plan text, "
        "and key 'test_code' containing test file contents."
    )

    user_content = (
        f"Feature: {suggestion['name']}\n"
        f"Rationale: {suggestion['rationale']}\n"
        f"Complexity: {suggestion['complexity']}\n"
        f"Impacted files: {json.dumps(suggestion.get('impacted_files', []))}\n"
        f"Implementation sketch: {suggestion.get('implementation_sketch', 'N/A')}\n"
        f"Test cases: {json.dumps(suggestion.get('test_cases', []))}\n"
    )

    if digest:
        user_content += (
            f"\nRepo context:\n"
            f"Framework: {digest.get('framework', 'unknown')}\n"
            f"Dependencies: {json.dumps(digest.get('dependencies', {}))}\n"
            f"Scripts: {json.dumps(digest.get('scripts', {}))}\n"
        )

    result = await call_llm_structured(
        system_prompt=system_prompt,
        user_prompt=user_content,
        response_model=ImplementationPlan,
        api_key=api_key,
    )
    return result.plan


async def _generate_test_file(
    suggestion: dict,
    digest: dict | None = None,
    api_key: str | None = None,
) -> str:
    """Generate test file contents via OpenAI."""
    framework = (digest.get("framework") or "unknown") if digest else "unknown"
    dependencies = digest.get("dependencies", {}) if digest else {}

    # Determine test framework from project context
    is_python = (
        "fastapi" in framework.lower()
        or "django" in framework.lower()
        or "flask" in framework.lower()
        or "pytest" in str(dependencies).lower()
        or any(k in dependencies for k in ("fastapi", "django", "flask", "pytest"))
    )
    if is_python:
        test_framework_hint = (
            "Use pytest for Python. Write a .py test file using pytest conventions "
            "(def test_..., use httpx.AsyncClient or TestClient for FastAPI). "
            "Do NOT use Jest, supertest, or any JavaScript testing library."
        )
    else:
        test_framework_hint = (
            "Use jest/vitest for JavaScript/TypeScript. "
            "Do NOT use pytest or any Python testing library."
        )

    system_prompt = (
        "You are a senior test engineer. Write test code for the described feature. "
        f"{test_framework_hint} "
        "Return a JSON object with key 'plan' containing a brief note and "
        "'test_code' containing the full test file contents."
    )

    user_content = (
        f"Feature: {suggestion['name']}\n"
        f"Framework: {framework}\n"
        f"Test cases to cover:\n"
        + "\n".join(f"- {tc}" for tc in suggestion.get("test_cases", []))
    )

    result = await call_llm_structured(
        system_prompt=system_prompt,
        user_prompt=user_content,
        response_model=ImplementationPlan,
        api_key=api_key,
    )
    return result.test_code or ""


# ---------------------------------------------------------------------------
# Step 3: Invoke Claude Code CLI
# ---------------------------------------------------------------------------


def _resolve_claude_cmd() -> list[str]:
    """Resolve the claude executable for subprocess. Handles Windows/npm PATH issues."""
    claude_path = shutil.which("claude")
    if claude_path:
        return [claude_path]
    # Fallback: npx finds the package even when PATH doesn't include npm globals
    if sys.platform == "win32":
        npx_claude = shutil.which("npx")
        if npx_claude:
            return [npx_claude, "claude"]
    return ["claude"]


def _get_claude_live_log_path() -> Path:
    """Path to the live log file. Tail this in a separate terminal to watch Claude."""
    base = Path(settings.sandbox_base_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base / "claude_live.log"


def _parse_stream_json_line(raw_line: str) -> str | None:
    """Parse a single stream-json line into human-readable text.

    Returns a readable string, or None if the line should be skipped.
    """
    line = raw_line.strip()
    if not line:
        return None

    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        # Not JSON — return as-is (could be stderr or non-json output)
        return line.strip() if line.strip() else None

    event_type = event.get("type")

    # Assistant messages: text and tool_use
    if event_type == "assistant":
        message = event.get("message", {})
        content_blocks = message.get("content", [])
        parts = []
        for block in content_blocks:
            block_type = block.get("type")
            if block_type == "text":
                text = block.get("text", "").strip()
                if text:
                    parts.append(text)
            elif block_type == "tool_use":
                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                if tool_name == "Read":
                    parts.append(f"[Reading] {tool_input.get('file_path', '?')}")
                elif tool_name == "Edit":
                    parts.append(f"[Editing] {tool_input.get('file_path', '?')}")
                elif tool_name == "Write":
                    parts.append(f"[Writing] {tool_input.get('file_path', '?')}")
                elif tool_name == "Bash":
                    cmd = tool_input.get("command", "?")
                    # Truncate long commands
                    if len(cmd) > 200:
                        cmd = cmd[:200] + "..."
                    parts.append(f"[Running] {cmd}")
                else:
                    parts.append(f"[{tool_name}] {json.dumps(tool_input)[:200]}")
        return "\n".join(parts) if parts else None

    # Tool results
    if event_type == "user":
        message = event.get("message", {})
        content_blocks = message.get("content", [])
        parts = []
        for block in content_blocks:
            if block.get("type") == "tool_result":
                output = block.get("content", "")
                if isinstance(output, list):
                    # Content can be a list of text blocks
                    output = " ".join(
                        b.get("text", "") for b in output if b.get("type") == "text"
                    )
                if output:
                    # Truncate large outputs
                    truncated = output[:500]
                    if len(output) > 500:
                        truncated += f"... ({len(output)} chars total)"
                    parts.append(f"  -> {truncated}")
        return "\n".join(parts) if parts else None

    # Result event (final)
    if event_type == "result":
        result_text = event.get("result", "")
        if result_text:
            truncated = result_text[:500]
            if len(result_text) > 500:
                truncated += "..."
            return f"[Result] {truncated}"
        return None

    # Skip system, ping, and other event types
    return None


def _run_claude_sync(
    cmd: list[str], cwd: str, env: dict, timeout: int, run_id: str
) -> tuple[int, str, str]:
    """Run Claude Code CLI with live streaming to file.

    Parses stream-json output into human-readable text.
    Streams parsed output to sandboxes/claude_live.log in real-time
    and inserts log entries into the database as they arrive.

    Run `tail -f backend/sandboxes/claude_live.log` in a separate terminal
    to watch Claude work.

    Returns (returncode, stdout, stderr).
    """
    log_path = _get_claude_live_log_path()
    full_stdout: list[str] = []
    full_stderr: list[str] = []
    file_lock = threading.Lock()

    def read_stdout(pipe) -> None:
        """Read stdout, parse stream-json, write readable output."""
        try:
            for line in iter(pipe.readline, b""):
                raw = line.decode("utf-8", errors="replace")
                full_stdout.append(raw)
                parsed = _parse_stream_json_line(raw)
                if parsed:
                    with file_lock:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(parsed + "\n")
                    # Also insert into DB for frontend polling
                    try:
                        _log(run_id, "claude_code", parsed)
                    except Exception:
                        pass  # Don't let DB errors kill the stream reader
        except Exception:
            pass
        finally:
            pipe.close()

    def read_stderr(pipe) -> None:
        """Read stderr and write to log file."""
        try:
            for line in iter(pipe.readline, b""):
                text = line.decode("utf-8", errors="replace").strip()
                if text:
                    full_stderr.append(text)
                    with file_lock:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(f"[stderr] {text}\n")
        except Exception:
            pass
        finally:
            pipe.close()

    # Clear and write header at start
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== Claude Code run {run_id} ===\n\n")

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
    )

    t1 = threading.Thread(target=read_stdout, args=(proc.stdout,))
    t2 = threading.Thread(target=read_stderr, args=(proc.stderr,))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    try:
        returncode = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise
    finally:
        t1.join(timeout=5)
        t2.join(timeout=5)

    stdout_text = "".join(full_stdout)
    stderr_text = "".join(full_stderr)
    return returncode, stdout_text, stderr_text


async def _invoke_claude_code(
    sandbox_path: str,
    prompt: str,
    run_id: str,
) -> bool:
    """Invoke the Claude Code CLI in headless mode.

    Returns True if the process exits successfully.
    """
    claude_cmd = _resolve_claude_cmd()
    cmd = [
        *claude_cmd,
        "-p", prompt,
        "--allowedTools", "Read,Edit,Write,Bash",
        "--output-format", "stream-json",
        "--verbose",
    ]
    env = os.environ.copy()
    timeout = settings.claude_code_timeout
    log_path = _get_claude_live_log_path()
    logger.info(f"Claude Code live log: {log_path}")
    _log(run_id, "build", f"Live log: {log_path}", level="info")

    try:
        returncode, stdout_text, stderr_text = await asyncio.wait_for(
            asyncio.to_thread(
                _run_claude_sync, cmd, sandbox_path, env, timeout, run_id
            ),
            timeout=timeout + 10,
        )

        if stderr_text:
            _log(run_id, "claude_code", stderr_text[:2000], level="warn")

        if returncode != 0:
            _log(
                run_id,
                "claude_code",
                f"Exit code {returncode}",
                level="error",
            )
            return False

        return True

    except asyncio.TimeoutError:
        _log(
            run_id,
            "claude_code",
            f"Claude Code timed out after {timeout}s",
            level="error",
        )
        return False
    except FileNotFoundError as e:
        _log(
            run_id,
            "claude_code",
            f"Claude Code CLI not found: {e}. "
            "Install via https://claude.ai/download or ensure 'claude' is in PATH.",
            level="error",
        )
        return False
    except subprocess.TimeoutExpired:
        _log(
            run_id,
            "claude_code",
            f"Claude Code timed out after {timeout}s",
            level="error",
        )
        return False
    except Exception as e:
        _log(
            run_id,
            "claude_code",
            f"Claude Code error: {type(e).__name__}: {e}",
            level="error",
        )
        logger.exception("Claude Code invocation failed")
        return False


# ---------------------------------------------------------------------------
# Step 4: Run verification commands
# ---------------------------------------------------------------------------


async def _run_command(
    cmd: str, cwd: str, timeout: int = 120
) -> tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace") if stdout else "",
            stderr.decode("utf-8", errors="replace") if stderr else "",
        )
    except asyncio.TimeoutError:
        return (1, "", f"Command timed out after {timeout}s")
    except Exception as e:
        return (1, "", str(e))


async def _run_verification(
    sandbox_path: str,
    scripts: dict[str, str],
) -> bool:
    """Run npm test/lint/typecheck if they exist. Returns True if all pass."""
    checks = ["test", "lint", "typecheck"]

    for check in checks:
        if check not in scripts:
            continue

        exit_code, stdout, stderr = await _run_command(
            f"npm run {check}", cwd=sandbox_path
        )

        if exit_code != 0:
            logger.warning(f"Verification '{check}' failed: {stderr[:500]}")
            return False

    return True


# ---------------------------------------------------------------------------
# Step 5: Commit, push, open PR
# ---------------------------------------------------------------------------


async def _commit_push_pr(
    sandbox_path: str,
    github_url: str,
    branch_name: str,
    suggestion: dict,
    plan: str,
    run_id: str,
) -> str:
    """Commit changes, push branch, open PR. Returns the PR URL."""
    commit_message = f"feat: {suggestion['name']}\n\nAuto-implemented by Product Evolution Engine"

    commit_and_push(sandbox_path, commit_message, branch_name)

    pr_body = (
        f"## Auto-implemented: {suggestion['name']}\n\n"
        f"**Rationale:** {suggestion['rationale']}\n\n"
        f"**Complexity:** {suggestion['complexity']}\n\n"
        f"### Plan\n\n{plan[:2000]}\n\n"
        f"---\n"
        f"*Generated by [Product Evolution Engine](https://github.com/)*"
    )

    pr_url = open_pull_request(
        github_url=github_url,
        branch_name=branch_name,
        title=f"feat: {suggestion['name']}",
        body=pr_body,
    )

    return pr_url


# ---------------------------------------------------------------------------
# Phase 1: Plan generation (stops at awaiting_approval)
# ---------------------------------------------------------------------------


async def execute_plan_phase(execution_run_id: str) -> None:
    """Run the plan generation phase only.

    Steps:
      1. Fetch context (execution run, suggestion, repo)
      2. Clone repo into sandbox, create branch
      3. Generate Plan.md + tests via OpenAI
      4. Save plan to DB, set status to awaiting_approval
    """
    db = get_supabase()

    try:
        # ---- Fetch context ----
        exec_run = db.table("execution_runs").select("*").eq("id", execution_run_id).execute().data[0]
        suggestion = db.table("feature_suggestions").select("*").eq("id", exec_run["feature_suggestion_id"]).execute().data[0]
        repo = db.table("repos").select("*").eq("id", exec_run["repo_id"]).execute().data[0]

        github_url = repo["github_url"]
        repo_name = repo["name"]
        feature_slug = _slugify(suggestion["name"])
        run_suffix = execution_run_id.replace("-", "")[:8]
        branch_name = f"pee/feature-{feature_slug}-{run_suffix}"

        # Try to get the digest for context
        digest = None
        try:
            run_result = db.table("analysis_runs").select("digest_json").eq("repo_id", repo["id"]).eq("status", "completed").order("completed_at", desc=True).limit(1).execute()
            if run_result.data:
                digest = run_result.data[0].get("digest_json")
        except Exception:
            pass

        # ---- Step 1: Clone into sandbox ----
        _update_status(execution_run_id, "cloning")
        _log(execution_run_id, "clone", f"Cloning {github_url} into sandbox")

        sandbox_path = await _clone_to_sandbox(
            github_url, repo_name, execution_run_id
        )
        _update_status(execution_run_id, "cloning", sandbox_path=sandbox_path)

        # Create feature branch
        create_branch(sandbox_path, branch_name)
        _update_status(execution_run_id, "cloning", branch_name=branch_name)
        _log(execution_run_id, "clone", f"Created branch {branch_name}")

        # ---- Step 2: Generate plan + tests ----
        _update_status(execution_run_id, "planning")
        _log(execution_run_id, "plan", "Generating implementation plan via OpenAI")

        plan = await _generate_plan(suggestion, digest)

        # Write Plan.md to sandbox
        plan_path = Path(sandbox_path) / "Plan.md"
        plan_path.write_text(plan, encoding="utf-8")
        _log(execution_run_id, "plan", "Plan.md written to sandbox")

        # Generate and write test file
        _update_status(execution_run_id, "testing")
        _log(execution_run_id, "tests", "Generating test file via OpenAI")

        test_code = await _generate_test_file(suggestion, digest=digest)
        # Derive test path from framework so Python gets pytest, JS gets Jest
        framework = ((digest.get("framework") or "") if digest else "").lower()
        is_python = any(f in framework for f in ("fastapi", "django", "flask")) or \
                    any(k in (digest.get("dependencies", {}) if digest else {})
                        for k in ("fastapi", "django", "flask", "pytest"))
        if is_python:
            test_path = Path(sandbox_path) / f"tests/test_{feature_slug}.py"
        else:
            test_path = Path(sandbox_path) / f"__tests__/{feature_slug}.test.ts"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(test_code, encoding="utf-8")
        _log(execution_run_id, "tests", f"Test file written: {test_path.name}")

        # ---- Save plan and wait for approval ----
        _update_status(execution_run_id, "awaiting_approval", plan_md=plan)
        _log(execution_run_id, "plan", "Plan ready for review. Awaiting approval.")

        logger.info(f"Plan phase completed for {execution_run_id}. Awaiting user approval.")

    except Exception as e:
        logger.exception(f"Plan phase failed for {execution_run_id}: {e}")
        _update_status(execution_run_id, "failed")
        _log(execution_run_id, "error", str(e), level="error")


# ---------------------------------------------------------------------------
# Phase 2: Build (invoked after user approves the plan)
# ---------------------------------------------------------------------------


async def execute_build_phase(execution_run_id: str) -> None:
    """Run the build phase after user approval.

    Steps:
      1. Fetch context (sandbox path, suggestion, repo, plan)
      2. Invoke Claude Code CLI
      3. Run verification (test/lint/typecheck)
      4. Retry on failure (up to max_fix_iterations)
      5. Commit, push, open PR
      6. Clean up sandbox
    """
    db = get_supabase()

    try:
        # ---- Fetch context ----
        exec_run = db.table("execution_runs").select("*").eq("id", execution_run_id).execute().data[0]
        suggestion = db.table("feature_suggestions").select("*").eq("id", exec_run["feature_suggestion_id"]).execute().data[0]
        repo = db.table("repos").select("*").eq("id", exec_run["repo_id"]).execute().data[0]

        sandbox_path = exec_run["sandbox_path"]
        branch_name = exec_run["branch_name"]
        plan = exec_run.get("plan_md", "")
        github_url = repo["github_url"]
        feature_slug = _slugify(suggestion["name"])

        # Get digest for scripts info
        digest = None
        try:
            run_result = db.table("analysis_runs").select("digest_json").eq("repo_id", repo["id"]).eq("status", "completed").order("completed_at", desc=True).limit(1).execute()
            if run_result.data:
                digest = run_result.data[0].get("digest_json")
        except Exception:
            pass

        scripts = digest.get("scripts", {}) if digest else {}

        # Derive test path to tell Claude where the tests are
        framework = ((digest.get("framework") or "") if digest else "").lower()
        is_python = any(f in framework for f in ("fastapi", "django", "flask")) or \
                    any(k in (digest.get("dependencies", {}) if digest else {})
                        for k in ("fastapi", "django", "flask", "pytest"))
        if is_python:
            test_file_ref = f"tests/test_{feature_slug}.py"
        else:
            test_file_ref = f"__tests__/{feature_slug}.test.ts"

        # ---- Build + verify loop ----
        max_iterations = settings.max_fix_iterations
        iteration = 0
        success = False

        while iteration <= max_iterations:
            _update_status(execution_run_id, "building", iteration_count=iteration)

            if iteration == 0:
                prompt = (
                    f"Implement the feature described in Plan.md. "
                    f"Follow the plan step by step. "
                    f"Run the tests in {test_file_ref}. "
                    f"Do not modify .env, CI configs, or deployment configs. "
                    f"Max 25 files changed."
                )
            else:
                prompt = (
                    f"The previous implementation attempt failed verification. "
                    f"Fix the issues and ensure all tests pass. "
                    f"Review Plan.md for the original requirements. "
                    f"Do not modify .env, CI configs, or deployment configs."
                )

            _log(execution_run_id, "build", f"Invoking Claude Code (iteration {iteration})")
            claude_ok = await _invoke_claude_code(sandbox_path, prompt, execution_run_id)

            if not claude_ok:
                _log(execution_run_id, "build", f"Claude Code returned non-zero (iteration {iteration})", level="warn")

            # Verify
            _update_status(execution_run_id, "verifying")
            _log(execution_run_id, "verify", f"Running verification (iteration {iteration})")

            verified = await _run_verification(sandbox_path, scripts)

            if verified:
                _log(execution_run_id, "verify", "All checks passed!")
                success = True
                break
            else:
                _log(execution_run_id, "verify", f"Verification failed (iteration {iteration})", level="warn")
                iteration += 1

        if not success:
            _update_status(execution_run_id, "failed")
            _log(execution_run_id, "done", f"Failed after {max_iterations + 1} attempts", level="error")
            return

        # ---- Commit, push, open PR ----
        _update_status(execution_run_id, "pushing")
        _log(execution_run_id, "push", "Committing and pushing changes")

        pr_url = await _commit_push_pr(
            sandbox_path, github_url, branch_name, suggestion, plan, execution_run_id
        )

        _update_status(execution_run_id, "done", pr_url=pr_url)
        _log(execution_run_id, "done", f"PR opened: {pr_url}")

        logger.info(f"Execution {execution_run_id} completed. PR: {pr_url}")

        # Clean up sandbox only on success
        if sandbox_path:
            try:
                shutil.rmtree(sandbox_path, ignore_errors=True)
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"Build phase failed for {execution_run_id}: {e}")
        _update_status(execution_run_id, "failed")
        _log(execution_run_id, "error", str(e), level="error")
        # Sandbox is preserved on failure for retry


def _get_recent_error_logs(run_id: str, limit: int = 10) -> str:
    """Fetch the most recent error/warn logs for a run to inject into retry prompt."""
    db = get_supabase()
    result = (
        db.table("execution_logs")
        .select("step,message,log_level")
        .eq("execution_run_id", run_id)
        .in_("log_level", ["error", "warn"])
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    if not result.data:
        return ""
    lines = []
    for log in reversed(result.data):
        lines.append(f"[{log['log_level'].upper()}] [{log['step']}] {log['message']}")
    return "\n".join(lines)


async def retry_build_phase(execution_run_id: str) -> None:
    """Retry the build phase with error context from the previous attempt.

    Re-uses the existing sandbox. Resets status to 'building' and
    injects previous error logs into the Claude Code prompt.
    """
    db = get_supabase()

    try:
        exec_run = db.table("execution_runs").select("*").eq("id", execution_run_id).execute().data[0]
        suggestion = db.table("feature_suggestions").select("*").eq("id", exec_run["feature_suggestion_id"]).execute().data[0]
        repo = db.table("repos").select("*").eq("id", exec_run["repo_id"]).execute().data[0]

        sandbox_path = exec_run["sandbox_path"]
        branch_name = exec_run["branch_name"]
        plan = exec_run.get("plan_md", "")
        github_url = repo["github_url"]
        feature_slug = _slugify(suggestion["name"])

        if not sandbox_path or not Path(sandbox_path).exists():
            _update_status(execution_run_id, "failed")
            _log(execution_run_id, "error", "Sandbox no longer exists. Cannot retry.", level="error")
            return

        # Update Plan.md in sandbox in case user edited it
        plan_path = Path(sandbox_path) / "Plan.md"
        plan_path.write_text(plan, encoding="utf-8")

        # Get previous error context
        error_context = _get_recent_error_logs(execution_run_id)

        # Get digest for scripts
        digest = None
        try:
            run_result = db.table("analysis_runs").select("digest_json").eq("repo_id", repo["id"]).eq("status", "completed").order("completed_at", desc=True).limit(1).execute()
            if run_result.data:
                digest = run_result.data[0].get("digest_json")
        except Exception:
            pass

        scripts = digest.get("scripts", {}) if digest else {}

        # Derive test path from framework
        framework = ((digest.get("framework") or "") if digest else "").lower()
        is_python = any(f in framework for f in ("fastapi", "django", "flask")) or \
                    any(k in (digest.get("dependencies", {}) if digest else {})
                        for k in ("fastapi", "django", "flask", "pytest"))
        test_file_ref = f"tests/test_{feature_slug}.py" if is_python else f"__tests__/{feature_slug}.test.ts"

        # Regenerate test file — the previous attempt may have had a wrong framework
        _log(execution_run_id, "tests", "Regenerating test file with corrected framework detection")
        test_code = await _generate_test_file(suggestion, digest=digest)
        test_path = Path(sandbox_path) / test_file_ref
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(test_code, encoding="utf-8")
        _log(execution_run_id, "tests", f"Test file regenerated: {test_path.name}")

        # Build with error context
        _update_status(execution_run_id, "building", iteration_count=0)
        _log(execution_run_id, "build", "Retrying build with error context from previous attempt")

        prompt = (
            f"Implement the feature described in Plan.md. "
            f"Follow the plan step by step. "
            f"Run the tests in {test_file_ref}. "
            f"Do not modify .env, CI configs, or deployment configs. "
            f"Max 25 files changed."
        )
        if error_context:
            prompt += (
                f"\n\nIMPORTANT: The previous build attempt failed with these errors. "
                f"Fix these issues:\n{error_context}"
            )

        max_iterations = settings.max_fix_iterations
        iteration = 0
        success = False

        while iteration <= max_iterations:
            _update_status(execution_run_id, "building", iteration_count=iteration)
            _log(execution_run_id, "build", f"Invoking Claude Code (retry iteration {iteration})")

            claude_ok = await _invoke_claude_code(sandbox_path, prompt, execution_run_id)

            if not claude_ok:
                _log(execution_run_id, "build", f"Claude Code returned non-zero (iteration {iteration})", level="warn")

            _update_status(execution_run_id, "verifying")
            _log(execution_run_id, "verify", f"Running verification (iteration {iteration})")

            verified = await _run_verification(sandbox_path, scripts)

            if verified:
                _log(execution_run_id, "verify", "All checks passed!")
                success = True
                break
            else:
                _log(execution_run_id, "verify", f"Verification failed (iteration {iteration})", level="warn")
                iteration += 1
                # Update prompt for next iteration
                prompt = (
                    f"The previous implementation attempt failed verification. "
                    f"Fix the issues and ensure all tests pass. "
                    f"Review Plan.md for the original requirements. "
                    f"Do not modify .env, CI configs, or deployment configs."
                )

        if not success:
            _update_status(execution_run_id, "failed")
            _log(execution_run_id, "done", f"Retry failed after {max_iterations + 1} attempts", level="error")
            return

        # Commit, push, open PR
        _update_status(execution_run_id, "pushing")
        _log(execution_run_id, "push", "Committing and pushing changes")

        pr_url = await _commit_push_pr(
            sandbox_path, github_url, branch_name, suggestion, plan, execution_run_id
        )

        _update_status(execution_run_id, "done", pr_url=pr_url)
        _log(execution_run_id, "done", f"PR opened: {pr_url}")

        # Clean up sandbox on success
        try:
            shutil.rmtree(sandbox_path, ignore_errors=True)
        except Exception:
            pass

    except Exception as e:
        logger.exception(f"Retry failed for {execution_run_id}: {e}")
        _update_status(execution_run_id, "failed")
        _log(execution_run_id, "error", str(e), level="error")


async def abandon_execution(execution_run_id: str) -> None:
    """Abandon a failed execution and clean up its sandbox."""
    db = get_supabase()
    exec_run = db.table("execution_runs").select("sandbox_path").eq("id", execution_run_id).execute().data[0]
    sandbox_path = exec_run.get("sandbox_path")

    if sandbox_path:
        try:
            shutil.rmtree(sandbox_path, ignore_errors=True)
        except Exception:
            pass

    _update_status(execution_run_id, "failed")
    _log(execution_run_id, "done", "Execution abandoned by user.")
