"use client";

import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { AlertTriangle, FlaskConical, Loader2 } from "lucide-react";

import { AuthPanel } from "@/components/auth-panel";
import { ChatWorkspace } from "@/components/chat-workspace";
import { getSupabaseBrowserClient } from "@/lib/supabase";

const supabase = getSupabaseBrowserClient();

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(Boolean(supabase));

  useEffect(() => {
    if (!supabase) return;

    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!supabase) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f5f4ee] px-5">
        <div className="w-full max-w-lg rounded-3xl border border-amber-200 bg-white p-8 shadow-xl shadow-slate-900/5">
          <span className="mb-5 grid size-12 place-items-center rounded-2xl bg-amber-100 text-amber-800">
            <AlertTriangle />
          </span>
          <h1 className="font-serif text-2xl font-semibold text-[#1d312b]">
            ต้องตั้งค่า Supabase ก่อน
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            คัดลอกไฟล์{" "}
            <code className="rounded bg-muted px-1.5 py-0.5">.env.example</code>{" "}
            เป็น{" "}
            <code className="rounded bg-muted px-1.5 py-0.5">.env.local</code>{" "}
            แล้วใส่ anon หรือ publishable key ของ Supabase Project
          </p>
          <p className="mt-4 text-xs text-amber-800">
            แอปนี้ไม่ใช้และไม่ต้องการ service_role key
          </p>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f5f4ee]">
        <div className="flex items-center gap-3 text-[#173f34]">
          <FlaskConical className="size-5" />
          <Loader2 className="size-5 animate-spin" />
        </div>
      </main>
    );
  }

  if (!session) {
    return <AuthPanel supabase={supabase} />;
  }

  return <ChatWorkspace supabase={supabase} user={session.user} />;
}
