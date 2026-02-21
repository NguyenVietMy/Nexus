"use client";

import type { StrategicBranch } from "@/types";

interface BranchPanelProps {
  repoId: string;
  branches: StrategicBranch[];
  onClose: () => void;
}

export function BranchPanel({ branches, onClose }: BranchPanelProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Strategic Futures</h2>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          &times;
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {branches.length === 0 ? (
          <div className="text-center py-8">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">
              Generating strategic branches...
            </p>
          </div>
        ) : (
          branches.map((b) => (
            <div
              key={b.id}
              className="rounded-lg border border-border bg-card p-4 space-y-3"
            >
              <div>
                <h3 className="text-sm font-semibold">{b.branch_name}</h3>
                <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                  {b.theme}
                </span>
              </div>

              {b.narrative && (
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {b.narrative}
                </p>
              )}

              {b.architecture_impact && (
                <div className="text-xs">
                  <span className="font-medium text-foreground">
                    Architecture:
                  </span>{" "}
                  <span className="text-muted-foreground">
                    {b.architecture_impact}
                  </span>
                </div>
              )}

              {b.tradeoffs && (
                <div className="text-xs">
                  <span className="font-medium text-foreground">
                    Tradeoffs:
                  </span>{" "}
                  <span className="text-muted-foreground">{b.tradeoffs}</span>
                </div>
              )}

              {b.execution_order.length > 0 && (
                <div className="text-xs">
                  <span className="font-medium text-foreground">
                    Execution order:
                  </span>
                  <ol className="mt-1 ml-4 list-decimal space-y-0.5 text-muted-foreground">
                    {b.execution_order.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
