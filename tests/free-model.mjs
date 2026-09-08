import assert from "node:assert/strict";
import test from "node:test";

import {
  CHAT_AGENT_INSTRUCTIONS,
  HUB_CONVERSATION_TITLE,
  createFreeChatAgent,
  createFreeChatRunner,
} from "../src/lib/free-model.mjs";

test("free model runs AGENTS-SDK-LAB offline without an API key", async () => {
  const agent = createFreeChatAgent();
  const { model, runner } = createFreeChatRunner("สวัสดีจาก free model");

  const result = await runner.run(agent, "สวัสดี");

  assert.equal(result.finalOutput, "สวัสดีจาก free model");
  assert.equal(model.calls.length, 1);
  model.assertComplete();
});

test("free model agent keeps the shared lab instructions", () => {
  const agent = createFreeChatAgent();

  assert.equal(agent.name, "AGENTS-SDK-LAB");
  assert.equal(agent.instructions, CHAT_AGENT_INSTRUCTIONS);
});

test("single-room hub uses one shared conversation title", () => {
  assert.equal(HUB_CONVERSATION_TITLE, "Chat Hub");
});
