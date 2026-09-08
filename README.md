# AGENTS-SDK-LAB

เว็บแอป Next.js + TypeScript ที่ใช้ Supabase Auth/RLS เก็บบทสนทนาจริง และเรียก
xAI Grok ผ่าน OpenAI-compatible API และ Agents SDK เฉพาะใน API route ฝั่ง server

## การตั้งค่า

ต้องใช้ Node.js 22 ขึ้นไป จากนั้นติดตั้ง dependencies:

```bash
npm install
cp .env.example .env.local
```

กำหนดค่าใน `.env.local` โดยใช้ anon key หรือ publishable key ของ Supabase LAB
และ xAI API key สำหรับ server:

```env
NEXT_PUBLIC_SUPABASE_URL=https://jwnbaidkwubbfqfwmcan.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_or_publishable_key
XAI_API_KEY=your_server_only_xai_api_key
XAI_MODEL=grok-3-latest
```

ห้ามนำ `XAI_API_KEY` ไปใช้ใน Client Component และห้ามใช้หรือเพิ่ม
Supabase `service_role` key ในโปรเจกต์นี้ API route ใช้ anon key ร่วมกับ access
token ของผู้ใช้ เพื่อให้ RLS ทำงานทุก query

จากนั้นรัน:

```bash
npm run dev
```

เปิด http://localhost:43127

## สร้างฐานข้อมูล

Migration ใน `supabase/migrations/` สอดคล้องกับ Supabase LAB `jwnbaidkwubbfqfwmcan`:

- `20260907183254_create_chat_core_schema.sql`
- `20260908091159_add_chat_requests_and_reply_links.sql`

สำหรับ Supabase project ที่ link แล้ว (LAB มี migrations เหล่านี้ apply แล้ว — ไม่ต้อง push ซ้ำ):

```bash
npx supabase@latest link --project-ref jwnbaidkwubbfqfwmcan
```

สำหรับฐานข้อมูล local:

```bash
npx supabase@latest start
npx supabase@latest db reset
```

Schema หลักใช้ `profiles.display_name`, `conversations.model_label`, `messages.metadata`
และ `chat_requests` สำหรับ idempotency ของ Agent

Migration ถอนสิทธิ์ของ role `anon` จากทุกตารางของแชต (`profiles`,
`conversations`, `messages`, `chat_requests`) ผู้ใช้ที่ authenticated
อ่านและเขียนได้เฉพาะแถวของตนเอง

## การทำงานของแชต

1. Client บันทึกข้อความผู้ใช้จริงผ่าน Supabase และ RLS
2. Client ส่ง access token, conversation ID และ message ID ไป `POST /api/chat`
3. Server ตรวจ token และสิทธิ์เจ้าของข้อมูล แล้วอ่านประวัติล่าสุดไม่เกิน 20 ข้อความ
4. Agent `AGENTS-SDK-LAB` เรียก xAI Grok (`grok-3-latest` โดย default) ผ่าน `https://api.x.ai/v1`
5. Server บันทึกคำตอบจริงลง `messages` ก่อนส่งแถวนั้นกลับไปแสดงผล

ระบบไม่สร้าง mock/fake AI response และ Agent จะไม่กล่าวอ้างว่างานภายนอกสำเร็จ
หากไม่มีหลักฐานในบทสนทนา

## Single-room chat hub

ผู้ใช้แต่ละคนมีห้องสนทนาเดียวชื่อ `Chat Hub` บนหน้า `/` (ไม่มี route `/hub` แยก)
ข้อความทั้งหมดซิงก์ผ่าน Supabase และ Agent ตอบผ่าน `POST /api/chat`

## คำสั่งตรวจสอบ

```bash
npm run lint
npm run type-check
npm run build
node --test tests/free-model.mjs
npm test
git diff --check
```
