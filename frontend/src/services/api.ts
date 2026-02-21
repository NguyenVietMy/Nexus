import type {
  Repo,
  FeatureGraph,
  FeatureSuggestion,
  StrategicBranch,
  ExecutionRun,
  ExecutionLog,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---- Repos ----

export async function analyzeRepo(githubUrl: string): Promise<Repo> {
  return fetchJSON<Repo>("/api/repos/analyze", {
    method: "POST",
    body: JSON.stringify({ github_url: githubUrl }),
  });
}

export async function getRepo(repoId: string): Promise<Repo> {
  return fetchJSON<Repo>(`/api/repos/${repoId}`);
}

// ---- Features ----

export async function getFeatureGraph(repoId: string): Promise<FeatureGraph> {
  return fetchJSON<FeatureGraph>(`/api/repos/${repoId}/features`);
}

export async function getSuggestions(
  nodeId: string
): Promise<FeatureSuggestion[]> {
  return fetchJSON<FeatureSuggestion[]>(
    `/api/features/${nodeId}/suggestions`
  );
}

// ---- Strategic Branches ----

export async function simulateFutures(
  repoId: string
): Promise<StrategicBranch[]> {
  return fetchJSON<StrategicBranch[]>(`/api/repos/${repoId}/simulate`, {
    method: "POST",
  });
}

export async function getBranches(
  repoId: string
): Promise<StrategicBranch[]> {
  return fetchJSON<StrategicBranch[]>(`/api/repos/${repoId}/branches`);
}

// ---- Execution ----

export async function buildFeature(
  nodeId: string,
  suggestionId: string
): Promise<ExecutionRun> {
  return fetchJSON<ExecutionRun>(`/api/features/${nodeId}/build`, {
    method: "POST",
    body: JSON.stringify({ suggestion_id: suggestionId }),
  });
}

export async function getExecutionStatus(
  runId: string
): Promise<ExecutionRun> {
  return fetchJSON<ExecutionRun>(`/api/execution/${runId}`);
}

export async function getExecutionLogs(
  runId: string
): Promise<ExecutionLog[]> {
  return fetchJSON<ExecutionLog[]>(`/api/execution/${runId}/logs`);
}
