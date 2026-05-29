<script lang="ts">
  import { onMount } from 'svelte';
  import { isAuthenticated, isPro, openSignIn } from '$lib/stores/auth';
  import { base } from '$app/paths';

  // Auto-open sign-in modal if user lands here not yet signed in
  onMount(() => {
    if (!$isAuthenticated) {
      setTimeout(openSignIn, 400); // brief delay so the page renders first
    }
  });
</script>

<svelte:head>
  <title>Activate Pro Access — ADInteract</title>
  <meta name="description" content="Activate your ADInteract Pro subscription." />
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="max-w-lg mx-auto px-4 py-20 text-center">

  {#if $isPro}
    <!-- ── Already pro — you're good to go ──────────────────────────────────── -->
    <div class="rounded-2xl bg-emerald-50 border border-emerald-200 p-8">
      <div class="mx-auto h-16 w-16 rounded-full bg-emerald-100 flex items-center justify-center mb-5">
        <svg class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-emerald-900 mb-2">You're All Set!</h1>
      <p class="text-sm text-emerald-700 mb-6">
        Your ADInteract Pro access is active. You can now view all investor intelligence data including growth leaderboards, rental yields, and service charge benchmarks.
      </p>
      <a
        href="{base}/investors"
        class="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
      >
        Go to Investor Intelligence
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
        </svg>
      </a>
    </div>

  {:else if $isAuthenticated}
    <!-- ── Signed in, pending manual activation ──────────────────────────────── -->
    <div class="rounded-2xl bg-amber-50 border border-amber-200 p-8">
      <div class="mx-auto h-16 w-16 rounded-full bg-amber-100 flex items-center justify-center mb-5">
        <svg class="h-8 w-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-amber-900 mb-2">Purchase Received!</h1>
      <p class="text-sm text-amber-700 mb-4">
        Thank you for subscribing to ADInteract Pro. Your access will be activated shortly — typically within a few hours during business hours.
      </p>
      <p class="text-xs text-amber-600 mb-6">
        Make sure you're signed in with the same Google account email you used during checkout. Once activated, refresh this page and you'll be taken straight to the Investor Intelligence dashboard.
      </p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          type="button"
          onclick={() => window.location.reload()}
          class="inline-flex items-center justify-center gap-2 rounded-full border border-amber-300 bg-white px-5 py-2.5 text-sm font-semibold text-amber-700 hover:bg-amber-50 transition-colors"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Check activation status
        </button>
        <a
          href="{base}/"
          class="inline-flex items-center justify-center gap-2 rounded-full bg-amber-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-amber-600 transition-colors"
        >
          Browse free data
        </a>
      </div>
    </div>

  {:else}
    <!-- ── Not signed in ──────────────────────────────────────────────────────── -->
    <div class="rounded-2xl bg-white border border-gray-200 p-8 shadow-sm">
      <div class="mx-auto h-16 w-16 rounded-full bg-brand-50 flex items-center justify-center mb-5">
        <svg class="h-8 w-8 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Activate Your Pro Access</h1>
      <p class="text-sm text-gray-500 mb-6">
        Sign in with the Google account you used for your purchase to activate your ADInteract Pro subscription.
      </p>
      <button
        type="button"
        onclick={openSignIn}
        class="inline-flex items-center gap-2 rounded-full bg-brand-500 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-600 transition-colors"
      >
        <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
        </svg>
        Sign In to Activate
      </button>
    </div>
  {/if}

</div>
