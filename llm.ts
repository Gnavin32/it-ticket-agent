import { ChatOpenAI } from "@langchain/openai";
import { LLM_CONFIG } from "./config.js";
import "dotenv/config";

// This single client is reused by every node that needs to call the LLM
// (classify, notify_user). Pointed at OpenRouter instead of OpenAI directly —
// same API shape, different base URL + key.
export const llm = new ChatOpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  model: LLM_CONFIG.model,
  configuration: {
    baseURL: LLM_CONFIG.baseURL,
  },
  temperature: 0.2,
});