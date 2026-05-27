<script lang="ts">
  import { signInWithGoogle, closeSignIn } from '$lib/stores/auth';
  import { supabase, supabaseEnabled } from '$lib/supabase';

  type View = 'main' | 'whatsapp-phone' | 'whatsapp-otp';

  let view     = $state<View>('main');
  let phone    = $state('');
  let otp      = $state('');
  let loading  = $state(false);
  let errorMsg = $state('');
  let resendCountdown = $state(0);

  // ── Google ────────────────────────────────────────────────────────
  async function handleGoogle() {
    loading = true;
    errorMsg = '';
    try {
      await signInWithGoogle();
      // Page will redirect — no further action needed
    } catch (e) {
      errorMsg = e instanceof Error ? e.message : 'Google sign-in failed';
      loading = false;
    }
  }

  // ── WhatsApp: send OTP ────────────────────────────────────────────
  async function sendOTP() {
    const normalized = phone.trim().replace(/\s+/g, '');
    if (!normalized) { errorMsg = 'Please enter your WhatsApp number'; return; }

    loading = true;
    errorMsg = '';
    try {
      const res = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/send-whatsapp-otp`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`
          },
          body: JSON.stringify({ phone: normalized.startsWith('+') ? normalized : `+${normalized}` })
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to send OTP');

      view = 'whatsapp-otp';
      startCountdown();
    } catch (e) {
      errorMsg = e instanceof Error ? e.message : 'Failed to send OTP';
    } finally {
      loading = false;
    }
  }

  // ── WhatsApp: verify OTP ──────────────────────────────────────────
  async function verifyOTP() {
    if (otp.length < 6) { errorMsg = 'Enter the 6-digit code'; return; }
    if (!supabase) { errorMsg = 'Auth not configured'; return; }

    loading = true;
    errorMsg = '';
    try {
      const normalized = phone.trim().replace(/\s+/g, '');
      const res = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/verify-whatsapp-otp`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`
          },
          body: JSON.stringify({
            phone: normalized.startsWith('+') ? normalized : `+${normalized}`,
            otp: otp.trim()
          })
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Invalid OTP');

      // Exchange the hashed token returned by the Edge Function for a real session
      const { error: sessionError } = await supabase.auth.verifyOtp({
        token_hash: data.hashed_token,
        type:       'email'
      });
      if (sessionError) throw sessionError;
      // onAuthStateChange in auth.ts will call closeSignIn()
    } catch (e) {
      errorMsg = e instanceof Error ? e.message : 'Invalid OTP';
      loading = false;
    }
  }

  // ── Countdown for resend ──────────────────────────────────────────
  function startCountdown() {
    resendCountdown = 60;
    const t = setInterval(() => {
      resendCountdown--;
      if (resendCountdown <= 0) clearInterval(t);
    }, 1000);
  }

  function goBack() {
    view     = view === 'whatsapp-otp' ? 'whatsapp-phone' : 'main';
    errorMsg = '';
    otp      = '';
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) closeSignIn();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') closeSignIn();
  }
</script>

<!-- Backdrop -->
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
  onclick={handleBackdropClick}
  onkeydown={handleKeydown}
  role="dialog"
  aria-modal="true"
  aria-label="Sign in"
>
  <div
    class="relative w-full max-w-sm bg-white rounded-2xl shadow-2xl overflow-hidden"
    onclick={(e) => e.stopPropagation()}
  >
    <!-- Close -->
    <button
      type="button"
      onclick={closeSignIn}
      class="absolute top-3.5 right-3.5 z-10 flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
      aria-label="Close"
    >
      <svg class="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- ── Main view ───────────────────────────────────────────── -->
    {#if view === 'main'}
      <div class="px-8 py-10 pt-12">
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#1e4d3a]/10 mb-3">
            <svg class="h-6 w-6 text-[#1e4d3a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <h2 class="text-xl font-bold text-gray-900">Sign in to ADInteract</h2>
          <p class="text-sm text-gray-500 mt-1">Unlock full analytics & market insights</p>
        </div>

        {#if errorMsg}
          <p class="mb-4 text-sm text-red-600 text-center bg-red-50 rounded-lg px-3 py-2">{errorMsg}</p>
        {/if}

        <!-- Google -->
        <button
          type="button"
          onclick={handleGoogle}
          disabled={loading}
          class="w-full flex items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors mb-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg class="h-5 w-5 flex-shrink-0" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <!-- WhatsApp -->
        <button
          type="button"
          onclick={() => { view = 'whatsapp-phone'; errorMsg = ''; }}
          disabled={loading}
          class="w-full flex items-center justify-center gap-3 rounded-xl bg-[#25D366] px-4 py-3 text-sm font-semibold text-white hover:bg-[#1ebe5d] transition-colors mb-7 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg class="h-5 w-5 flex-shrink-0" viewBox="0 0 24 24" fill="white">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
          </svg>
          Continue with WhatsApp
        </button>

        <p class="text-xs text-gray-400 text-center">
          By signing in you agree to our
          <span class="underline cursor-pointer">terms of use</span>
        </p>
      </div>

    <!-- ── WhatsApp phone view ──────────────────────────────────── -->
    {:else if view === 'whatsapp-phone'}
      <div class="px-8 py-10 pt-12">
        <button type="button" onclick={goBack} class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back
        </button>

        <h2 class="text-xl font-bold text-gray-900 mb-1">WhatsApp</h2>
        <p class="text-sm text-gray-500 mb-5">Enter your number with country code. We'll send a verification code.</p>

        {#if errorMsg}
          <p class="mb-4 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{errorMsg}</p>
        {/if}

        <div class="mb-5">
          <div class="flex items-center rounded-xl border border-gray-200 focus-within:border-[#25D366] focus-within:ring-2 focus-within:ring-[#25D366]/20 transition-colors overflow-hidden">
            <span class="pl-4 pr-1 text-sm text-gray-500 select-none">+</span>
            <input
              type="tel"
              bind:value={phone}
              placeholder="971XXXXXXXXX"
              class="flex-1 pr-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none bg-transparent"
              onkeydown={(e) => e.key === 'Enter' && sendOTP()}
            />
          </div>
          <p class="mt-1.5 text-xs text-gray-400">UAE example: 971501234567 — include country code, no spaces</p>
        </div>

        <button
          type="button"
          onclick={sendOTP}
          disabled={loading || !phone.trim()}
          class="w-full rounded-xl bg-[#25D366] py-3 text-sm font-semibold text-white hover:bg-[#1ebe5d] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Sending…' : 'Send OTP'}
        </button>
      </div>

    <!-- ── WhatsApp OTP view ───────────────────────────────────── -->
    {:else if view === 'whatsapp-otp'}
      <div class="px-8 py-10 pt-12">
        <button type="button" onclick={goBack} class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back
        </button>

        <h2 class="text-xl font-bold text-gray-900 mb-1">Enter OTP</h2>
        <p class="text-sm text-gray-500 mb-5">
          Check WhatsApp at <strong class="text-gray-700">+{phone.replace(/^\+/, '')}</strong> for the 6-digit code.
        </p>

        {#if errorMsg}
          <p class="mb-4 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{errorMsg}</p>
        {/if}

        <div class="mb-5">
          <input
            type="text"
            inputmode="numeric"
            pattern="[0-9]*"
            maxlength="6"
            bind:value={otp}
            placeholder="_ _ _ _ _ _"
            class="w-full rounded-xl border border-gray-200 px-4 py-3.5 text-center text-2xl font-bold tracking-[0.5em] text-gray-900 placeholder-gray-300
                   focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20 transition-colors"
            onkeydown={(e) => e.key === 'Enter' && verifyOTP()}
          />
        </div>

        <button
          type="button"
          onclick={verifyOTP}
          disabled={loading || otp.length < 6}
          class="w-full rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mb-4"
        >
          {#if loading}
            <svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Verifying…
          {:else}
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
            Login
          {/if}
        </button>

        <div class="text-center">
          {#if resendCountdown > 0}
            <p class="text-xs text-gray-400">You can resend OTP in {resendCountdown}s</p>
          {:else}
            <button
              type="button"
              onclick={sendOTP}
              disabled={loading}
              class="text-xs text-brand-600 hover:text-brand-700 font-medium underline-offset-2 hover:underline disabled:opacity-50"
            >
              Resend OTP
            </button>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
