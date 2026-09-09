import { run } from "@openai/agents";
import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";
import { z } from "zod";

import { chatAgent } from "@/lib/agent";

import { resolveChatRequest, type ChatDb } from "./resolve";

export const runtime = "nodejs";

const requestSchema = z.object({
  conversationId: z.string().uuid(),
  userMessageId: z.string().uuid(),
});

function bearerToken(request: Request) {
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Bearer ")) return null;

  const token = authorization.slice("Bearer ".length).trim();
  return token || null;
}

export async function POST(request: Request) {
  const token = bearerToken(request);
  if (!token) {
    return NextResponse.json(
      { error: "Missing Supabase access token" },
      { status: 401 },
    );
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!supabaseUrl || !supabaseAnonKey || !process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      { error: "Server environment is not configured" },
      { status: 500 },
    );
  }

  let parsedBody: z.infer<typeof requestSchema>;
  try {
    parsedBody = requestSchema.parse(await request.json());
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  // This client uses the public anon key plus the caller's verified access
  // token. RLS remains active; no service_role credential is used.
  const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: false,
      detectSessionInUrl: false,
      persistSession: false,
    },
    global: {
      headers: { Authorization: `Bearer ${token}` },
    },
  });

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser(token);
  if (authError || !user) {
    return NextResponse.json(
      { error: "Invalid or expired access token" },
      { status: 401 },
    );
  }

  const { data: conversation, error: conversationError } = await supabase
    .from("conversations")
    .select("id")
    .eq("id", parsedBody.conversationId)
    .eq("user_id", user.id)
    .maybeSingle();
  if (conversationError) {
    return NextResponse.json(
      { error: "Could not read the conversation" },
      { status: 500 },
    );
  }
  if (!conversation) {
    return NextResponse.json({ error: "Conversation not found" }, { status: 404 });
  }

  const { data: userMessage, error: userMessageError } = await supabase
    .from("messages")
    .select("id")
    .eq("id", parsedBody.userMessageId)
    .eq("conversation_id", conversation.id)
    .eq("user_id", user.id)
    .eq("role", "user")
    .maybeSingle();
  if (userMessageError) {
    return NextResponse.json(
      { error: "Could not verify the user message" },
      { status: 500 },
    );
  }
  if (!userMessage) {
    return NextResponse.json({ error: "User message not found" }, { status: 404 });
  }

  const result = await resolveChatRequest({
    conversationId: conversation.id,
    db: supabase as unknown as ChatDb,
    runner: async (input) => {
      const agentResult = await run(chatAgent, input);
      return { finalOutput: agentResult.finalOutput };
    },
    userId: user.id,
    userMessageId: userMessage.id,
  });

  return NextResponse.json(result.body, { status: result.status });
}
