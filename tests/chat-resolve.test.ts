import assert from "node:assert/strict";
import { test } from "node:test";

import { resolveChatRequest, type ChatRunner, type ResolveParams } from "../src/app/api/chat/resolve";

import { FakeChatDb } from "./helpers/fake-chat-db";

const CONVERSATION_ID = "11111111-1111-1111-1111-111111111111";
const USER_MESSAGE_ID = "22222222-2222-2222-2222-222222222222";
const USER_ID = "33333333-3333-3333-3333-333333333333";
const FIXED_NOW = Date.UTC(2026, 0, 1, 12, 0, 0);

function seedUserTurn(db: FakeChatDb): void {
  db.seedMessage({
    content: "Hello",
    conversation_id: CONVERSATION_ID,
    id: USER_MESSAGE_ID,
    reply_to_message_id: null,
    role: "user",
    user_id: USER_ID,
  });
}

function params(
  db: FakeChatDb,
  runner: ChatRunner,
  extra: Partial<ResolveParams> = {},
): ResolveParams {
  return {
    conversationId: CONVERSATION_ID,
    db,
    runner,
    userId: USER_ID,
    userMessageId: USER_MESSAGE_ID,
    ...extra,
  };
}

function createDeferred<T>(): {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
} {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

// Lets already-queued microtasks (the awaited fake-DB calls) drain so an
// in-flight request parks on its pending runner before we start another one.
function flushMicrotasks(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function contentOf(body: Record<string, unknown>): string {
  return (body.message as { content: string }).content;
}

test("1. a duplicate request while processing returns 202 and never re-runs the agent", async () => {
  const db = new FakeChatDb();
  seedUserTurn(db);

  const deferred = createDeferred<{ finalOutput: string }>();
  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    return deferred.promise;
  };

  const inFlight = resolveChatRequest(params(db, runner));
  await flushMicrotasks();
  assert.equal(calls, 1, "the first request should have claimed the work and started the agent");

  const duplicate = await resolveChatRequest(params(db, runner));
  assert.equal(duplicate.status, 202);
  assert.deepEqual(duplicate.body, { status: "in_progress" });
  assert.equal(calls, 1, "the concurrent duplicate must not invoke the agent again");

  deferred.resolve({ finalOutput: "Hi there" });
  const first = await inFlight;
  assert.equal(first.status, 200);
  assert.equal(contentOf(first.body), "Hi there");
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 1, "exactly one reply is stored");
});

test("2. a duplicate request after completion returns the original reply", async () => {
  const db = new FakeChatDb();
  seedUserTurn(db);

  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    return { finalOutput: "Answer" };
  };

  const first = await resolveChatRequest(params(db, runner));
  assert.equal(first.status, 200);
  const firstId = (first.body.message as { id: string }).id;

  const second = await resolveChatRequest(params(db, runner));
  assert.equal(second.status, 200);
  assert.equal(second.body.status, "completed");
  assert.equal((second.body.message as { id: string }).id, firstId);
  assert.equal(contentOf(second.body), "Answer");
  assert.equal(calls, 1, "a completed request must not re-run the agent");
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 1);
});

test("3. a failed agent run releases the claim and a later retry succeeds", async () => {
  const db = new FakeChatDb();
  seedUserTurn(db);

  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    if (calls === 1) throw new Error("model exploded");
    return { finalOutput: "Recovered answer" };
  };

  const failed = await resolveChatRequest(params(db, runner));
  assert.equal(failed.status, 502);
  assert.equal(db.request(CONVERSATION_ID, USER_MESSAGE_ID)?.status, "failed");
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 0, "no reply is stored on failure");

  const retried = await resolveChatRequest(params(db, runner));
  assert.equal(retried.status, 200);
  assert.equal(contentOf(retried.body), "Recovered answer");
  assert.equal(calls, 2, "the retry re-runs the agent");
  assert.equal(db.request(CONVERSATION_ID, USER_MESSAGE_ID)?.status, "completed");
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 1);
});

test("4. a stale in_progress claim can be reclaimed and completed", async () => {
  const db = new FakeChatDb({ now: () => FIXED_NOW });
  seedUserTurn(db);

  const staleIso = new Date(FIXED_NOW - 10 * 60 * 1000).toISOString();
  db.seedChatRequest({
    conversation_id: CONVERSATION_ID,
    created_at: staleIso,
    response_message_id: null,
    status: "in_progress",
    updated_at: staleIso,
    user_id: USER_ID,
    user_message_id: USER_MESSAGE_ID,
  });

  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    return { finalOutput: "Fresh answer" };
  };

  const result = await resolveChatRequest(
    params(db, runner, { now: () => FIXED_NOW, staleAfterMs: 60 * 1000 }),
  );
  assert.equal(result.status, 200);
  assert.equal(contentOf(result.body), "Fresh answer");
  assert.equal(calls, 1);
  assert.equal(db.request(CONVERSATION_ID, USER_MESSAGE_ID)?.status, "completed");
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 1);
});

test("4b. a fresh in_progress claim is NOT reclaimed and returns 202", async () => {
  const db = new FakeChatDb({ now: () => FIXED_NOW });
  seedUserTurn(db);

  const recentIso = new Date(FIXED_NOW - 5 * 1000).toISOString();
  db.seedChatRequest({
    conversation_id: CONVERSATION_ID,
    created_at: recentIso,
    response_message_id: null,
    status: "in_progress",
    updated_at: recentIso,
    user_id: USER_ID,
    user_message_id: USER_MESSAGE_ID,
  });

  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    return { finalOutput: "should not run" };
  };

  const result = await resolveChatRequest(
    params(db, runner, { now: () => FIXED_NOW, staleAfterMs: 60 * 1000 }),
  );
  assert.equal(result.status, 202);
  assert.deepEqual(result.body, { status: "in_progress" });
  assert.equal(calls, 0, "a fresh claim must be left alone");
});

test("5. a history-read failure releases the claim so the request can be retried", async () => {
  const db = new FakeChatDb();
  seedUserTurn(db);
  db.queueError("messages:history", { code: "500", message: "history boom" });

  let calls = 0;
  const runner: ChatRunner = async () => {
    calls += 1;
    return { finalOutput: "Answer" };
  };

  const failed = await resolveChatRequest(params(db, runner));
  assert.equal(failed.status, 500);
  assert.equal(calls, 0, "the agent must not run when history cannot be read");
  assert.equal(db.request(CONVERSATION_ID, USER_MESSAGE_ID)?.status, "failed");

  const retried = await resolveChatRequest(params(db, runner));
  assert.equal(retried.status, 200);
  assert.equal(contentOf(retried.body), "Answer");
  assert.equal(calls, 1);
  assert.equal(db.assistantReplies(USER_MESSAGE_ID).length, 1);
});
