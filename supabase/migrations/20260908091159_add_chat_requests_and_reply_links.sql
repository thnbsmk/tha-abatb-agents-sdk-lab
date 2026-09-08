-- Matches Supabase LAB jwnbaidkwubbfqfwmcan migration 20260908091159_add_chat_requests_and_reply_links

alter table public.messages
  add column reply_to_message_id uuid;

alter table public.messages
  add constraint messages_reply_role_check check (
    (role = 'user' and reply_to_message_id is null)
    or (role = 'assistant' and reply_to_message_id is not null)
  );

alter table public.messages
  add constraint messages_reply_fkey
    foreign key (reply_to_message_id, conversation_id, user_id)
    references public.messages (id, conversation_id, user_id)
    on delete restrict;

alter table public.messages
  add constraint messages_one_reply_per_user_message_key
    unique (conversation_id, reply_to_message_id);

create table public.chat_requests (
  conversation_id uuid not null,
  user_message_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  status text not null default 'in_progress'
    check (status in ('in_progress', 'completed', 'failed')),
  response_message_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (conversation_id, user_message_id),
  constraint chat_requests_conversation_owner_fkey
    foreign key (conversation_id, user_id)
    references public.conversations (id, user_id)
    on delete cascade,
  constraint chat_requests_user_message_fkey
    foreign key (user_message_id, conversation_id, user_id)
    references public.messages (id, conversation_id, user_id)
    on delete cascade,
  constraint chat_requests_response_message_fkey
    foreign key (response_message_id, conversation_id, user_id)
    references public.messages (id, conversation_id, user_id)
    on delete restrict,
  constraint chat_requests_completion_check check (
    (status in ('in_progress', 'failed') and response_message_id is null)
    or (status = 'completed' and response_message_id is not null)
  )
);

create index chat_requests_user_updated_idx
  on public.chat_requests (user_id, updated_at desc);

create trigger chat_requests_set_updated_at
before update on public.chat_requests
for each row execute function public.set_updated_at();

alter table public.chat_requests enable row level security;

create policy "Users manage only their own chat requests"
on public.chat_requests
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

revoke all on table public.chat_requests from anon;
grant select, insert, update, delete on table public.chat_requests to authenticated;
