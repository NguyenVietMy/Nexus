"use client";

import { useState } from "react";
import type { StrategicBranch } from "@/types";

interface BranchPanelProps {
  repoId: string;
  branches: StrategicBranch[];
  onClose: () => void;
}

type ViewMode = "cards" | "compare";

function InitiativeItem({
  name,
  description,
}: {
  name: string;
  description: string;
}) {
  return (
    <div className="rounded border border-border/60 bg-muted/30 px-2.5 py-1.5">
      <span className="text-xs font-medium text-foreground">{name}</span>
      {description && (
        <p className="mt-0.5 text-[11px] text-muted-foreground leading-snug">
          {description}
        </p>
      )}
    </div>
  );
}

function BranchCard({ branch }: { branch: StrategicBranch }) {
  const initiatives = Array.isArray(branch.initiatives_json)
    ? branch.initiatives_json
    : [];
  const execOrder = branch.execution_order ?? [];

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div>
        <h3 className="text-sm font-semibold">{branch.branch_name}</h3>
        <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
          {branch.theme}
        </span>
      </div>

      {branch.narrative && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          {branch.narrative}
        </p>
      )}

      {initiatives.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs font-medium text-foreground">
            Initiatives ({initiatives.length})
          </span>
          <div className="flex flex-wrap gap-1.5">
            {initiatives.map((init, i) => (
              <InitiativeItem
                key={i}
                name={
                  (init as { name?: string }).name ?? `Initiative ${i + 1}`
                }
                description={
                  (init as { description?: string }).description ?? ""
                }
              />
            ))}
          </div>
        </div>
      )}

      {branch.architecture_impact && (
        <div className="text-xs">
          <span className="font-medium text-foreground">Architecture:</span>{" "}
          <span className="text-muted-foreground">
            {branch.architecture_impact}
          </span>
        </div>
      )}

      {branch.scalability_impact && (
        <div className="text-xs">
          <span className="font-medium text-foreground">Scalability:</span>{" "}
          <span className="text-muted-foreground">
            {branch.scalability_impact}
          </span>
        </div>
      )}

      {branch.risk_impact && (
        <div className="text-xs">
          <span className="font-medium text-foreground">Risk:</span>{" "}
          <span className="text-muted-foreground">{branch.risk_impact}</span>
        </div>
      )}

      {branch.tradeoffs && (
        <div className="text-xs">
          <span className="font-medium text-foreground">Tradeoffs:</span>{" "}
          <span className="text-muted-foreground">{branch.tradeoffs}</span>
        </div>
      )}

      {execOrder.length > 0 && (
        <div className="text-xs">
          <span className="font-medium text-foreground">
            Recommended order:
          </span>
          <ol className="mt-1 ml-4 list-decimal space-y-0.5 text-muted-foreground">
            {execOrder.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function CompareView({ branches }: { branches: StrategicBranch[] }) {
  const [selected, setSelected] = useState<number>(0);
  const b = branches[selected];
  if (!b) return null;

  const initiatives = Array.isArray(b.initiatives_json)
    ? b.initiatives_json
    : [];

  return (
    <div className="space-y-4">
      {/* Branch selector tabs */}
      <div className="flex gap-1 rounded-lg border border-border p-1 bg-muted/30">
        {branches.map((branch, i) => (
          <button
            key={branch.id}
            onClick={() => setSelected(i)}
            className={`flex-1 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              selected === i
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            {branch.branch_name}
          </button>
        ))}
      </div>

      {/* Selected branch detail */}
      <div className="rounded-lg border border-border bg-card p-4 space-y-3">
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

        <div className="grid grid-cols-1 gap-3 text-xs">
          {b.architecture_impact && (
            <div>
              <span className="font-medium text-foreground">Architecture</span>
              <p className="mt-0.5 text-muted-foreground">
                {b.architecture_impact}
              </p>
            </div>
          )}
          {b.scalability_impact && (
            <div>
              <span className="font-medium text-foreground">Scalability</span>
              <p className="mt-0.5 text-muted-foreground">
                {b.scalability_impact}
              </p>
            </div>
          )}
          {b.risk_impact && (
            <div>
              <span className="font-medium text-foreground">Risk</span>
              <p className="mt-0.5 text-muted-foreground">{b.risk_impact}</p>
            </div>
          )}
          {b.tradeoffs && (
            <div>
              <span className="font-medium text-foreground">Tradeoffs</span>
              <p className="mt-0.5 text-muted-foreground">{b.tradeoffs}</p>
            </div>
          )}
        </div>

        {initiatives.length > 0 && (
          <div className="space-y-2">
            <span className="text-xs font-medium text-foreground">
              Initiatives
            </span>
            <div className="space-y-1.5">
              {initiatives.map((init, i) => (
                <InitiativeItem
                  key={i}
                  name={(init as { name?: string }).name ?? `#${i + 1}`}
                  description={(init as { description?: string }).description ?? ""}
                />
              ))}
            </div>
          </div>
        )}

        {(b.execution_order ?? []).length > 0 && (
          <div className="text-xs">
            <span className="font-medium text-foreground">
              Recommended execution order
            </span>
            <ol className="mt-1 ml-4 list-decimal space-y-0.5 text-muted-foreground">
              {(b.execution_order ?? []).map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

export function BranchPanel({ branches, onClose }: BranchPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("cards");

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Strategic Futures</h2>
        <div className="flex items-center gap-2">
          {branches.length > 0 && (
            <div className="flex rounded-md border border-border p-0.5">
              <button
                onClick={() => setViewMode("cards")}
                className={`rounded px-2 py-1 text-[10px] font-medium ${
                  viewMode === "cards"
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Cards
              </button>
              <button
                onClick={() => setViewMode("compare")}
                className={`rounded px-2 py-1 text-[10px] font-medium ${
                  viewMode === "compare"
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Compare
              </button>
            </div>
          )}
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-lg leading-none"
          >
            &times;
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {branches.length === 0 ? (
          <div className="text-center py-8">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">
              Generating strategic branches...
            </p>
          </div>
        ) : viewMode === "compare" ? (
          <CompareView branches={branches} />
        ) : (
          <div className="space-y-4">
            {branches.map((b) => (
              <BranchCard key={b.id} branch={b} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
