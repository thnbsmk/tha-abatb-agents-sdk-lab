Investigate this reported issue in the **agents-sdk-lab** repository checked out at `/workspace/agensdk`.

## Issue #17: Chat API returns 500 when OpenAI credentials are missing

**Reporter:** @dev-user

### Description
When the server is started without `OPENAI_API_KEY`, sending a chat message returns a generic HTTP 500 instead of a clear configuration error.

### Reproduction steps
1. Start the app without `OPENAI_API_KEY` in `.env.local`.
2. Sign in and send a chat message.
3. Observe the API response from `POST /api/chat`.

### Expected behavior
The API should return a clear configuration error (for example HTTP 503) explaining that `OPENAI_API_KEY` is missing.

### Actual behavior
The client receives HTTP 500 with `{ "error": "Server environment is not configured" }`.

### Notes
- Repository: agents-sdk-lab (Next.js + Supabase + OpenAI Agents SDK)
- Relevant route: `src/app/api/chat/route.ts`

Please inspect the repository, trace the relevant code path, attempt focused reproduction with available commands, and return an investigation report with root cause, suggested fix, and a regression test idea. Do not modify source files.
