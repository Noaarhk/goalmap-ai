import type { BlueprintData, RoadmapData, RoadmapNode, RoadmapEdge } from "../types";
import { supabase } from "./supabase";

// Server response types
interface ServerNodeResponse {
	id: string;
	parent_id: string | null;
	type: "goal" | "milestone" | "task";
	label: string;
	details: string | null;
	order: number;
	is_assumed: boolean;
	status: "pending" | "in_progress" | "completed";
	progress: number;
	completion_criteria: string | null;
	start_date: string | null;
	end_date: string | null;
	duration_days: number | null;
	created_at: string;
	updated_at: string;
}

interface ServerRoadmapResponse {
	id: string;
	title: string;
	goal: string;
	status: string;
	nodes: ServerNodeResponse[];
	created_at: string;
	updated_at: string;
}

// Transform server response to frontend RoadmapData (snake_case → camelCase)
function transformServerRoadmap(server: ServerRoadmapResponse): RoadmapData {
	const nodes: RoadmapNode[] = server.nodes.map((n) => ({
		id: n.id,
		label: n.label,
		details: n.details,
		isAssumed: n.is_assumed,
		type: n.type,
		status: n.status,
		order: n.order,
		progress: n.progress,
		startDate: n.start_date || undefined,
		endDate: n.end_date || undefined,
		completionCriteria: n.completion_criteria || undefined,
		parentId: n.parent_id || undefined,
	}));

	// Generate edges from parent_id relationships
	const edges: RoadmapEdge[] = server.nodes
		.filter((n) => n.parent_id)
		.map((n) => ({
			id: `e-${n.parent_id}-${n.id}`,
			source: n.parent_id!,
			target: n.id,
		}));

	return {
		id: server.id,
		title: server.title,
		createdAt: new Date(server.created_at).getTime(),
		score: 0, // Server doesn't have this, default to 0
		summary: server.goal,
		nodes,
		edges,
	};
}

export interface ChatResponseEvent {
	type: "token" | "status" | "blueprint_update" | "error";
	data: any;
}

export interface RoadmapResponseEvent {
	type: "roadmap_skeleton" | "roadmap_actions" | "roadmap_complete" | "error";
	data: any;
}

export interface SkeletonResponseEvent {
	type: "roadmap_skeleton" | "error";
	data: {
		goal?: any;
		thread_id?: string;
		code?: string;
		message?: string;
	};
}

export interface ActionsResponseEvent {
	type: "roadmap_actions" | "roadmap_complete" | "error";
	data: any;
}

export interface NodeUpdate {
	node_id: string;
	progress_delta: number;
	log_entry: string;
}

export interface CheckInAnalyzeResponse {
	checkin_id: string;
	proposed_updates: NodeUpdate[];
}

export interface CheckInConfirmResponse {
	success: boolean;
	updated_nodes: string[];
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

type EventHandler<T> = (event: T) => void;

async function getAuthHeaders(): Promise<Record<string, string>> {
	const {
		data: { session },
	} = await supabase.auth.getSession();
	console.log("[Auth] Session:", session ? `Token exists (expires: ${new Date(session.expires_at! * 1000).toISOString()})` : "No session");
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
	};
	if (session?.access_token) {
		headers.Authorization = `Bearer ${session.access_token}`;
	}
	return headers;
}

async function fetchJSON<T>(url: string, options: RequestInit = {}): Promise<T> {
	console.log(`[API Request] ${options.method || "GET"} ${url}`, options.body ? JSON.parse(options.body as string) : "");
	const headers = await getAuthHeaders();
	const response = await fetch(url, {
		...options,
		headers: {
			...headers,
			...options.headers,
		},
	});

	if (!response.ok) {
        console.error(`[API Error] ${response.status} ${response.statusText} for ${url}`);
		throw new Error(`HTTP error! status: ${response.status}`);
	}
    
    // Handle 204 No Content
    if (response.status === 204) {
        return null as T;
    }

	return response.json();
}

async function streamRequest<T>(
	url: string,
	body: any,
	onEvent: EventHandler<T>,
) {
	try {
        console.log(`[API Stream Request] POST ${url}`, body);
		const headers = await getAuthHeaders();
		const response = await fetch(url, {
			method: "POST",
			headers,
			body: JSON.stringify(body),
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		if (!response.body) {
			throw new Error("Response body is empty");
		}

		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split("\n\n");
			buffer = lines.pop() || ""; // Keep the last incomplete chunk

			for (const line of lines) {
				if (line.startsWith("event: ")) {
					const typeLine = line.split("\n")[0];
					const dataLine = line.split("\n")[1];

					if (typeLine && dataLine) {
						const eventType = typeLine.replace("event: ", "").trim();
						const eventDataStr = dataLine.replace("data: ", "").trim();

						try {
							const eventData = JSON.parse(eventDataStr);
							onEvent({ type: eventType, data: eventData } as unknown as T);
						} catch (e) {
							console.error("Failed to parse SSE data", e);
						}
					}
				}
			}
		}
	} catch (error) {
		console.error("Stream request failed", error);
		throw error;
	}
}

export const apiClient = {
	// Stream chat with response-first architecture
	streamChat: async (
		message: string,
		history: { role: string; content: string }[],
		currentBlueprint: Partial<BlueprintData>,
		chatId: string,
		onEvent: EventHandler<ChatResponseEvent>,
	) => {
		await streamRequest(
			`${API_BASE}/v1/chat/stream`,
			{
				message,
				history,
				current_blueprint: currentBlueprint,
				chat_id: chatId,
			},
			onEvent,
		);
	},

	streamRoadmap: async (
		blueprint: BlueprintData,
		chatId: string,
		onEvent: EventHandler<RoadmapResponseEvent>,
	) => {
		await streamRequest(
			`${API_BASE}/v1/roadmaps/stream`,
			{
				goal: blueprint.goal,
				why: blueprint.why,
				timeline: blueprint.timeline,
				obstacles: blueprint.obstacles,
				resources: blueprint.resources,
				conversation_id: chatId,
			},
			onEvent,
		);
	},

	// HIL Step 1: Generate skeleton (milestones only)
	streamSkeleton: async (
		blueprint: BlueprintData,
		chatId: string,
		onEvent: EventHandler<SkeletonResponseEvent>,
	) => {
		await streamRequest(
			`${API_BASE}/v1/roadmaps/stream/skeleton`,
			{
				goal: blueprint.goal,
				why: blueprint.why,
				timeline: blueprint.timeline,
				obstacles: blueprint.obstacles,
				resources: blueprint.resources,
				conversation_id: chatId,
			},
			onEvent,
		);
	},

	// HIL Step 2: Resume and generate actions
	streamActions: async (
		threadId: string,
		blueprint: BlueprintData,
		chatId: string,
		onEvent: EventHandler<ActionsResponseEvent>,
		modifiedMilestones?: { id: string; label: string; is_new?: boolean }[],
	) => {
		await streamRequest(
			`${API_BASE}/v1/roadmaps/stream/actions`,
			{
				thread_id: threadId,
				goal: blueprint.goal,
				why: blueprint.why,
				timeline: blueprint.timeline,
				obstacles: blueprint.obstacles,
				resources: blueprint.resources,
				conversation_id: chatId,
				modified_milestones: modifiedMilestones || null,
			},
			onEvent,
		);
	},
    
    // --- REST API Methods ---

    // Conversations
    getConversations: async () => {
        return fetchJSON<any[]>(`${API_BASE}/v1/conversations/`);
    },

    createConversation: async (title?: string) => {
        return fetchJSON<any>(`${API_BASE}/v1/conversations/`, {
            method: "POST",
            body: JSON.stringify({ title }),
        });
    },

    getConversation: async (id: string) => {
        return fetchJSON<any>(`${API_BASE}/v1/conversations/${id}/`);
    },
    
    deleteConversation: async (id: string) => {
        return fetchJSON<void>(`${API_BASE}/v1/conversations/${id}/`, {
            method: "DELETE",
        });
    },

    updateConversation: async (id: string, updates: { title?: string }) => {
        return fetchJSON<any>(`${API_BASE}/v1/conversations/${id}/`, {
            method: "PUT",
            body: JSON.stringify(updates),
        });
    },

    // Roadmaps
    getRoadmaps: async () => {
        return fetchJSON<any[]>(`${API_BASE}/v1/roadmaps/`);
    },

    getRoadmap: async (id: string): Promise<RoadmapData> => {
        const serverResponse = await fetchJSON<ServerRoadmapResponse>(`${API_BASE}/v1/roadmaps/${id}`);
        return transformServerRoadmap(serverResponse);
    },

    deleteRoadmap: async (id: string) => {
        return fetchJSON<void>(`${API_BASE}/v1/roadmaps/${id}/`, {
            method: "DELETE",
        });
    },

    // Consult
    consultNode: async (nodeContext: {
        id: string;
        label: string;
        type: string;
        details?: string | null;
    }, question: string): Promise<string> => {
        const response = await fetchJSON<{ advice: string }>(`${API_BASE}/v1/consult`, {
            method: "POST",
            body: JSON.stringify({
                node_id: nodeContext.id,
                node_label: nodeContext.label,
                node_type: nodeContext.type,
                node_details: nodeContext.details ? [nodeContext.details] : [],
                question,
            }),
        });
        return response.advice;
    },

    // Check-ins
    analyzeCheckIn: async (roadmapId: string, userInput: string): Promise<CheckInAnalyzeResponse> => {
        return fetchJSON<CheckInAnalyzeResponse>(`${API_BASE}/v1/checkins/analyze`, {
            method: "POST",
            body: JSON.stringify({
                roadmap_id: roadmapId,
                user_input: userInput,
            }),
        });
    },

    confirmCheckIn: async (
        checkinId: string,
        updates?: NodeUpdate[]
    ): Promise<CheckInConfirmResponse> => {
        return fetchJSON<CheckInConfirmResponse>(`${API_BASE}/v1/checkins/confirm`, {
            method: "POST",
            body: JSON.stringify({
                checkin_id: checkinId,
                updates: updates || null,
            }),
        });
    },

    rejectCheckIn: async (checkinId: string): Promise<{ success: boolean }> => {
        return fetchJSON<{ success: boolean }>(`${API_BASE}/v1/checkins/${checkinId}/reject`, {
            method: "POST",
        });
    },
};
