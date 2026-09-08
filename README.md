<!--
  ⚠️ MERGE NOTE — UNRESOLVED PROJECT DIRECTION
  This branch merges two divergent histories that describe *different* products:
    1. A Next.js + Supabase chat app (imported into `main` via PR #5).
    2. A Python "agents-lab" package + Cloud Agent environment (this PR).
  Both READMEs are preserved below to avoid losing information, but the repository
  needs a human decision on its actual direction (see the PR discussion). Once
  decided, delete the section that does not apply and remove this note.
  Note: `.cursor/environment.json` currently provisions only the Python toolchain
  and does NOT set up the Next.js/Supabase app.
-->

# AGENTS-SDK-LAB

เว็บแอป Next.js + TypeScript สำหรับล็อกอินและบันทึกบทสนทนาจริงใน Supabase

## การตั้งค่า

ต้องใช้ Node.js 20.9 ขึ้นไป จากนั้นติดตั้ง dependencies:

```bash
npm install
cp .env.example .env.local
```

กำหนด `NEXT_PUBLIC_SUPABASE_ANON_KEY` ใน `.env.local` เป็น anon key หรือ
publishable key ของโปรเจกต์ Supabase นี้:

```env
NEXT_PUBLIC_SUPABASE_URL=https://jwnbaidkwubbfqfwmcan.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_or_publishable_key
```

ห้ามใช้ `service_role` key ในแอปฝั่ง browser

จากนั้นรัน:

```bash
npm run dev
```

เปิด http://localhost:43127

## ตารางที่ใช้

แอปใช้ตารางเดิมโดยตรงและไม่ได้สร้างข้อมูลจำลอง:

- `profiles`: อ่านโปรไฟล์ด้วย `id` ที่ตรงกับ Auth user
- `conversations`: อ่าน/สร้างด้วย `id`, `user_id`, `title`, `created_at`, `updated_at`
- `messages`: อ่าน/สร้างด้วย `id`, `conversation_id`, `user_id`, `role`, `content`, `created_at`

Supabase ต้องเปิด Email/Password authentication และกำหนด Row Level Security policies
ให้ผู้ใช้ที่ล็อกอินอ่านและสร้างได้เฉพาะแถวของตนเอง แอปส่ง access token ของผู้ใช้
ไปกับทุก query และไม่ใช้ `service_role` เพื่อข้าม RLS หาก schema ของตารางเดิมใช้ชื่อ
คอลัมน์ต่างจากรายการข้างต้น ให้ปรับ query ใน
`src/components/chat-workspace.tsx` ให้ตรงกับ schema จริง

โปรเจกต์นี้ยังไม่เชื่อม AI provider ข้อความที่ผู้ใช้ส่งจะถูกบันทึกจริงใน Supabase
โดยไม่มีการสร้างคำตอบจำลอง

## คำสั่งตรวจสอบ

```bash
npm run lint
npm run type-check
npm run build
```

---

# tha-abatb-agents-sdk-lab (Python)

A minimal, self-contained lab for experimenting with **tool-calling agents** in Python.

It implements the core pieces of an "agents SDK" with zero runtime dependencies, so it
runs end-to-end offline (no API keys required):

- `Tool` / `@tool` — wrap a plain function as a tool an agent can call.
- `Model` — decides the next action (call a tool or answer). `MockModel` is a
  deterministic, offline default.
- `Agent` — a name, instructions, tools, and a model.
- `Runner` — drives the loop: model → tool → observation → … → final answer.

## Requirements

- Python 3.10+

## Setup

```bash
pip install -e ".[dev]"
```

## Run the demo

```bash
agents-lab "Compute (6 * 7) + 3"        # -> The calculator result is 45.0.
agents-lab --trace "Compute (6 * 7) + 3" # show each tool call
python -m agents_lab "hello there"       # -> The echo result is hello there.
```

## Use it in code

```python
from agents_lab import Runner, build_demo_agent

result = Runner.run(build_demo_agent(), "Compute (6 * 7) + 3")
print(result.final_output)  # The calculator result is 45.0.
```

## Development

```bash
ruff check .          # lint
mypy                  # type-check (config in pyproject.toml)
pytest                # run tests
```
