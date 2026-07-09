<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';

  let { price }: { price: number | null } = $props();

  const THRESHOLD = 2_000_000;
</script>

{#if price == null}
  <span class="inline-flex items-center gap-1.5 rounded-full bg-gray-100 text-gray-400 px-3 py-1 text-xs font-semibold">
    {m.visa_badge_enter_price()}
  </span>
{:else if price >= THRESHOLD}
  <span class="inline-flex items-center gap-1.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 px-3 py-1 text-xs font-semibold">
    <svg class="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
    {m.visa_badge_qualifies()}
  </span>
{:else}
  <span class="inline-flex items-center gap-1.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200 px-3 py-1 text-xs font-semibold">
    <svg class="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
    {m.visa_badge_not_qualifies()}
  </span>
{/if}
