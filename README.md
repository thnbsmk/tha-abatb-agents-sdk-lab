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
