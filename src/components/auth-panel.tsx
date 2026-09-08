"use client";

import { useState } from "react";
import { FlaskConical, Loader2 } from "lucide-react";
import type { SupabaseClient } from "@supabase/supabase-js";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type AuthPanelProps = {
  supabase: SupabaseClient;
};

export function AuthPanel({ supabase }: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{
    kind: "error" | "success";
    text: string;
  } | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);

    const result =
      mode === "login"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });

    if (result.error) {
      setMessage({ kind: "error", text: result.error.message });
    } else if (mode === "signup" && !result.data.session) {
      setMessage({
        kind: "success",
        text: "สร้างบัญชีแล้ว กรุณายืนยันอีเมลก่อนเข้าสู่ระบบ",
      });
    }

    setBusy(false);
  }

  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden bg-[#f5f4ee] px-5 py-12">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(217,119,87,0.14),transparent_34%),radial-gradient(circle_at_80%_78%,rgba(40,89,72,0.12),transparent_35%)]" />
      <div className="relative w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-3">
          <span className="grid size-11 place-items-center rounded-2xl bg-[#173f34] text-[#f8f4e8] shadow-lg shadow-emerald-950/10">
            <FlaskConical className="size-5" />
          </span>
          <div>
            <p className="text-xs font-semibold tracking-[0.22em] text-[#b05237]">
              AGENTS
            </p>
            <p className="font-mono text-sm font-semibold text-[#173f34]">
              SDK—LAB
            </p>
          </div>
        </div>

        <Card className="border-black/8 bg-white/88 shadow-2xl shadow-slate-900/8 backdrop-blur">
          <CardHeader className="space-y-2 px-7 pt-7">
            <CardTitle className="font-serif text-3xl tracking-tight text-[#182a25]">
              {mode === "login" ? "กลับเข้าสู่แล็บ" : "สร้างบัญชี"}
            </CardTitle>
            <CardDescription className="text-sm leading-6">
              {mode === "login"
                ? "เข้าสู่ระบบเพื่อเปิดบทสนทนาที่บันทึกไว้ใน Supabase"
                : "สมัครด้วยอีเมลเพื่อเริ่มบทสนทนาแรกของคุณ"}
            </CardDescription>
          </CardHeader>
          <CardContent className="px-7 pb-7">
            <form className="space-y-5" onSubmit={submit}>
              <div className="space-y-2">
                <Label htmlFor="email">อีเมล</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">รหัสผ่าน</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="อย่างน้อย 6 ตัวอักษร"
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  minLength={6}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>

              {message && (
                <Alert
                  variant={message.kind === "error" ? "destructive" : "default"}
                >
                  <AlertDescription>{message.text}</AlertDescription>
                </Alert>
              )}

              <Button
                className="w-full bg-[#173f34] text-white hover:bg-[#225746]"
                disabled={busy}
                type="submit"
              >
                {busy && <Loader2 className="animate-spin" />}
                {mode === "login" ? "เข้าสู่ระบบ" : "สมัครสมาชิก"}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              {mode === "login" ? "ยังไม่มีบัญชี?" : "มีบัญชีแล้ว?"}{" "}
              <button
                className="font-semibold text-[#b05237] underline-offset-4 hover:underline"
                onClick={() => {
                  setMode(mode === "login" ? "signup" : "login");
                  setMessage(null);
                }}
                type="button"
              >
                {mode === "login" ? "สมัครสมาชิก" : "เข้าสู่ระบบ"}
              </button>
            </p>
          </CardContent>
        </Card>
        <p className="mt-5 text-center text-xs text-[#69756f]">
          ข้อมูลบัญชีและบทสนทนาถูกจัดเก็บใน Supabase Project ของคุณ
        </p>
      </div>
    </main>
  );
}
