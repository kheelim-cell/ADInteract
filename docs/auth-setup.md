# ADInteract — Auth Setup Guide

Complete setup: Supabase (Google OAuth + database) + Twilio (WhatsApp OTP) + GitHub Actions secrets.

---

## Part 1 — Supabase

### 1.1 Create a Supabase project

1. Go to https://supabase.com → **Start your project** → sign up with GitHub
2. Click **New project**
   - Name: `ADInteract`
   - Database password: generate a strong one — save it somewhere safe
   - Region: **Middle East (Bahrain)** — closest to your users
3. Wait ~2 minutes for the project to provision

### 1.2 Get your API keys

1. In your Supabase project: **Project Settings** → **API**
2. Copy:
   - **Project URL** → this is `VITE_SUPABASE_URL`
   - **anon / public** key → this is `VITE_SUPABASE_ANON_KEY`
   - **service_role / secret** key → used by Edge Functions (never expose in frontend)

### 1.3 Run the database migrations

1. In Supabase: **SQL Editor** → **New query**
2. Paste the entire contents of `supabase/migrations/20240101000000_auth_tables.sql`
3. Click **Run**

You should see two new tables in **Table Editor**: `profiles` and `whatsapp_otps`.

### 1.4 Configure Google OAuth

**In Google Cloud Console** (https://console.cloud.google.com):

1. Create a new project (or use an existing one)
2. **APIs & Services** → **OAuth consent screen**
   - User type: **External**
   - App name: `ADInteract`
   - User support email: your email
   - Developer contact email: your email
   - Save → **Publish app** (so external users can sign in)
3. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Name: `ADInteract`
   - Authorized redirect URIs — add exactly:
     ```
     https://<your-project-ref>.supabase.co/auth/v1/callback
     ```
     (Replace `<your-project-ref>` with your Supabase project reference, visible in the URL)
4. Copy the **Client ID** and **Client Secret**

**Back in Supabase**:

1. **Authentication** → **Providers** → **Google** → enable it
2. Paste in the **Client ID** and **Client Secret**
3. Save

### 1.5 Configure Site URL (for OAuth redirect)

1. Supabase → **Authentication** → **URL Configuration**
2. **Site URL**: `https://<your-github-username>.github.io/ADInteract`
3. **Redirect URLs** — add:
   ```
   https://<your-github-username>.github.io/ADInteract/
   https://<your-github-username>.github.io/ADInteract
   http://localhost:5173/
   http://localhost:5173
   ```
4. Save

---

## Part 2 — Twilio (WhatsApp OTP)

### 2.1 Create a Twilio account

1. Go to https://www.twilio.com → **Sign up** (free trial works)
2. Verify your phone number during signup
3. On the dashboard, find and copy:
   - **Account SID** → this is `TWILIO_ACCOUNT_SID`
   - **Auth Token** → this is `TWILIO_AUTH_TOKEN`

### 2.2 Activate the WhatsApp Sandbox (for testing)

The sandbox lets you test immediately without a business approval wait.

1. Twilio Console → **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Follow the on-screen steps:
   - You'll get a sandbox number (e.g. `+14155238886`)
   - Send a WhatsApp message from your phone to that number: `join <your-sandbox-code>`
   - Your phone is now connected to the sandbox
3. The sandbox number is your `TWILIO_WHATSAPP_FROM` value: `whatsapp:+14155238886`

> **For production**: apply for a WhatsApp Business number via Twilio. Takes 1-7 days for Meta approval. Once approved, replace the sandbox number with your approved number in the `TWILIO_WHATSAPP_FROM` secret.

---

## Part 3 — Install the Supabase JS package

In your project directory:

```bash
npm install @supabase/supabase-js
```

---

## Part 4 — Deploy Edge Functions

### 4.1 Install the Supabase CLI

```bash
# macOS / Linux
brew install supabase/tap/supabase

# Windows (PowerShell — run as admin)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

Or download the binary from: https://github.com/supabase/cli/releases

### 4.2 Log in and link your project

```bash
supabase login
# Opens browser → authorize

supabase link --project-ref <your-project-ref>
# Your project ref is the subdomain of your Supabase URL
# e.g. if URL is https://abcdefghij.supabase.co, ref is abcdefghij
```

### 4.3 Set Edge Function secrets

```bash
supabase secrets set \
  TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
```

> `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are injected automatically — you do NOT need to set these.

### 4.4 Deploy the Edge Functions

```bash
supabase functions deploy send-whatsapp-otp
supabase functions deploy verify-whatsapp-otp
```

Confirm in Supabase dashboard → **Edge Functions** — both should appear as `Active`.

---

## Part 5 — GitHub Actions Secrets

So the CI/CD build can inject the Supabase keys at build time:

1. GitHub → your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Add two secrets:

| Secret name | Value |
|-------------|-------|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anon/public key |

The workflows (`deploy.yml` and `data-refresh.yml`) already reference these secrets — no further changes needed.

---

## Part 6 — Local Development

Create a `.env.local` file in the project root (this file is gitignored):

```env
VITE_SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Then run:

```bash
npm run dev
```

Sign in with Google will redirect to `http://localhost:5173/` (already added to Supabase redirect URLs above).

For WhatsApp OTP locally, the Edge Functions run on Supabase's servers — calls go directly to `<your-project>.supabase.co/functions/v1/...` and work regardless of where the frontend is running.

---

## Verification Checklist

- [ ] `profiles` and `whatsapp_otps` tables visible in Supabase Table Editor
- [ ] Google provider enabled in Supabase Authentication → Providers
- [ ] Site URL and redirect URLs saved in Supabase Authentication → URL Configuration
- [ ] `send-whatsapp-otp` and `verify-whatsapp-otp` functions Active in Supabase Edge Functions
- [ ] Twilio secrets set (`supabase secrets list` confirms them)
- [ ] `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` added to GitHub repo secrets
- [ ] `npm install @supabase/supabase-js` run locally
- [ ] `.env.local` created with your project URL and anon key
- [ ] Local `npm run dev` shows Sign In button in header
- [ ] Google sign-in flow completes and header shows user avatar
- [ ] WhatsApp OTP flow: enter phone → receive WhatsApp message → enter OTP → signed in
- [ ] Signed-in state: stats, charts, and table all fully visible
- [ ] Signed-out state: stats + charts blurred with "Sign In to view" overlay, table visible
