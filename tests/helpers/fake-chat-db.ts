// An in-memory stand-in for the Supabase client used by `resolveChatRequest`.
//
// It models only what the endpoint relies on, but it faithfully enforces the
// invariants the crash-safety logic depends on:
//   - chat_requests has a composite primary key (conversation_id,
//     user_message_id); a second insert conflicts (Postgres error 23505).
//   - messages allows at most one reply per user message
//     (conversation_id, reply_to_message_id); a second insert conflicts.
//   - a conditional UPDATE ... RETURNING only "reclaims" a row whose current
//     state still matches the filters, and bumps updated_at (as the DB trigger
//     does), which is what makes concurrent reclaim safe.

import { randomUUID } from "node:crypto";

import type { ChatDb, DbError, Queryable, Row, TableRef } from "../../src/app/api/chat/resolve";

type Filter = { op: "eq" | "lt"; column: string; value: unknown };
type Mode = "select" | "insert" | "update";

export interface FakeChatDbOptions {
  now?: () => number;
}

export class FakeChatDb implements ChatDb {
  private readonly tables: Record<string, Row[]> = {
    conversations: [],
    messages: [],
    chat_requests: [],
  };

  private readonly errorQueue: Array<{ tag: string; error: DbError }> = [];
  private readonly clock: () => number;

  constructor(options: FakeChatDbOptions = {}) {
    this.clock = options.now ?? Date.now;
  }

  from(table: string): TableRef {
    return new FakeQuery(this, table);
  }

  // --- Test seeding & assertions -------------------------------------------

  seedMessage(row: Row): void {
    this.tables.messages.push({
      created_at: this.nowIso(),
      id: randomUUID(),
      reply_to_message_id: null,
      ...row,
    });
  }

  seedChatRequest(row: Row): void {
    const iso = this.nowIso();
    this.tables.chat_requests.push({
      created_at: iso,
      response_message_id: null,
      status: "in_progress",
      updated_at: iso,
      ...row,
    });
  }

  request(conversationId: string, userMessageId: string): Row | undefined {
    return this.tables.chat_requests.find(
      (row) =>
        row.conversation_id === conversationId && row.user_message_id === userMessageId,
    );
  }

  assistantReplies(userMessageId: string): Row[] {
    return this.tables.messages.filter(
      (row) => row.role === "assistant" && row.reply_to_message_id === userMessageId,
    );
  }

  // --- Error injection ------------------------------------------------------

  queueError(tag: string, error: DbError): void {
    this.errorQueue.push({ tag, error });
  }

  // --- Internal execution (called by FakeQuery) -----------------------------

  nowIso(): string {
    return new Date(this.clock()).toISOString();
  }

  takeError(tag: string): DbError | undefined {
    const index = this.errorQueue.findIndex((entry) => entry.tag === tag);
    if (index === -1) return undefined;
    const [entry] = this.errorQueue.splice(index, 1);
    return entry.error;
  }

  execInsert(table: string, values: Row): { data: Row[]; error: DbError } {
    if (table === "chat_requests") {
      const exists = this.request(
        String(values.conversation_id),
        String(values.user_message_id),
      );
      if (exists) {
        return { data: [], error: { code: "23505", message: "duplicate chat_requests" } };
      }
      const iso = this.nowIso();
      const row: Row = {
        created_at: iso,
        response_message_id: values.response_message_id ?? null,
        status: values.status ?? "in_progress",
        updated_at: iso,
        ...values,
      };
      this.tables.chat_requests.push(row);
      return { data: [row], error: null };
    }

    if (table === "messages") {
      const replyTo = values.reply_to_message_id ?? null;
      if (replyTo !== null) {
        const clash = this.tables.messages.some(
          (row) =>
            row.conversation_id === values.conversation_id &&
            row.reply_to_message_id === replyTo,
        );
        if (clash) {
          return { data: [], error: { code: "23505", message: "duplicate reply" } };
        }
      }
      const row: Row = {
        created_at: this.nowIso(),
        id: randomUUID(),
        reply_to_message_id: replyTo,
        ...values,
      };
      this.tables.messages.push(row);
      return { data: [row], error: null };
    }

    const generic: Row = { ...values };
    this.tables[table] = this.tables[table] ?? [];
    this.tables[table].push(generic);
    return { data: [generic], error: null };
  }

  execUpdate(table: string, values: Row, filters: Filter[]): { data: Row[]; error: DbError } {
    const rows = this.tables[table] ?? [];
    const matched = rows.filter((row) => matchesAll(row, filters));
    for (const row of matched) {
      Object.assign(row, values);
      row.updated_at = this.nowIso();
    }
    return { data: matched, error: null };
  }

  execSelect(
    table: string,
    filters: Filter[],
    orderSpec: { column: string; ascending: boolean } | null,
    limitN: number | null,
  ): { data: Row[]; error: DbError } {
    let rows = (this.tables[table] ?? []).filter((row) => matchesAll(row, filters));
    if (orderSpec) {
      const { column, ascending } = orderSpec;
      rows = [...rows].sort((a, b) => {
        const left = String(a[column] ?? "");
        const right = String(b[column] ?? "");
        if (left === right) return 0;
        const order = left < right ? -1 : 1;
        return ascending ? order : -order;
      });
    }
    if (limitN !== null) {
      rows = rows.slice(0, limitN);
    }
    return { data: rows, error: null };
  }
}

function matchesAll(row: Row, filters: Filter[]): boolean {
  return filters.every((filter) => {
    if (filter.op === "eq") return row[filter.column] === filter.value;
    return String(row[filter.column] ?? "") < String(filter.value);
  });
}

class FakeQuery implements Queryable {
  private mode: Mode = "select";
  private values: Row = {};
  private readonly filters: Filter[] = [];
  private orderSpec: { column: string; ascending: boolean } | null = null;
  private limitN: number | null = null;
  private modeLocked = false;

  constructor(
    private readonly db: FakeChatDb,
    private readonly table: string,
  ) {}

  select(): this {
    if (!this.modeLocked) this.mode = "select";
    return this;
  }

  insert(values: Row): this {
    this.mode = "insert";
    this.modeLocked = true;
    this.values = values;
    return this;
  }

  update(values: Row): this {
    this.mode = "update";
    this.modeLocked = true;
    this.values = values;
    return this;
  }

  eq(column: string, value: unknown): this {
    this.filters.push({ op: "eq", column, value });
    return this;
  }

  lt(column: string, value: unknown): this {
    this.filters.push({ op: "lt", column, value });
    return this;
  }

  order(column: string, options: { ascending: boolean }): this {
    this.orderSpec = { column, ascending: options.ascending };
    return this;
  }

  limit(count: number): this {
    this.limitN = count;
    return this;
  }

  async maybeSingle(): Promise<{ data: Row | null; error: DbError }> {
    const { data, error } = this.run();
    return { data: data[0] ?? null, error };
  }

  async single(): Promise<{ data: Row | null; error: DbError }> {
    const { data, error } = this.run();
    if (error) return { data: null, error };
    if (data.length === 0) {
      return { data: null, error: { code: "PGRST116", message: "no rows returned" } };
    }
    return { data: data[0], error: null };
  }

  then<TResult1 = { data: Row[]; error: DbError }, TResult2 = never>(
    onfulfilled?:
      | ((value: { data: Row[]; error: DbError }) => TResult1 | PromiseLike<TResult1>)
      | null,
    onrejected?: ((reason: unknown) => TResult2 | PromiseLike<TResult2>) | null,
  ): PromiseLike<TResult1 | TResult2> {
    return Promise.resolve(this.run()).then(onfulfilled, onrejected);
  }

  private run(): { data: Row[]; error: DbError } {
    const forced = this.db.takeError(this.tag());
    if (forced) return { data: [], error: forced };

    if (this.mode === "insert") return this.db.execInsert(this.table, this.values);
    if (this.mode === "update") {
      return this.db.execUpdate(this.table, this.values, this.filters);
    }
    return this.db.execSelect(this.table, this.filters, this.orderSpec, this.limitN);
  }

  // A stable label per logical query so tests can inject targeted failures.
  private tag(): string {
    if (this.table === "chat_requests") {
      if (this.mode === "insert") return "chat_requests:claim";
      if (this.mode === "update") {
        if (this.values.status === "completed") return "chat_requests:complete";
        if (this.values.status === "failed") return "chat_requests:release";
        if (this.filters.some((f) => f.column === "status" && f.value === "failed")) {
          return "chat_requests:reclaimFailed";
        }
        if (this.filters.some((f) => f.op === "lt")) return "chat_requests:reclaimStale";
        return "chat_requests:update";
      }
      return "chat_requests:select";
    }
    if (this.table === "messages") {
      if (this.mode === "insert") return "messages:save";
      if (this.limitN !== null) return "messages:history";
      return "messages:reply";
    }
    return `${this.table}:${this.mode}`;
  }
}
