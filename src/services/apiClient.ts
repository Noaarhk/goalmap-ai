import type { BlueprintData } from "../types";
import { supabase } from "./supabase";

export interface ChatResponseEvent {
	type: "token" | "status" | "blueprint_update" | "error";
	data: any;
}

export interface RoadmapResponseEvent {
	type: "roadmap_skeleton" | "roadmap_actions" | "roadmap_direct_actions" | "error";
	data: any;
}

const API_BASE = "http://localhost:8000/api";

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
        details?: string[];
    }, question: string): Promise<string> => {
        const response = await fetchJSON<{ advice: string }>(`${API_BASE}/v1/consult`, {
            method: "POST",
            body: JSON.stringify({
                node_id: nodeContext.id,
                node_label: nodeContext.label,
                node_type: nodeContext.type,
                node_details: nodeContext.details || [],
                question,
            }),
        });
        return response.advice;
    },
};
