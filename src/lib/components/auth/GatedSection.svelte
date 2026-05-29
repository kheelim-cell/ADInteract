<script lang="ts">
  import { setContext } from 'svelte';
  import { isAuthenticated, isPro, openSignIn } from '$lib/stores/auth';
  import { supabaseEnabled, investorProGated, stanStoreUrl } from '$lib/supabase';

  let {
    children,
    /**
     * proOnly=true  → Investor-page mode.
     *   • VITE_INVESTOR_PRO_GATED=true  → requires active Pro subscription (is_pro = true).
     *   • VITE_INVESTOR_PRO_GATED=false → fully open — no gate at all (promo/launch mode).
     * proOnly=false (default) → standard mode: gate on sign-in (Sales, Rental pages).
     */
    proOnly = false
  }: { children: import('svelte').Snippet; proOnly?: boolean } = $props();

  // ── Lock logic ──────────────────────────────────────────────────────────────
  let locked = $derived(
    // Supabase not configured → never lock (dev/preview mode)
    !supabaseEnabled ? false
    // proOnly + pro gating toggled OFF → completely open (promotional mode)
    : proOnly && !investorProGated ? false
    // proOnly + pro gating ON → require isPro
    : proOnly && investorProGated ? !$isPro
    // Standard auth gate → require sign-in
    : !$isAuthenticated
  );

  // Show "Upgrade to Pro" when user is signed in but doesn't have pro
  let needsUpgrade = $derived(
    proOnly && investorProGated && supabaseEnabled && $isAuthenticated && !$isPro
  );

  // Share locked state with GatedBlur descendants
  setContext('gated-locked', { get: () => locked });
</script>

<div class="relative h-full">
  <!-- Content: block pointer events when locked -->
  <div class="h-full {locked ? 'pointer-events-none select-none' : ''}">
    {@render children()}
  </div>

  <!-- Light wash so blurred values lose contrast -->
  {#if locked}
    <div class="absolute inset-0 bg-white/15 z-[5]"></div>
  {/if}

  <!-- CTA overlay -->
  {#if locked}
    <div class="absolute inset-0 flex items-center justify-center z-10">
      {#if needsUpgrade}
        <!-- Upgrade to Pro CTA -->
        <a
          href={stanStoreUrl || '#'}
          target={stanStoreUrl ? '_blank' : undefined}
          rel="noopener noreferrer"
          class="inline-flex items-center gap-2 rounded-full bg-amber-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-amber-600 transition-colors"
        >
          <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
          </svg>
          Upgrade to Pro
        </a>
      {:else}
        <!-- Sign-in CTA -->
        <button
          type="button"
          onclick={openSignIn}
          class="inline-flex items-center gap-2 rounded-full bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-brand-600 transition-colors"
        >
          <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
          Sign In to view
        </button>
      {/if}
    </div>
  {/if}
</div>
