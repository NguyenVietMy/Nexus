"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import { getFeatureGraph, getSuggestions, simulateFutures } from "@/services/api";
import { FeatureGraphNode } from "./FeatureGraphNode";
import type { FeatureNode, FeatureEdge, FeatureSuggestion, StrategicBranch } from "@/types";

const nodeTypes = { feature: FeatureGraphNode };

interface FeatureGraphViewProps {
  repoId: string;
  onNodeSelect: (nodeId: string) => void;
  onSimulate: () => void;
  setSuggestions: (s: FeatureSuggestion[]) => void;
  setBranches: (b: StrategicBranch[]) => void;
}

function toFlowNodes(features: FeatureNode[]): Node[] {
  const rootNodes = features.filter((f) => !f.parent_feature_id);
  const childMap = new Map<string, FeatureNode[]>();

  for (const f of features) {
    if (f.parent_feature_id) {
      const siblings = childMap.get(f.parent_feature_id) ?? [];
      siblings.push(f);
      childMap.set(f.parent_feature_id, siblings);
    }
  }

  const nodes: Node[] = [];
  let y = 0;

  function layout(feature: FeatureNode, x: number, depth: number) {
    nodes.push({
      id: feature.id,
      type: "feature",
      position: { x: depth * 320, y },
      data: {
        label: feature.name,
        description: feature.description,
        riskScore: feature.risk_score,
        anchorFiles: feature.anchor_files,
      },
    });
    y += 100;

    const children = childMap.get(feature.id) ?? [];
    for (const child of children) {
      layout(child, x, depth + 1);
    }
  }

  for (const root of rootNodes) {
    layout(root, 0, 0);
  }

  return nodes;
}

function toFlowEdges(edges: FeatureEdge[]): Edge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source_node_id,
    target: e.target_node_id,
    type: e.edge_type === "related" ? "default" : "smoothstep",
    animated: e.edge_type === "related",
    style: {
      stroke: e.edge_type === "related" ? "#6d28d9" : "#3f3f46",
    },
  }));
}

export function FeatureGraphView({
  repoId,
  onNodeSelect,
  onSimulate,
  setSuggestions,
  setBranches,
}: FeatureGraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const graph = await getFeatureGraph(repoId);
        setNodes(toFlowNodes(graph.nodes));
        setEdges(toFlowEdges(graph.edges));
      } catch {
        // Will show empty graph
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [repoId, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    async (_: React.MouseEvent, node: Node) => {
      onNodeSelect(node.id);
      try {
        const suggestions = await getSuggestions(node.id);
        setSuggestions(suggestions);
      } catch {
        setSuggestions([]);
      }
    },
    [onNodeSelect, setSuggestions]
  );

  const handleSimulate = useCallback(async () => {
    onSimulate();
    try {
      const branches = await simulateFutures(repoId);
      setBranches(branches);
    } catch {
      setBranches([]);
    }
  }, [repoId, onSimulate, setBranches]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-muted-foreground">Loading feature graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="#27272a" gap={24} />
        <Controls
          className="!bg-card !border-border !rounded-lg"
          showInteractive={false}
        />
        <MiniMap
          nodeColor="#6d28d9"
          maskColor="rgba(0,0,0,0.7)"
          className="!bg-card !border-border !rounded-lg"
        />
      </ReactFlow>

      {/* Simulate Futures button */}
      <button
        onClick={handleSimulate}
        className="absolute bottom-6 right-6 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-lg transition-colors hover:bg-primary/90"
      >
        Simulate Futures
      </button>
    </div>
  );
}
