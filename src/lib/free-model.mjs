import { Agent, Runner } from "@openai/agents";
import {
  ScriptedModel,
  assistantMessage,
} from "@openai/agents/testing";

export const CHAT_AGENT_INSTRUCTIONS = [
  "You are AGENTS-SDK-LAB, a careful and concise assistant.",
  "Always answer in the same language as the user's latest message.",
  "Never claim that an external action succeeded unless the conversation contains concrete evidence that it succeeded.",
  "If evidence is missing, say clearly that the action has not been verified.",
].join(" ");

export const HUB_CONVERSATION_TITLE = "Chat Hub";

export function createFreeChatAgent() {
  return new Agent({
    name: "AGENTS-SDK-LAB",
    instructions: CHAT_AGENT_INSTRUCTIONS,
  });
}

export function createFreeChatModel(replyText = "สวัสดีจาก free model") {
  return new ScriptedModel([[assistantMessage(replyText)]]);
}

export function createFreeChatRunner(replyText = "สวัสดีจาก free model") {
  const model = createFreeChatModel(replyText);
  const runner = new Runner({ model, tracingDisabled: true });
  return { model, runner };
}
