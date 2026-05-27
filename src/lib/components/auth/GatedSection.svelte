<script lang="ts">
  import { isAuthenticated, openSignIn } from '$lib/stores/auth';
  import { supabaseEnabled } from '$lib/supabase';

  let { children }: { children: import('svelte').Snippet } = $props();

  // If Supabase is not configured, never gate — show everything
  let locked = $derived(supabaseEnabled && !$isAuthenticated);
</script>

<div class="relative">
  <!-- Blurred content layer -->
  <div class={locked ? 'blur-md pointer-events-none select-none' : ''}>
    {@render children()}
  </div>

  <!-- White wash overlay (makes blurred text truly unreadable) -->
  {#if locked}
    <div class="absolute inset-0 bg-white/50 z-[5] rounded-inherit"></div>
  {/if}

  <!-- Sign-in CTA (only when locked) -->
  {#if locked}
    <div class="absolute inset-0 flex items-center justify-center z-10">
      <button
        type="button"
        onclick={openSignIn}
        class="inline-flex items-center gap-2 rounded-full bg-[#1e4d3a] px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-[#174033] transition-colors"
      >
        <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
        </svg>
        Sign In to view
      </button>
    </div>
  {/if}
</div>
