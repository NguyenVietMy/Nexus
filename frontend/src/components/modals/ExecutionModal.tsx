"use client";

import { useEffect, useState } from "react";
import { getExecutionStatus, getExecutionLogs } from "@/services/api";
import type { ExecutionRun, ExecutionLog } from "@/types";

interface ExecutionModalProps {
  runId: string;
  onClose: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  cloning: "Cloning repository...",
  planning: "Generating plan...",
  testing: "Writing tests...",
  building: "Claude Code building...",
  verifying: "Running verification...",
  pushing: "Pushing & opening PR...",
  done: "Complete!",
  failed: "Failed",
};

export function ExecutionModal({ runId, onClose }: ExecutionModalProps) {
  const [run, setRun] = useState<ExecutionRun | null>(null);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      while (active) {
        try {
          const [status, newLogs] = await Promise.all([
            getExecutionStatus(runId),
            getExecutionLogs(runId),
          ]);
          if (!active) break;
          setRun(status);
          setLogs(newLogs);
          if (status.status === "done" || status.status === "failed") break;
        } catch {
          // retry
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
    };
    poll();
    return () => {
      active = false;
    };
  }, [runId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="text-base font-semibold">Execution Status</h2>
            {run && (
              <p className="text-sm text-muted-foreground">
                {STATUS_LABELS[run.status] ?? run.status}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            &times;
          </button>
        </div>

        {/* Progress */}
        {run && (
          <div className="px-6 py-3 border-b border-border">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span>Iteration: {run.iteration_count}</span>
              {run.pr_url && (
                <a
                  href={run.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  View PR
                </a>
              )}
            </div>
          </div>
        )}

        {/* Log stream */}
        <div className="max-h-80 overflow-y-auto p-4 font-mono text-xs">
          {logs.length === 0 ? (
            <p className="text-muted-foreground">Waiting for logs...</p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className={`py-0.5 ${
                  log.log_level === "error"
                    ? "text-red-400"
                    : log.log_level === "warn"
                      ? "text-amber-400"
                      : "text-muted-foreground"
                }`}
              >
                <span className="text-zinc-600">
                  [{log.step}]
                </span>{" "}
                {log.message}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-border px-6 py-3">
          <button
            onClick={onClose}
            className="rounded-md bg-muted px-4 py-2 text-xs font-medium hover:bg-muted/80"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
