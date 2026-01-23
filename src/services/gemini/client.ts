import { GoogleGenAI } from "@google/genai";

// Always use the API key directly from process.env.API_KEY
export const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const withTimeout = <T>(
  promise: Promise<T>,
  ms: number = 60000,
): Promise<T> => {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms)
    ),
  ]);
};


export const generateContentWithTimeout = async (params: any) => {
  const { timeout, ...genAIParams } = params;
  console.log(`Calling Gemini API (${genAIParams.model})...`);
  try {
    const res = await withTimeout(ai.models.generateContent(genAIParams), timeout);
    return res;
  } catch (e) {
    console.error("Gemini API call failed:", e);
    throw e;
  }
};
