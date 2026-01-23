export interface RoadmapNode {
    id: string;
    label: string;
    details: string[];
    is_assumed: boolean;
    type: "milestone" | "step" | "task";
    position?: { x: number; y: number };
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
