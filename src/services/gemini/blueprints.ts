import { Type } from "@google/genai";
import type { BlueprintData } from "../../types";
import { generateContentWithTimeout } from "./client";

const SYSTEM_INSTRUCTION = `You are a world-class Goal Architect. Your mission is to help users turn abstract goals into concrete roadmaps.
Analyze user messages to extract: Goal, Why, Timeline, Obstacles, and Resources.
When chatting, be encouraging and professional. Ask one specific follow-up question at a time to fill missing details.
Always keep track of the goal state.`;

const CLIP_HISTORY = (messages: { role: string; content: string }[]) => 
	messages.slice(-10);

export const extractBlueprintIdentity = async (
	messages: { role: string; content: string }[],
): Promise<Partial<BlueprintData>> => {
  const prompt = `Based on the conversation history, extract the core identity in JSON:
  - goal: The main objective.
  - why: The deep motivation or purpose. (Do not include tools/resources).
  - fieldScores: { goal: 0-100, why: 0-100 }

  History: ${CLIP_HISTORY(messages).map(m => `${m.role}: ${m.content}`).join("\n")}`;

	const response = await generateContentWithTimeout({
		model: "gemini-3-flash-preview",
		contents: prompt,
		config: {
			systemInstruction: "Extract JSON only with 'goal', 'why', and their scores.",
			responseMimeType: "application/json",
			responseSchema: {
				type: Type.OBJECT,
				properties: {
					goal: { type: Type.STRING },
					why: { type: Type.STRING },
					fieldScores: {
						type: Type.OBJECT,
						properties: {
							goal: { type: Type.NUMBER },
							why: { type: Type.NUMBER },
						},
						required: ["goal", "why"],
					},
				},
				required: ["goal", "why", "fieldScores"],
			},
		},
	});

	try {
		let text = response.text as string;
		if (text.startsWith("```")) {
			text = text.replace(/^```json\n?/, "").replace(/\n?```$/, "");
		}
		return JSON.parse(text);
	} catch (e) {
		console.error("Failed to parse Identity JSON:", response.text);
		throw e;
	}
};

export const extractBlueprintTactics = async (
	messages: { role: string; content: string }[],
): Promise<Partial<BlueprintData>> => {
  const prompt = `Based on the conversation history, extract tactical details in JSON:
  - timeline: When to achieve it.
  - obstacles: Potential problems or fears.
  - resources: Physical tools, money, or skills.
  - fieldScores: { timeline: 0-100, obstacles: 0-100, resources: 0-100 }

  History: ${CLIP_HISTORY(messages).map(m => `${m.role}: ${m.content}`).join("\n")}`;

	const response = await generateContentWithTimeout({
		model: "gemini-3-flash-preview",
		contents: prompt,
		config: {
			systemInstruction: "Extract JSON only with 'timeline', 'obstacles', 'resources', and their scores.",
			responseMimeType: "application/json",
			responseSchema: {
				type: Type.OBJECT,
				properties: {
					timeline: { type: Type.STRING },
					obstacles: { type: Type.STRING },
					resources: { type: Type.STRING },
					fieldScores: {
						type: Type.OBJECT,
						properties: {
							timeline: { type: Type.NUMBER },
							obstacles: { type: Type.NUMBER },
							resources: { type: Type.NUMBER },
						},
						required: ["timeline", "obstacles", "resources"],
					},
				},
				required: ["timeline", "obstacles", "resources", "fieldScores"],
			},
		},
	});

	try {
		let text = response.text as string;
		if (text.startsWith("```")) {
			text = text.replace(/^```json\n?/, "").replace(/\n?```$/, "");
		}
		return JSON.parse(text);
	} catch (e) {
		console.error("Failed to parse Tactics JSON:", response.text);
		throw e;
	}
};


export const generateBlueprintTips = async (
	blueprint: BlueprintData,
	messages: { role: string; content: string }[],
): Promise<Partial<BlueprintData>> => {
	const prompt = `Based on the current blueprint and history, provide two types of strategic tips in Korean:
  1. "readinessTips": 2-3 specific points on what info is missing or needs more detail to reach 100% readiness.
  2. "successTips": 2-3 pieces of strategic advice or encouragement.
  
  Current Blueprint: ${JSON.stringify(blueprint)}
  History: ${messages.map((m) => `${m.role}: ${m.content}`).join("\n")}`;

	const response = await generateContentWithTimeout({
		model: "gemini-3-flash-preview",
		contents: prompt,
		config: {
			systemInstruction: "Extract JSON only with two types of tips in Korean.",
			responseMimeType: "application/json",
			responseSchema: {
				type: Type.OBJECT,
				properties: {
					readinessTips: {
						type: Type.ARRAY,
						items: { type: Type.STRING },
					},
					successTips: {
						type: Type.ARRAY,
						items: { type: Type.STRING },
					},
				},
				required: ["readinessTips", "successTips"],
			},
		},
	});

	try {
		let text = response.text as string;
		if (text.startsWith("```")) {
			text = text.replace(/^```json\n?/, "").replace(/\n?```$/, "");
		}
		return JSON.parse(text);
	} catch (_e) {
		console.error("Failed to parse tips JSON:", response.text);
		return {};
	}
};



export const getAssistantResponse = async (
	messages: { role: string; content: string }[],
): Promise<{ message: string; statusSummary: Partial<BlueprintData> }> => {
	const prompt = `Assistant Response & Goal Update:
	1. "message": Your encouraging response as The Oracle. Ask for missing details one at a time.
	2. "statusSummary": Update the "goal", "why", and their scores (0-100) based ONLY on new information or refinements in the latest chat. 
	
	Rules:
	- "message" is REQUIRED.
	- "statusSummary" fields are OPTIONAL. If nothing new for a field, use null or omit it.
	- Keep "why" focused on purpose, avoid listing long concept words.
	
	History: ${CLIP_HISTORY(messages).map(m => `${m.role}: ${m.content}`).join("\n")}`;


	const response = await generateContentWithTimeout({
		model: "gemini-3-flash-preview",
		contents: prompt,
		config: {
			systemInstruction: `${SYSTEM_INSTRUCTION} Reply in JSON format.`,
			responseMimeType: "application/json",
			responseSchema: {
				type: Type.OBJECT,
				properties: {
					message: { type: Type.STRING },
					statusSummary: {
						type: Type.OBJECT,
						properties: {
							goal: { type: Type.STRING },
							why: { type: Type.STRING },
							fieldScores: {
								type: Type.OBJECT,
								properties: {
									goal: { type: Type.NUMBER },
									why: { type: Type.NUMBER },
								},
								required: ["goal", "why"],
							},
						},
						required: ["fieldScores"],
					},
				},
				required: ["message", "statusSummary"],
			},
		},
	});

	try {
		let text = response.text as string;
		if (text.startsWith("```")) {
			text = text.replace(/^```json\n?/, "").replace(/\n?```$/, "");
		}
		return JSON.parse(text);
	} catch (_e) {
		console.error("Failed to parse Oracle Response:", response.text);
		return {
			message: "The Oracle is having trouble focusing. Could you rephrase your last point?",
			statusSummary: {},
		};
	}
};

