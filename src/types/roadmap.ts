export interface RoadmapNode {
    id: string;
    label: string;
    details: string[];
    is_assumed: boolean;
    type: "goal" | "milestone" | "action";
    status?: "pending" | "in_progress" | "completed";
    order?: number;
    position?: { x: number; y: number };
    // Enhanced fields
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
    id: string;
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
