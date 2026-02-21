"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";

interface FeatureNodeData {
  label: string;
  description: string;
  riskScore: number | null;
  anchorFiles: string[];
  [key: string]: unknown;
}

function riskBadge(score: number | null) {
  if (score === null) return null;
  const color =
    score <= 33
      ? "bg-emerald-500/20 text-emerald-400"
      : score <= 66
        ? "bg-amber-500/20 text-amber-400"
        : "bg-red-500/20 text-red-400";
  return (
    <span
      className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ${color}`}
    >
      {score}
    </span>
  );
}

export function FeatureGraphNode({ data }: NodeProps) {
  const nodeData = data as unknown as FeatureNodeData;

  return (
    <div className="min-w-[200px] max-w-[280px] rounded-xl border border-border bg-card p-3 shadow-md transition-shadow hover:shadow-lg hover:shadow-primary/5">
      <Handle type="target" position={Position.Left} className="!bg-primary" />

      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold leading-tight">{nodeData.label}</h3>
        {riskBadge(nodeData.riskScore)}
      </div>

      {nodeData.description && (
        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
          {nodeData.description}
        </p>
      )}

      {nodeData.anchorFiles?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {nodeData.anchorFiles.slice(0, 3).map((f) => (
            <span
              key={f}
              className="inline-flex rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
            >
              {f.split("/").pop()}
            </span>
          ))}
          {nodeData.anchorFiles.length > 3 && (
            <span className="text-[10px] text-muted-foreground">
              +{nodeData.anchorFiles.length - 3} more
            </span>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-primary"
      />
    </div>
  );
}
