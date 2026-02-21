"use client";

import { useState } from "react";
import { analyzeRepo } from "@/services/api";
import type { Repo } from "@/types";

interface RepoInputProps {
  onRepoCreated: (repo: Repo) => void;
}

export function RepoInput({ onRepoCreated }: RepoInputProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const repo = await analyzeRepo(url.trim());
      onRepoCreated(repo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze repo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="w-full max-w-lg space-y-8 text-center">
        <div>
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <span className="text-2xl font-bold text-primary">PE</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">
            Analyze a Repository
          </h2>
          <p className="mt-2 text-muted-foreground">
            Paste a GitHub URL to generate a feature topology graph, explore
            expansion suggestions, and auto-build features with Claude Code.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="w-full rounded-lg border border-border bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            required
          />
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Starting Analysis..." : "Analyze Repository"}
          </button>
        </form>

        {error && (
          <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-red-400">
            {error}
          </p>
        )}

        <div className="text-xs text-muted-foreground">
          Supports TypeScript/Node projects up to 100k LOC
        </div>
      </div>
    </div>
  );
}
