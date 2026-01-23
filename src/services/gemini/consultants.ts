import { generateContentWithTimeout } from "./client";

export const consultNode = async (
  nodeContext: any,
  question: string,
): Promise<string> => {
  const prompt =
    `You are an expert advisor strictly focused on this specific roadmap step.
  
  Context (Current Step):
  Label: ${nodeContext.label}
  Type: ${nodeContext.type}
  Details: ${JSON.stringify(nodeContext.details || [])}
  
  User Question: ${question}
  
  Provide specific, actionable advice relative to THIS step only. Keep it concise.`;

  const response = await generateContentWithTimeout({
    model: "gemini-3-flash-preview",
    contents: [{ role: "user", parts: [{ text: prompt }] }],
    config: {
      systemInstruction: "You are a tactical advisor. Be brief and practical.",
    },
  });

  return response.text || "I am meditating on this step...";
};
