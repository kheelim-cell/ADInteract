-- Broker vanity pages: self-signup via Manychat → form → live /b/[slug] page
-- Brokers DM "BUILD" on Instagram → receive adinteract.co/b/signup → fill form → live immediately

create table if not exists public.brokers (
  id           uuid         default gen_random_uuid() primary key,
  slug         text         unique not null,
  display_name text         not null,
  agency       text,
  bio          text,
  email        text         not null,
  photo_url    text,
  districts    text[]       default '{}',
  visit_count  integer      default 0,
  active       boolean      default true,
  created_at   timestamptz  default now()
);

alter table public.brokers enable row level security;

-- Brokers can self-register (anon INSERT)
do $$ begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'brokers' and policyname = 'anon_can_register'
  ) then
    create policy "anon_can_register" on public.brokers
      for insert to anon, authenticated
      with check (true);
  end if;
end $$;

-- Anyone can read active broker pages
do $$ begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'brokers' and policyname = 'anon_can_read_active'
  ) then
    create policy "anon_can_read_active" on public.brokers
      for select to anon, authenticated
      using (active = true);
  end if;
end $$;

-- Security-definer RPC so anon can increment visit_count without needing UPDATE policy
create or replace function public.increment_broker_visit(broker_slug text)
returns void language plpgsql security definer as $$
begin
  update public.brokers
  set visit_count = visit_count + 1
  where slug = broker_slug and active = true;
end;
$$;

-- Storage bucket for broker headshots (public reads)
insert into storage.buckets (id, name, public)
values ('broker-photos', 'broker-photos', true)
on conflict (id) do nothing;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'storage' and tablename = 'objects' and policyname = 'broker_photos_insert'
  ) then
    create policy "broker_photos_insert" on storage.objects
      for insert to anon, authenticated
      with check (bucket_id = 'broker-photos');
  end if;
end $$;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'storage' and tablename = 'objects' and policyname = 'broker_photos_select'
  ) then
    create policy "broker_photos_select" on storage.objects
      for select to anon, authenticated
      using (bucket_id = 'broker-photos');
  end if;
end $$;
