# codex / exec-server

Bootstrap สำหรับ **Cursor Remote** หรือเครื่อง self-hosted ที่ต้องเชื่อม ChatGPT / OpenAI Agents API กับ workspace จริงผ่าน `codex exec-server`

Repository หลักของแอป: [thnbsmk/tha-abatb-agents-sdk-lab](https://github.com/thnbsmk/tha-abatb-agents-sdk-lab)

## ใช้ใน Cursor Remote (แนะนำ)

รันใน **Terminal ของ Cursor Agent ลิงก์จากแบงก์** — ไม่ใช่ sandbox แชททั่วไป

```bash
git clone https://github.com/thnbsmk/exec-server.git /workspace/codex-exec-server
cd /workspace/codex-exec-server

./setup.sh
cp .env.example .env
# แก้ .env: ใส่ OPENAI_ENVIRONMENT_KEY, REMOTE_URL, ENVIRONMENT_ID จาก session

./check.sh
./connect.sh
```

ปล่อย `./connect.sh` ให้รันค้างไว้ แล้วกลับไปใช้งานใน ChatGPT / Agents session

## ค่าที่ต้องมี

| ตัวแปร | มาจากไหน |
|--------|----------|
| `OPENAI_ENVIRONMENT_KEY` | OpenAI Platform → Project → Agents → Environment key |
| `REMOTE_URL` | Session ปัจจุบัน (`.../connect/rt_...`) |
| `ENVIRONMENT_ID` | Session ปัจจุบัน (`ccarenv_...`) |
| `WORKSPACE_DIRECTORY` | โฟลเดอร์โค้ด (default `/workspace/agensdk`) |

## เชื่อมแบบ one-liner

```bash
REMOTE_URL='https://api.openai.com/v1/agents/api/connect/rt_xxx' \
ENVIRONMENT_ID='ccarenv_xxx' \
OPENAI_ENVIRONMENT_KEY='...' \
./connect.sh
```

## โครงสร้าง

```
exec-server/
  setup.sh       # clone workspace + install codex
  check.sh       # ตรวจ prerequisites
  connect.sh     # รัน exec-server
  .env.example
```

## หมายเหตุ

- `REMOTE_URL` และ `ENVIRONMENT_ID` เปลี่ยนทุก session
- ใช้ `OPENAI_ENVIRONMENT_KEY` เท่านั้นใน `connect.sh` — ไม่ใช้ `OPENAI_API_KEY`
- ถ้า `check.sh` ขึ้น missing แสดงว่ารันอยู่ผิด environment (เช่น sandbox แชท)
