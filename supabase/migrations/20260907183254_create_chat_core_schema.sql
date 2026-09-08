-- Matches Supabase LAB jwnbaidkwubbfqfwmcan migration 20260907183254_create_chat_core_schema

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text,
  model_label text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint conversations_id_user_id_key unique (id, user_id)
);

create index conversations_user_id_idx
  on public.conversations (user_id);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system', 'tool')),
  content text not null,
  metadata jsonb,
  created_at timestamptz not null default now(),
  constraint messages_conversation_owner_fkey
    foreign key (conversation_id, user_id)
    references public.conversations (id, user_id)
    on delete cascade,
  constraint messages_identity_owner_key
    unique (id, conversation_id, user_id)
);

create index messages_conversation_id_created_at_idx
  on public.messages (conversation_id, created_at);
create index messages_user_id_idx
  on public.messages (user_id);

create function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create policy profiles_select_own
on public.profiles
for select
to authenticated
using ((select auth.uid()) = id);

create policy profiles_insert_own
on public.profiles
for insert
to authenticated
with check ((select auth.uid()) = id);

create policy profiles_update_own
on public.profiles
for update
to authenticated
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

create policy conversations_select_own
on public.conversations
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy conversations_insert_own
on public.conversations
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy conversations_update_own
on public.conversations
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy conversations_delete_own
on public.conversations
for delete
to authenticated
using ((select auth.uid()) = user_id);

create policy messages_select_own
on public.messages
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy messages_insert_own
on public.messages
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy messages_update_own
on public.messages
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy messages_delete_own
on public.messages
for delete
to authenticated
using ((select auth.uid()) = user_id);

revoke all on table public.profiles from anon;
revoke all on table public.conversations from anon;
revoke all on table public.messages from anon;

grant select, insert, update, delete on table public.profiles to authenticated;
grant select, insert, update, delete on table public.conversations to authenticated;
grant select, insert, update, delete on table public.messages to authenticated;
