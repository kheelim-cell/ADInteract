<script lang="ts">
  import { signInWithGoogle, closeSignIn } from '$lib/stores/auth';

  const IDENTITY_OPTIONS = ['Broker', 'End User', 'Investor'] as const;
  type Identity = typeof IDENTITY_OPTIONS[number];

  let name      = $state('');
  let identity  = $state<Identity | ''>('');
  let whatsapp  = $state('');
  let loading   = $state(false);
  let errorMsg  = $state('');

  async function handleGoogle() {
    errorMsg = '';
    if (!name.trim()) { errorMsg = 'Please enter your name';     return; }
    if (!identity)    { errorMsg = 'Please select your role';    return; }

    loading = true;
    try {
      await signInWithGoogle({
        name:     name.trim(),
        identity: identity,
        whatsapp: whatsapp.trim()
      });
      // Google OAuth redirects the page — no further action needed here
    } catch (e) {
      errorMsg = e instanceof Error ? e.message : 'Google sign-in failed';
      loading  = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) closeSignIn();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') closeSignIn();
  }

  const inputClass = 'w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20 transition-colors bg-white';
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

    <div class="px-8 py-10 pt-12">

      <!-- Header -->
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

      <!-- Profile form -->
      <div class="space-y-3 mb-5">

        <!-- Name -->
        <div>
          <label for="auth-name" class="block text-xs font-semibold text-gray-600 mb-1.5">
            Name <span class="text-red-400">*</span>
          </label>
          <input
            id="auth-name"
            type="text"
            bind:value={name}
            placeholder="Your full name"
            class={inputClass}
            onkeydown={(e) => e.key === 'Enter' && handleGoogle()}
          />
        </div>

        <!-- Identity -->
        <div>
          <label for="auth-identity" class="block text-xs font-semibold text-gray-600 mb-1.5">
            I am a <span class="text-red-400">*</span>
          </label>
          <select
            id="auth-identity"
            bind:value={identity}
            class="{inputClass} appearance-none"
          >
            <option value="">Select your role…</option>
            {#each IDENTITY_OPTIONS as opt}
              <option value={opt}>{opt}</option>
            {/each}
          </select>
        </div>

        <!-- WhatsApp -->
        <div>
          <label for="auth-whatsapp" class="block text-xs font-semibold text-gray-600 mb-1.5">
            WhatsApp Number
          </label>
          <div class="flex items-center rounded-xl border border-gray-200 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-400/20 transition-colors overflow-hidden">
            <span class="pl-3.5 pr-1 text-sm text-gray-400 select-none">+</span>
            <input
              id="auth-whatsapp"
              type="tel"
              bind:value={whatsapp}
              placeholder="971501234567"
              class="flex-1 pr-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none bg-transparent"
            />
          </div>
          <p class="mt-1 text-xs text-gray-400">Include country code · e.g. 971501234567</p>
        </div>

      </div>

      <!-- Google sign-in button -->
      <button
        type="button"
        onclick={handleGoogle}
        disabled={loading}
        class="w-full flex items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors mb-4 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {#if loading}
          <svg class="h-4 w-4 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Redirecting…
        {:else}
          <svg class="h-5 w-5 flex-shrink-0" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        {/if}
      </button>

      <p class="text-xs text-gray-400 text-center">
        By signing in you agree to our
        <span class="underline cursor-pointer">terms of use</span>
      </p>

    </div>
  </div>
</div>
