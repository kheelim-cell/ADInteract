-- Email subscribers: add district/source attribution columns.
-- The base table already exists in production (created outside migrations),
-- so this is written to be safe on both fresh and existing databases.
create table if not exists public.email_subscribers (
  email      text primary key,
  created_at timestamptz not null default now()
);

alter table public.email_subscribers add column if not exists district text;
alter table public.email_subscribers add column if not exists source text;
alter table public.email_subscribers add column if not exists created_at timestamptz not null default now();

alter table public.email_subscribers enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'email_subscribers'
      and policyname = 'anon_can_subscribe'
  ) then
    create policy "anon_can_subscribe"
      on public.email_subscribers
      for insert
      to anon, authenticated
      with check (true);
  end if;
end $$;
