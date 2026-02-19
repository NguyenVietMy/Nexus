"use client";

import { useState, useRef, useEffect } from "react";
import type { FeatureGraph } from "@/types";

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
}

interface GraphFixPanelProps {
  repoId: string;
  onFixed: (graph: FeatureGraph) => void;
  onClose: () => void;
  onGraphFix: (repoId: string, message: string) => Promise<{ explanation: string; nodes: FeatureGraph["nodes"]; edges: FeatureGraph["edges"] }>;
}

export function GraphFixPanel({ repoId, onFixed, onClose, onGraphFix }: GraphFixPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const msg = input.trim();
    if (!msg || sending) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setSending(true);

    try {
      const result = await onGraphFix(repoId, msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.explanation },
      ]);
      onFixed({ nodes: result.nodes, edges: result.edges });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fix graph";
      setMessages((prev) => [...prev, { role: "error", content: message }]);
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="absolute right-4 top-4 bottom-20 w-80 flex flex-col rounded-xl border border-border bg-card/95 backdrop-blur-sm shadow-xl z-10">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
        <div>
          <h3 className="text-sm font-semibold">Fix Graph</h3>
          <p className="text-[11px] text-muted-foreground">
            Describe structural changes in plain language
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground text-lg leading-none"
        >
          &times;
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-6 space-y-2">
            <p className="text-xs text-muted-foreground">
              Examples:
            </p>
            {[
              "Merge Auth and Login nodes",
              "Make Rate Limiting a child of API Gateway",
              "Add a Notifications node under User Management",
              "Remove the Legacy Import node",
            ].map((ex) => (
              <button
                key={ex}
                onClick={() => setInput(ex)}
                className="block w-full text-left rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-xs leading-relaxed ${
              m.role === "user"
                ? "bg-primary/10 text-foreground ml-4"
                : m.role === "error"
                  ? "bg-red-500/10 text-red-400 border border-red-500/20"
                  : "bg-muted/50 text-muted-foreground mr-4"
            }`}
          >
            {m.role === "assistant" && (
              <span className="block text-[10px] font-medium text-primary mb-1">
                Applied ✓
              </span>
            )}
            {m.content}
          </div>
        ))}

        {sending && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
            <div className="h-3 w-3 animate-spin rounded-full border border-primary border-t-transparent" />
            Thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-3 shrink-0">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the change… (Enter to send)"
          rows={2}
          disabled={sending}
          className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="mt-2 w-full rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50 transition-colors hover:bg-primary/90"
        >
          {sending ? "Applying…" : "Apply change"}
        </button>
      </div>
    </div>
  );
}
