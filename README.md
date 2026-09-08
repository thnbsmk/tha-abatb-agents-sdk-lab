# AGENTS-SDK-LAB

เว็บแอป Next.js + TypeScript ที่ใช้ Supabase Auth/RLS เก็บบทสนทนาจริง และเรียก
OpenAI Agents SDK เฉพาะใน API route ฝั่ง server

## การตั้งค่า

ต้องใช้ Node.js 22 ขึ้นไป จากนั้นติดตั้ง dependencies:

```bash
npm install
cp .env.example .env.local
```

กำหนดค่าใน `.env.local` โดยใช้ anon key หรือ publishable key ของ Supabase
และ OpenAI API key สำหรับ server:

```env
NEXT_PUBLIC_SUPABASE_URL=https://jwnbaidkwubbfqfwmcan.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_or_publishable_key
OPENAI_API_KEY=your_server_only_openai_api_key
```

ห้ามนำ `OPENAI_API_KEY` ไปใช้ใน Client Component และห้ามใช้หรือเพิ่ม
Supabase `service_role` key ในโปรเจกต์นี้ API route ใช้ anon key ร่วมกับ access
token ของผู้ใช้ เพื่อให้ RLS ทำงานทุก query

จากนั้นรัน:

```bash
npm run dev
```

เปิด http://localhost:43127

## สร้างฐานข้อมูล

Migration อยู่ที่ `supabase/migrations/*_create_chat_schema.sql` และสร้างตาราง
foreign keys, indexes, triggers และ RLS policies ที่จำเป็นทั้งหมด

สำหรับ Supabase project ที่ link แล้ว:

```bash
npx supabase@latest link --project-ref YOUR_PROJECT_REF
npx supabase@latest db push
```

สำหรับฐานข้อมูล local:

```bash
npx supabase@latest start
npx supabase@latest db reset
```

Migration ถอนสิทธิ์ของ role `anon` จากทุกตารางของแชต (`profiles`,
`conversations`, `messages`, `chat_requests`) ผู้ใช้ที่ authenticated
อ่านและเขียนได้เฉพาะแถวที่ `user_id` ตรงกับ `auth.uid()` เท่านั้น

## การทำงานของแชต

1. Client บันทึกข้อความผู้ใช้จริงผ่าน Supabase และ RLS
2. Client ส่ง access token, conversation ID และ message ID ไป `POST /api/chat`
3. Server ตรวจ token และสิทธิ์เจ้าของข้อมูล แล้วอ่านประวัติล่าสุดไม่เกิน 20 ข้อความ
4. Agent `AGENTS-SDK-LAB` สร้างคำตอบจริงโดยตอบภาษาเดียวกับข้อความล่าสุด
5. Server บันทึกคำตอบจริงลง `messages` ก่อนส่งแถวนั้นกลับไปแสดงผล

ระบบไม่สร้าง mock/fake AI response และ Agent จะไม่กล่าวอ้างว่างานภายนอกสำเร็จ
หากไม่มีหลักฐานในบทสนทนา

## Single-room chat hub

ผู้ใช้แต่ละคนมีห้องสนทนาเดียวชื่อ `Chat Hub` แทนการสร้างหลายบทสนทนา
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
