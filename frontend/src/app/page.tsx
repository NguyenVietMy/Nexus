"use client";

import { useState, useEffect } from "react";
import { RepoInput } from "@/components/modals/RepoInput";
import { FeatureGraphView } from "@/components/graph/FeatureGraphView";
import { SuggestionPanel } from "@/components/panels/SuggestionPanel";
import { BranchPanel } from "@/components/panels/BranchPanel";
import { getRepo } from "@/services/api";
import type { Repo, FeatureSuggestion, StrategicBranch } from "@/types";

export default function Home() {
  const [repo, setRepo] = useState<Repo | null>(null);

  // Poll repo status while analysis is in progress
  useEffect(() => {
    if (!repo || (repo.status !== "pending" && repo.status !== "analyzing")) {
      return;
    }
    const interval = setInterval(async () => {
      try {
        const updated = await getRepo(repo.id);
        setRepo(updated);
        if (updated.status === "ready" || updated.status === "error") {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [repo?.id, repo?.status]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<FeatureSuggestion[]>([]);
  const [branches, setBranches] = useState<StrategicBranch[]>([]);
  const [simulateError, setSimulateError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<
    "suggestions" | "branches" | null
  >(null);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-primary-foreground">
              PE
            </span>
          </div>
          <h1 className="text-lg font-semibold tracking-tight">
            Product Evolution Engine
          </h1>
        </div>
        {repo && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {repo.name}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                repo.status === "ready"
                  ? "bg-emerald-500/10 text-emerald-400"
                  : repo.status === "analyzing"
                    ? "bg-amber-500/10 text-amber-400"
                    : repo.status === "error"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-zinc-500/10 text-zinc-400"
              }`}
            >
              {repo.status}
            </span>
          </div>
        )}
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Graph area */}
        <main className="flex-1 relative">
          {!repo ? (
            <RepoInput onRepoCreated={setRepo} />
          ) : repo.status !== "ready" ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <p className="text-muted-foreground">
                  Analyzing repository...
                </p>
              </div>
            </div>
          ) : (
            <FeatureGraphView
              repoId={repo.id}
              onNodeSelect={(nodeId) => {
                setSelectedNodeId(nodeId);
                setActivePanel("suggestions");
              }}
              onSimulate={() => {
                setActivePanel("branches");
                setSimulateError(null);
              }}
              setSuggestions={setSuggestions}
              setBranches={setBranches}
              setSimulateError={setSimulateError}
            />
          )}
        </main>

        {/* Side panel */}
        {activePanel && (
          <aside className="w-96 border-l border-border overflow-y-auto">
            {activePanel === "suggestions" && selectedNodeId && (
              <SuggestionPanel
                nodeId={selectedNodeId}
                suggestions={suggestions}
                onClose={() => setActivePanel(null)}
              />
            )}
            {activePanel === "branches" && repo && (
              <BranchPanel
                repoId={repo.id}
                branches={branches}
                simulateError={simulateError}
                onClose={() => setActivePanel(null)}
              />
            )}
          </aside>
        )}
      </div>
    </div>
  );
}
