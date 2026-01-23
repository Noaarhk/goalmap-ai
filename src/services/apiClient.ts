import type { BlueprintData } from "../types";

export interface ChatResponseEvent {
	type: "token" | "status" | "blueprint_update" | "error";
	data: any;
}

export interface RoadmapResponseEvent {
	type: "roadmap_milestones" | "roadmap_tasks" | "error";
	data: any;
}

const API_BASE = "http://localhost:8000/api";

type EventHandler<T> = (event: T) => void;

async function streamRequest<T>(
	url: string,
	body: any,
	onEvent: EventHandler<T>,
) {
	try {
		const response = await fetch(url, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
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
		onEvent: EventHandler<ChatResponseEvent>,
	) => {
		await streamRequest(
			`${API_BASE}/chat/stream`,
			{ message, history, current_blueprint: currentBlueprint }, // Note: snake_case for backend
			onEvent,
		);
	},

	streamRoadmap: async (
		blueprint: BlueprintData,
		onEvent: EventHandler<RoadmapResponseEvent>,
	) => {
		await streamRequest(
			`${API_BASE}/roadmap/stream`,
			{
				goal: blueprint.goal,
				why: blueprint.why,
				timeline: blueprint.timeline,
				obstacles: blueprint.obstacles,
				resources: blueprint.resources,
			},
			onEvent,
		);
	},
};
