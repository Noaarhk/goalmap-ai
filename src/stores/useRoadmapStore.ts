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
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { computeTreeLayout } from "../features/visualization/utils/layoutEngine";
import { apiClient } from "../services/apiClient";
import type { RoadmapData } from "../types";

interface StreamingMilestone {
    id: string;
    label: string;
    status: "pending" | "generating" | "done";
}

interface StreamingAction {
    milestoneId: string;
    id: string;
    label: string;
}

interface RoadmapStore {
    roadmap: RoadmapData | null;
    history: RoadmapData[];
    nodes: Node[];
    edges: Edge[];
    selectedNodeId: string | null;

    // Streaming state for TransitionView
    streamingGoal: string | null;
    streamingStatus: string | null;
    streamingStep: number;
    streamingMilestones: StreamingMilestone[];
    streamingActions: StreamingAction[];

    // Actions
    setRoadmap: (data: RoadmapData) => void;
    addToHistory: (data: RoadmapData) => void;
    loadRoadmap: (id: string) => void;
    setNodes: (nodes: Node[]) => void;
    setEdges: (edges: Edge[]) => void;
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    setSelectedNodeId: (id: string | null) => void;
    
    // Streaming Actions
    setStreamingGoal: (goal: string | null) => void;
    setStreamingStatus: (status: string | null) => void;
    setStreamingStep: (step: number) => void;
    setStreamingMilestones: (milestones: StreamingMilestone[]) => void;
    addStreamingActions: (actions: StreamingAction[]) => void;
    resetStreaming: () => void;
    
    // Layout Actions
    recomputeLayout: () => void;

    // API Actions
    setHistory: (history: RoadmapData[]) => void;
    removeFromHistory: (id: string) => void;
    reset: () => void;

    // Node Progress Actions
    updateNodeProgress: (nodeId: string, progressDelta: number) => void;
    refreshNodesFromRoadmap: () => void;

    // Server Sync Actions
    syncFromServer: (roadmapId: string) => Promise<boolean>;
}

export const useRoadmapStore = create<RoadmapStore>()(
    persist(
        (set, get) => ({
            roadmap: null,
            history: [],
            nodes: [],
            edges: [],
            selectedNodeId: null,
            streamingGoal: null,
            streamingStatus: null,
            streamingStep: 0,
            streamingMilestones: [],
            streamingActions: [],

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

            // Streaming actions
            setStreamingGoal: (streamingGoal) => set({ streamingGoal }),
            setStreamingStatus: (streamingStatus) => set({ streamingStatus }),
            setStreamingStep: (streamingStep) => set({ streamingStep }),
            setStreamingMilestones: (streamingMilestones) => set({ streamingMilestones }),
            addStreamingActions: (actions) => set((state) => ({
                streamingActions: [...state.streamingActions, ...actions]
            })),
            resetStreaming: () => set({
                streamingGoal: null,
                streamingStatus: null,
                streamingStep: 0,
                streamingMilestones: [],
                streamingActions: []
            }),

            recomputeLayout: () => {
                const { roadmap } = get();
                if (!roadmap) return;
                const { nodes, edges } = computeTreeLayout(roadmap.nodes, roadmap.edges);
                set({ nodes, edges });
            },

            setHistory: (history) => set({ history }),
            removeFromHistory: (id) => set((state) => ({
                history: state.history.filter((r) => r.id !== id)
            })),
            reset: () => set({ 
                roadmap: null, 
                history: [], 
                nodes: [], 
                edges: [], 
                selectedNodeId: null,
                streamingGoal: null,
                streamingStatus: null,
                streamingMilestones: [],
                streamingActions: []
            }),

            updateNodeProgress: (nodeId, progressDelta) => {
                const { roadmap, nodes } = get();
                if (!roadmap) return;

                // Update roadmap data
                const updatedNodes = roadmap.nodes.map((n) =>
                    n.id === nodeId
                        ? { ...n, progress: Math.min(100, (n.progress || 0) + progressDelta) }
                        : n
                );
                const updatedRoadmap = { ...roadmap, nodes: updatedNodes };

                // Update ReactFlow nodes data
                const updatedFlowNodes = nodes.map((n) =>
                    n.id === nodeId
                        ? { ...n, data: { ...n.data, progress: Math.min(100, (n.data.progress || 0) + progressDelta) } }
                        : n
                );

                set({ roadmap: updatedRoadmap, nodes: updatedFlowNodes });
            },

            refreshNodesFromRoadmap: () => {
                const { roadmap, nodes } = get();
                if (!roadmap) return;

                // Sync ReactFlow nodes with roadmap data
                const updatedFlowNodes = nodes.map((n) => {
                    const roadmapNode = roadmap.nodes.find((rn) => rn.id === n.id);
                    if (roadmapNode) {
                        return { ...n, data: { ...n.data, progress: roadmapNode.progress || 0 } };
                    }
                    return n;
                });

                set({ nodes: updatedFlowNodes });
            },

            syncFromServer: async (roadmapId: string) => {
                try {
                    console.log("[RoadmapStore] Syncing from server:", roadmapId);
                    const serverRoadmap = await apiClient.getRoadmap(roadmapId);
                    
                    // Compute layout for the server data
                    const { nodes, edges } = computeTreeLayout(serverRoadmap.nodes, serverRoadmap.edges);
                    
                    // Update store with server data
                    const { history } = get();
                    const updatedHistory = history.map((r) =>
                        r.id === roadmapId ? serverRoadmap : r
                    );
                    
                    set({
                        roadmap: serverRoadmap,
                        nodes,
                        edges,
                        history: updatedHistory,
                    });
                    
                    console.log("[RoadmapStore] Sync complete, nodes updated:", serverRoadmap.nodes.length);
                    return true;
                } catch (error) {
                    console.error("[RoadmapStore] Sync failed:", error);
                    return false;
                }
            },
        }),
        {
            name: "roadmap-storage",
            version: 1,
            migrate: (persisted: any) => {
                // Migrate old "roadmapNode" type to "roadmapCard"
                if (persisted?.nodes) {
                    persisted.nodes = persisted.nodes.map((n: any) =>
                        n.type === "roadmapNode" ? { ...n, type: "roadmapCard" } : n
                    );
                }
                return persisted;
            },
            partialize: (state) => ({
                roadmap: state.roadmap,
                nodes: state.nodes,
                edges: state.edges,
                history: state.history
            }),
        }
    )
);
