create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  user_id uuid not null unique references auth.users (id) on delete cascade,
  username text,
  full_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_user_identity_check check (id = user_id)
);

create table public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint conversations_id_user_id_key unique (id, user_id)
);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  reply_to_message_id uuid,
  role text not null check (role in ('user', 'assistant')),
  content text not null check (length(btrim(content)) > 0),
  created_at timestamptz not null default now(),
  constraint messages_reply_role_check check (
    (role = 'user' and reply_to_message_id is null)
    or (role = 'assistant' and reply_to_message_id is not null)
  ),
  constraint messages_identity_owner_key
    unique (id, conversation_id, user_id),
  constraint messages_conversation_owner_fkey
    foreign key (conversation_id, user_id)
    references public.conversations (id, user_id)
    on delete cascade,
  constraint messages_reply_fkey
    foreign key (reply_to_message_id, conversation_id, user_id)
    references public.messages (id, conversation_id, user_id)
    on delete restrict,
  constraint messages_one_reply_per_user_message_key
    unique (conversation_id, reply_to_message_id)
);

create table public.chat_requests (
  conversation_id uuid not null,
  user_message_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  status text not null default 'in_progress'
    check (status in ('in_progress', 'completed')),
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
    (status = 'in_progress' and response_message_id is null)
    or (status = 'completed' and response_message_id is not null)
  )
);

create index conversations_user_updated_idx
  on public.conversations (user_id, updated_at desc);
create index messages_conversation_created_idx
  on public.messages (conversation_id, created_at);
create index messages_user_created_idx
  on public.messages (user_id, created_at desc);
create index chat_requests_user_updated_idx
  on public.chat_requests (user_id, updated_at desc);

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

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger conversations_set_updated_at
before update on public.conversations
for each row execute function public.set_updated_at();

create trigger chat_requests_set_updated_at
before update on public.chat_requests
for each row execute function public.set_updated_at();

create function public.touch_conversation_after_message()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  update public.conversations
  set updated_at = now()
  where id = new.conversation_id
    and user_id = new.user_id;
  return new;
end;
$$;

create trigger messages_touch_conversation
after insert on public.messages
for each row execute function public.touch_conversation_after_message();

create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, user_id, username, full_name, avatar_url)
  values (
    new.id,
    new.id,
    new.raw_user_meta_data ->> 'username',
    new.raw_user_meta_data ->> 'full_name',
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

insert into public.profiles (id, user_id, username, full_name, avatar_url)
select
  id,
  id,
  raw_user_meta_data ->> 'username',
  raw_user_meta_data ->> 'full_name',
  raw_user_meta_data ->> 'avatar_url'
from auth.users
on conflict (id) do nothing;

alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.chat_requests enable row level security;

create policy "Users manage only their own profile"
on public.profiles
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "Users manage only their own conversations"
on public.conversations
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "Users manage only their own messages"
on public.messages
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "Users manage only their own chat requests"
on public.chat_requests
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

revoke all on table public.profiles from anon;
revoke all on table public.conversations from anon;
revoke all on table public.messages from anon;
revoke all on table public.chat_requests from anon;

grant select, insert, update, delete on table public.profiles to authenticated;
grant select, insert, update, delete on table public.conversations to authenticated;
grant select, insert, update, delete on table public.messages to authenticated;
grant select, insert, update, delete on table public.chat_requests to authenticated;
