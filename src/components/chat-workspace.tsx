"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { SupabaseClient, User } from "@supabase/supabase-js";
import { FlaskConical, Loader2, LogOut, Menu, Send, X } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const HUB_CONVERSATION_TITLE = "Chat Hub";

type Row = Record<string, unknown>;

type Conversation = Row & {
  id: string;
  title?: string | null;
  created_at?: string;
  updated_at?: string;
};

type Message = Row & {
  id: string;
  conversation_id: string;
  content: string;
  role?: string;
  user_id?: string;
  created_at?: string;
};

type ChatWorkspaceProps = {
  supabase: SupabaseClient;
  user: User;
};

function displayDate(value?: string) {
  if (!value) return "";
  return new Intl.DateTimeFormat("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function ChatWorkspace({
  supabase,
  user,
}: ChatWorkspaceProps) {
  const [profile, setProfile] = useState<Row | null>(null);
  const [hubConversationId, setHubConversationId] = useState<string | null>(
    null,
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const profileName =
    (profile?.full_name as string | undefined) ||
    (profile?.username as string | undefined) ||
    user.email?.split("@")[0] ||
    "สมาชิก";

  const avatarUrl = profile?.avatar_url as string | undefined;

  const loadMessages = useCallback(
    async (conversationId: string) => {
      const { data, error: queryError } = await supabase
        .from("messages")
        .select("*")
        .eq("conversation_id", conversationId)
        .order("created_at", { ascending: true });

      if (queryError) {
        setError(queryError.message);
        return;
      }

      setMessages((data ?? []) as Message[]);
    },
    [supabase],
  );

  useEffect(() => {
    async function loadWorkspace() {
      setLoading(true);
      const [profileResult, conversationsResult] = await Promise.all([
        supabase.from("profiles").select("*").eq("id", user.id).maybeSingle(),
        supabase
          .from("conversations")
          .select("*")
          .eq("user_id", user.id)
          .eq("title", HUB_CONVERSATION_TITLE)
          .order("created_at", { ascending: true })
          .limit(1),
      ]);

      if (profileResult.error) {
        setError(profileResult.error.message);
      } else {
        setProfile(profileResult.data);
      }

      if (conversationsResult.error) {
        setError(conversationsResult.error.message);
      } else {
        const hub = (conversationsResult.data?.[0] ?? null) as
          | Conversation
          | null;
        if (hub) {
          setHubConversationId(hub.id);
          await loadMessages(hub.id);
        }
      }
      setLoading(false);
    }

    void loadWorkspace();
  }, [loadMessages, supabase, user.id]);

  useEffect(() => {
    if (!hubConversationId) return;

    const channel = supabase
      .channel(`messages:${hubConversationId}`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "messages",
          filter: `conversation_id=eq.${hubConversationId}`,
        },
        () => void loadMessages(hubConversationId),
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [hubConversationId, loadMessages, supabase]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(event: React.FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending) return;

    setSending(true);
    setError(null);

    const {
      data: { session },
      error: sessionError,
    } = await supabase.auth.getSession();
    if (sessionError || !session?.access_token) {
      setError(sessionError?.message || "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่");
      setSending(false);
      return;
    }

    let conversationId = hubConversationId;
    if (!conversationId) {
      const { data, error: conversationError } = await supabase
        .from("conversations")
        .insert({
          user_id: user.id,
          title: HUB_CONVERSATION_TITLE,
        })
        .select("*")
        .single();

      if (conversationError) {
        setError(conversationError.message);
        setSending(false);
        return;
      }

      const conversation = data as Conversation;
      conversationId = conversation.id;
      setHubConversationId(conversation.id);
    }

    const { data: savedMessage, error: messageError } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        user_id: user.id,
        role: "user",
        content,
      })
      .select("*")
      .single();

    if (messageError) {
      setError(messageError.message);
      setSending(false);
      return;
    }

    setMessages((current) => {
      if (current.some((message) => message.id === savedMessage.id)) {
        return current;
      }
      return [...current, savedMessage as Message];
    });
    setDraft("");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          conversationId,
          userMessageId: savedMessage.id,
        }),
      });
      const payload = (await response.json().catch(() => null)) as {
        error?: string;
        message?: Message;
        status?: "completed" | "in_progress";
      } | null;

      if (response.status === 202 && payload?.status === "in_progress") {
        return;
      }

      if (!response.ok || !payload?.message) {
        throw new Error(payload?.error || "ไม่สามารถรับคำตอบจาก Agent ได้");
      }

      setMessages((current) => {
        if (current.some((message) => message.id === payload.message?.id)) {
          return current;
        }
        return [...current, payload.message as Message];
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "ไม่สามารถรับคำตอบจาก Agent ได้",
      );
    } finally {
      setSending(false);
    }
  }

  const sidebar = (
    <aside className="flex h-full w-[290px] shrink-0 flex-col border-r border-white/10 bg-[#14382f] text-[#eef3e9]">
      <div className="flex h-20 items-center justify-between border-b border-white/10 px-5">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-xl bg-[#f2cf9f] text-[#14382f]">
            <FlaskConical className="size-4" />
          </span>
          <div>
            <p className="text-[10px] font-semibold tracking-[0.24em] text-[#efb18e]">
              AGENTS
            </p>
            <p className="font-mono text-xs font-semibold">SDK—LAB</p>
          </div>
        </div>
        <Button
          aria-label="ปิดเมนู"
          className="text-white md:hidden"
          onClick={() => setSidebarOpen(false)}
          size="icon"
          variant="ghost"
        >
          <X />
        </Button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col px-5 py-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/45">
          Single-room hub
        </p>
        <h2 className="mt-2 font-serif text-2xl font-semibold text-white">
          {HUB_CONVERSATION_TITLE}
        </h2>
        <p className="mt-3 text-sm leading-6 text-white/62">
          ผู้ใช้แต่ละคนมีห้องสนทนาเดียว ข้อความทั้งหมดซิงก์ผ่าน Supabase และ
          Agent ตอบผ่าน API route ฝั่ง server
        </p>
      </div>

      <div className="border-t border-white/10 p-4">
        <div className="flex items-center gap-3">
          <Avatar className="size-9 border border-white/15">
            <AvatarImage alt={profileName} src={avatarUrl} />
            <AvatarFallback className="bg-[#b85f43] text-white">
              {profileName.slice(0, 1).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{profileName}</p>
            <p className="truncate text-[11px] text-white/45">{user.email}</p>
          </div>
          <Button
            aria-label="ออกจากระบบ"
            className="text-white/60 hover:text-white"
            onClick={() => void supabase.auth.signOut()}
            size="icon"
            variant="ghost"
          >
            <LogOut />
          </Button>
        </div>
      </div>
    </aside>
  );

  return (
    <main className="flex h-dvh overflow-hidden bg-[#f4f2ea]">
      <div className="hidden md:block">{sidebar}</div>
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          {sidebar}
          <button
            aria-label="ปิดเมนู"
            className="flex-1 bg-black/30 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
            type="button"
          />
        </div>
      )}

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-20 shrink-0 items-center gap-3 border-b border-black/7 bg-[#faf9f5]/90 px-4 backdrop-blur md:px-7">
          <Button
            aria-label="เปิดเมนู"
            className="md:hidden"
            onClick={() => setSidebarOpen(true)}
            size="icon"
            variant="ghost"
          >
            <Menu />
          </Button>
          <div className="min-w-0">
            <h1 className="truncate font-serif text-xl font-semibold text-[#1d312b]">
              {HUB_CONVERSATION_TITLE}
            </h1>
            <p className="text-xs text-[#74807b]">
              ห้องสนทนาเดียวต่อผู้ใช้ · บันทึกและซิงก์ผ่าน Supabase
            </p>
          </div>
          <span className="ml-auto flex items-center gap-2 text-xs text-[#60736c]">
            <span className="size-2 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]" />
            <span className="hidden sm:inline">เชื่อมต่อแล้ว</span>
          </span>
        </header>

        {error && (
          <Alert className="m-4 mb-0 border-red-200 bg-red-50 text-red-800 md:mx-7">
            <AlertDescription className="flex items-center justify-between gap-3">
              <span>{error}</span>
              <button
                className="shrink-0 font-semibold"
                onClick={() => setError(null)}
                type="button"
              >
                ปิด
              </button>
            </AlertDescription>
          </Alert>
        )}

        <ScrollArea className="min-h-0 flex-1">
          <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col px-4 py-7 md:px-8 md:py-10">
            {loading ? (
              <div className="grid flex-1 place-items-center">
                <Loader2 className="size-6 animate-spin text-[#2c5b4d]" />
              </div>
            ) : messages.length === 0 ? (
              <div className="grid flex-1 place-items-center py-16 text-center">
                <div>
                  <span className="mx-auto mb-5 grid size-14 place-items-center rounded-2xl border border-[#d9d3c5] bg-white text-[#b05237] shadow-sm">
                    <FlaskConical className="size-6" />
                  </span>
                  <h2 className="font-serif text-3xl font-semibold tracking-tight text-[#20342e]">
                    เริ่มทดลองไอเดีย
                  </h2>
                  <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-[#6e7974]">
                    ส่งข้อความแรกเพื่อเปิดห้อง {HUB_CONVERSATION_TITLE}
                    ทุกข้อความจะถูกบันทึกลง conversations และ messages ของคุณ
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-auto space-y-6">
                {messages.map((message) => {
                  const mine = message.role === "user";
                  return (
                    <div
                      className={cn(
                        "flex gap-3",
                        mine ? "justify-end" : "justify-start",
                      )}
                      key={message.id}
                    >
                      <div
                        className={cn(
                          "max-w-[82%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[72%]",
                          mine
                            ? "rounded-br-md bg-[#205346] text-white"
                            : "rounded-bl-md border border-black/7 bg-white text-[#26352f]",
                        )}
                      >
                        <p className="whitespace-pre-wrap text-sm leading-6">
                          {message.content}
                        </p>
                        <p
                          className={cn(
                            "mt-1.5 text-[10px]",
                            mine ? "text-white/55" : "text-black/40",
                          )}
                        >
                          {displayDate(message.created_at)}
                        </p>
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="shrink-0 border-t border-black/7 bg-[#faf9f5] p-4 md:px-7 md:py-5">
          <form
            className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-black/10 bg-white p-2 shadow-lg shadow-slate-900/5 focus-within:border-[#377565]/50 focus-within:ring-4 focus-within:ring-[#377565]/8"
            onSubmit={sendMessage}
          >
            <Textarea
              aria-label="ข้อความ"
              className="max-h-36 min-h-11 resize-none border-0 bg-transparent px-3 py-3 shadow-none focus-visible:ring-0"
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="พิมพ์ข้อความ…"
              rows={1}
              value={draft}
            />
            <Button
              aria-label="ส่งข้อความ"
              className="size-11 shrink-0 rounded-xl bg-[#b05237] text-white hover:bg-[#963f28]"
              disabled={!draft.trim() || sending}
              size="icon"
              type="submit"
            >
              {sending ? <Loader2 className="animate-spin" /> : <Send />}
            </Button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[10px] text-[#8b928e]">
            Enter เพื่อส่ง · Shift + Enter เพื่อขึ้นบรรทัดใหม่
          </p>
        </div>
      </section>
    </main>
  );
}
