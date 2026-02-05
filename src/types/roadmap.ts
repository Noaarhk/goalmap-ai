export interface RoadmapNode {
    id: string;
    label: string;
    details: string | null;
    isAssumed: boolean;
    type: "goal" | "milestone" | "task";
    status?: "pending" | "in_progress" | "completed";
    order?: number;
    position?: { x: number; y: number };
    progress?: number;
    startDate?: string;
    endDate?: string;
    completionCriteria?: string;
    parentId?: string;
}

export interface RoadmapEdge {
    id: string;
    source: string;
    target: string;
}

export interface RoadmapData {
    id: string;  // Server UUID (set on roadmap_complete, temporary "rm-xxx" before that)
    createdAt: number;
    title: string;
    score: number;
    summary: string;
    nodes: RoadmapNode[];
    edges: RoadmapEdge[];
}

// Streaming state for TransitionView
export interface StreamingMilestone {
    id: string;
    label: string;
    status: "pending" | "generating" | "done";
}

export interface StreamingAction {
    milestoneId: string;
    id: string;
    label: string;
}
