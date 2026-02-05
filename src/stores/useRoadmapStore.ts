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
    
    // API Actions
    setHistory: (history: RoadmapData[]) => void;
    removeFromHistory: (id: string) => void;
    reset: () => void;
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
        }),
        {
            name: "roadmap-storage",
            partialize: (state) => ({ 
                roadmap: state.roadmap,
                nodes: state.nodes, 
                edges: state.edges,
                history: state.history
            }), // Persist roadmap data and history
        }
    )
);
