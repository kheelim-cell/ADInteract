-- ──────────────────────────────────────────────────────────────────────────────
-- ADInteract Auth Tables
-- Run this in: Supabase dashboard → SQL Editor → New query → Run
-- ──────────────────────────────────────────────────────────────────────────────

-- 1. profiles — one row per user (Google OAuth or WhatsApp)
create table if not exists public.profiles (
  id              uuid        primary key references auth.users(id) on delete cascade,
  email           text,
  whatsapp_number text,
  full_name       text,
  avatar_url      text,
  auth_method     text        not null default 'google',   -- 'google' | 'whatsapp'
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- Index for fast WhatsApp number lookups
create unique index if not exists profiles_whatsapp_number_idx
  on public.profiles (whatsapp_number)
  where whatsapp_number is not null;

-- Auto-update updated_at
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.handle_updated_at();

-- RLS: users can only read/update their own profile
alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Service role can do everything (needed by Edge Functions)
create policy "Service role full access on profiles"
  on public.profiles for all
  using (auth.role() = 'service_role');


-- 2. whatsapp_otps — transient OTP store (auto-purged after use/expiry)
create table if not exists public.whatsapp_otps (
  id           uuid        primary key default gen_random_uuid(),
  phone_number text        not null,
  otp_code     text        not null,
  expires_at   timestamptz not null,
  used         boolean     not null default false,
  created_at   timestamptz not null default now()
);

-- Indexes for the queries made by Edge Functions
create index if not exists whatsapp_otps_phone_idx
  on public.whatsapp_otps (phone_number, used, created_at desc);

create index if not exists whatsapp_otps_lookup_idx
  on public.whatsapp_otps (phone_number, otp_code, used, expires_at);

-- RLS: no direct client access — only Edge Functions (service_role) touch this table
alter table public.whatsapp_otps enable row level security;

create policy "Service role full access on whatsapp_otps"
  on public.whatsapp_otps for all
  using (auth.role() = 'service_role');

-- Optional: auto-delete expired OTPs older than 1 day (keep table tidy)
-- Enable via: Supabase dashboard → Database → Extensions → pg_cron
-- select cron.schedule('delete-expired-otps', '0 * * * *',
--   $$delete from public.whatsapp_otps where expires_at < now() - interval '1 day'$$);
