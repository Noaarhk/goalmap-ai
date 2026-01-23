import { Type } from "@google/genai";
import type { BlueprintData, RoadmapData } from "../../types";
import { generateContentWithTimeout } from "./client";

export const generateRoadmap = async (
	blueprint: BlueprintData,
	history: string,
): Promise<RoadmapData> => {
	const prompt = `Convert this goal data into a comprehensive roadmap.
  Title: ${blueprint.goal}
  Why: ${blueprint.why}
  Timeline: ${blueprint.timeline}
  Obstacles: ${blueprint.obstacles}
  Resources: ${blueprint.resources}
  
  Context: ${history}
  
  Generate a list of milestones. 
  For each milestone, define:
  - id (string)
  - label (short name)
  - is_assumed (boolean)
  - type (milestone)
  - steps (array of objects)
  
  For each step, define:
  - id (string)
  - label (short name)
  - type (step)
  - tasks (array of strings, specific action items)
  
  Your output must be a flattened list of nodes (Milestones, Steps, Tasks) and edges.
  - Create nodes for Milestones.
  - Create nodes for Steps.
  - Create nodes for Tasks (from the tasks array).
  - Create edges: Milestone -> Step, Step -> Task.
  
  Also provide a summary of the strategy.
  The total score (0-100) should represent how complete the user's initial information was.`;

	const response = await generateContentWithTimeout({
		model: "gemini-3-pro-preview",
		contents: prompt,
		timeout: 360000,
		config: {
			systemInstruction: "Generate a structured roadmap JSON.",
			responseMimeType: "application/json",
			responseSchema: {
				type: Type.OBJECT,
				properties: {
					title: { type: Type.STRING },
					summary: { type: Type.STRING },
					score: { type: Type.NUMBER },
					nodes: {
						type: Type.ARRAY,
						items: {
							type: Type.OBJECT,
							properties: {
								id: { type: Type.STRING },
								label: { type: Type.STRING },
								details: { type: Type.ARRAY, items: { type: Type.STRING } },
								is_assumed: { type: Type.BOOLEAN },
								type: { type: Type.STRING },
							},
						},
					},
					edges: {
						type: Type.ARRAY,
						items: {
							type: Type.OBJECT,
							properties: {
								id: { type: Type.STRING },
								source: { type: Type.STRING },
								target: { type: Type.STRING },
							},
						},
					},
				},
			},
		},
	});

	const data = JSON.parse(response.text as string);
	return {
		...data,
		id: crypto.randomUUID(),
		createdAt: Date.now(),
	};
};
