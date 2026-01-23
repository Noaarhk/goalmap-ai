import {
    applyEdgeChanges,
    applyNodeChanges,
    type Edge,
    type EdgeChange,
    type Node,
    type NodeChange,
    type OnEdgesChange,
    type OnNodesChange,
} from "reactflow";
import { create } from "zustand/react";
import type { RoadmapData } from "../types";

interface RoadmapStore {
    roadmap: RoadmapData | null;
    history: RoadmapData[];
    nodes: Node[];
    edges: Edge[];
    selectedNodeId: string | null;

    // Actions
    setRoadmap: (data: RoadmapData) => void;
    addToHistory: (data: RoadmapData) => void;
    loadRoadmap: (id: string) => void;
    setNodes: (nodes: Node[]) => void;
    setEdges: (edges: Edge[]) => void;
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    setSelectedNodeId: (id: string | null) => void;
}

export const useRoadmapStore = create<RoadmapStore>((set, get) => ({
    roadmap: null,
    history: [],
    nodes: [],
    edges: [],
    selectedNodeId: null,

    setRoadmap: (roadmap) => {
        const { history } = get();
        const exists = history.some((r) => r.id === roadmap.id);
        set({
            roadmap,
            history: exists ? history : [roadmap, ...history],
        });
    },

    addToHistory: (roadmap) => {
        const { history } = get();
        if (!history.some((r) => r.id === roadmap.id)) {
            set({ history: [roadmap, ...history] });
        }
    },

    loadRoadmap: (id) => {
        const { history } = get();
        const found = history.find((r) => r.id === id);
        if (found) {
            set({ roadmap: found });
        }
    },
    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),

    onNodesChange: (changes: NodeChange[]) => {
        set({
            nodes: applyNodeChanges(changes, get().nodes),
        });
    },

    onEdgesChange: (changes: EdgeChange[]) => {
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });
    },

    setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
}));
