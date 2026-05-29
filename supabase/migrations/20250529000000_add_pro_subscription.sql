-- ──────────────────────────────────────────────────────────────────────────────
-- Pro Subscription — add is_pro to profiles + fix missing columns
-- Run in: Supabase dashboard → SQL Editor → New query → Run
-- ──────────────────────────────────────────────────────────────────────────────

-- 1. Add is_pro flag (false by default — no existing user gets free pro access)
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS is_pro BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Add identity column (role: Broker | Investor | End User) — referenced in auth.ts upsert
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS identity TEXT;

-- 3. Add last_login_at — referenced in auth.ts upsert
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- 4. Index for fast pro-user lookups (admin queries)
CREATE INDEX IF NOT EXISTS profiles_is_pro_idx
  ON public.profiles (is_pro)
  WHERE is_pro = TRUE;

-- ──────────────────────────────────────────────────────────────────────────────
-- Grant pro access to a user (run manually after Stan Store purchase):
--
--   UPDATE public.profiles
--   SET is_pro = TRUE, updated_at = NOW()
--   WHERE email = 'buyer@example.com';
--
-- Revoke pro access:
--
--   UPDATE public.profiles
--   SET is_pro = FALSE, updated_at = NOW()
--   WHERE email = 'buyer@example.com';
--
-- List all pro users:
--
--   SELECT id, email, full_name, is_pro, created_at
--   FROM public.profiles
--   WHERE is_pro = TRUE
--   ORDER BY updated_at DESC;
-- ──────────────────────────────────────────────────────────────────────────────
