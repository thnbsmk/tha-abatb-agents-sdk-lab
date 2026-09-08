import "server-only";

import { Agent } from "@openai/agents";

import { CHAT_AGENT_INSTRUCTIONS } from "@/lib/chat-constants";
import { getXaiModelName } from "@/lib/xai";

export const chatAgent = new Agent({
  name: "AGENTS-SDK-LAB",
  model: getXaiModelName(),
  instructions: CHAT_AGENT_INSTRUCTIONS,
});
