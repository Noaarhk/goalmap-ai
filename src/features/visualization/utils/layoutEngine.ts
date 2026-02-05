import dagre from "dagre";
import type { Edge, Node } from "reactflow";
import type { RoadmapEdge, RoadmapNode } from "../../../types";

interface LayoutOptions {
	rankdir: "TB" | "LR";
	rankSep: number;
	nodeSep: number;
	marginX: number;
	marginY: number;
}

const NODE_DIMENSIONS: Record<string, { width: number; height: number }> = {
	goal: { width: 280, height: 140 },
	milestone: { width: 260, height: 120 },
	task: { width: 240, height: 100 },
};

const DEFAULT_OPTIONS: LayoutOptions = {
	rankdir: "TB",
	rankSep: 100,
	nodeSep: 60,
	marginX: 50,
	marginY: 50,
};

function getEdgeStyle(
	sourceType: string,
	targetType: string,
): Record<string, unknown> {
	if (sourceType === "goal" && targetType === "milestone") {
		return { stroke: "#3d84f5", strokeWidth: 2.5 };
	}
	if (sourceType === "milestone" && targetType === "task") {
		return { stroke: "#10b981", strokeWidth: 2 };
	}
	if (sourceType === "goal" && targetType === "task") {
		return { stroke: "#f59e0b", strokeWidth: 2, strokeDasharray: "6 3" };
	}
	return { stroke: "#475569", strokeWidth: 1.5 };
}

export function computeTreeLayout(
	roadmapNodes: RoadmapNode[],
	roadmapEdges: RoadmapEdge[],
	options?: Partial<LayoutOptions>,
): { nodes: Node[]; edges: Edge[] } {
	const opts = { ...DEFAULT_OPTIONS, ...options };
	const g = new dagre.graphlib.Graph();

	g.setGraph({
		rankdir: opts.rankdir,
		ranksep: opts.rankSep,
		nodesep: opts.nodeSep,
		marginx: opts.marginX,
		marginy: opts.marginY,
	});
	g.setDefaultEdgeLabel(() => ({}));

	for (const node of roadmapNodes) {
		const dims = NODE_DIMENSIONS[node.type] || NODE_DIMENSIONS.task;
		g.setNode(node.id, { width: dims.width, height: dims.height });
	}

	for (const edge of roadmapEdges) {
		g.setEdge(edge.source, edge.target);
	}

	dagre.layout(g);

	const nodeMap = new Map(roadmapNodes.map((n) => [n.id, n]));

	const flowNodes: Node[] = roadmapNodes.map((rn) => {
		const pos = g.node(rn.id);
		const dims = NODE_DIMENSIONS[rn.type] || NODE_DIMENSIONS.task;
		return {
			id: rn.id,
			type: "roadmapCard",
			data: { ...rn },
			position: {
				x: pos.x - dims.width / 2,
				y: pos.y - dims.height / 2,
			},
		};
	});

	const flowEdges: Edge[] = roadmapEdges.map((re) => {
		const sourceNode = nodeMap.get(re.source);
		const targetNode = nodeMap.get(re.target);
		const style = getEdgeStyle(
			sourceNode?.type || "",
			targetNode?.type || "",
		);

		return {
			id: re.id,
			source: re.source,
			target: re.target,
			type: "smoothstep",
			animated: false,
			style,
		};
	});

	return { nodes: flowNodes, edges: flowEdges };
}
