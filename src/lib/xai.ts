import "server-only";

import { setDefaultModelProvider } from "@openai/agents";
import { OpenAIProvider } from "@openai/agents-openai";

import { DEFAULT_XAI_MODEL } from "@/lib/chat-constants";

export const XAI_BASE_URL = "https://api.x.ai/v1";

let providerConfigured = false;

export function getXaiModelName() {
  return process.env.XAI_MODEL?.trim() || DEFAULT_XAI_MODEL;
}

export function ensureXaiProvider() {
  if (providerConfigured) return;

  const apiKey = process.env.XAI_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("XAI_API_KEY is not configured");
  }

  setDefaultModelProvider(
    new OpenAIProvider({
      apiKey,
      baseURL: XAI_BASE_URL,
    }),
  );
  providerConfigured = true;
}
