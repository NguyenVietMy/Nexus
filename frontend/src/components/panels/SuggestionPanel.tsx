"use client";

import { useState } from "react";
import { buildFeature } from "@/services/api";
import type { FeatureSuggestion } from "@/types";
import { ExecutionModal } from "@/components/modals/ExecutionModal";

interface SuggestionPanelProps {
  nodeId: string;
  suggestions: FeatureSuggestion[];
  onClose: () => void;
}

export function SuggestionPanel({
  nodeId,
  suggestions,
  onClose,
}: SuggestionPanelProps) {
  const [executionRunId, setExecutionRunId] = useState<string | null>(null);
  const [building, setBuilding] = useState<string | null>(null);

  const handleBuild = async (suggestion: FeatureSuggestion) => {
    setBuilding(suggestion.id);
    try {
      const run = await buildFeature(nodeId, suggestion.id);
      setExecutionRunId(run.id);
    } catch {
      // error handling
    } finally {
      setBuilding(null);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Feature Suggestions</h2>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          &times;
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {suggestions.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No suggestions available. Click a feature node to generate them.
          </p>
        ) : (
          suggestions.map((s) => (
            <div
              key={s.id}
              className="rounded-lg border border-border bg-card p-4 space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-medium">{s.name}</h3>
                <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                  {s.complexity}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{s.rationale}</p>

              {s.impacted_files.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {s.impacted_files.map((f) => (
                    <span
                      key={f}
                      className="inline-flex rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              )}

              {s.test_cases.length > 0 && (
                <details className="text-xs text-muted-foreground">
                  <summary className="cursor-pointer hover:text-foreground">
                    Test cases ({s.test_cases.length})
                  </summary>
                  <ul className="mt-1 ml-4 list-disc space-y-0.5">
                    {s.test_cases.map((tc, i) => (
                      <li key={i}>{tc}</li>
                    ))}
                  </ul>
                </details>
              )}

              <button
                onClick={() => handleBuild(s)}
                disabled={building === s.id}
                className="mt-2 w-full rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                {building === s.id ? "Starting..." : "Auto Build"}
              </button>
            </div>
          ))
        )}
      </div>

      {/* Execution modal */}
      {executionRunId && (
        <ExecutionModal
          runId={executionRunId}
          onClose={() => setExecutionRunId(null)}
        />
      )}
    </div>
  );
}
