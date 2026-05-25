<script lang="ts">
  import { growthPercent, formatPercent } from '$lib/utils/format';

  let {
    label,
    value,
    currentRaw = 0,
    previousRaw = 0,
    previousValue = null
  }: {
    label: string;
    value: string;
    currentRaw?: number;
    previousRaw?: number;
    previousValue?: number | null;
  } = $props();

  let growth = $derived(growthPercent(currentRaw, previousRaw));
  let isPositive = $derived(growth !== null && growth > 0);
  let isNegative = $derived(growth !== null && growth < 0);
  let isNeutral = $derived(growth === null || growth === 0);
</script>

<div class="stat-card flex flex-col items-center text-center py-6 px-4">
  <span class="inline-block px-4 py-1 rounded-full bg-gray-100 text-xs font-medium text-gray-500 mb-4">{label}</span>
  <p class="text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
  {#if !isNeutral && growth !== null}
    <span class="mt-3 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-sm font-semibold
                 {isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}">
      {#if isPositive}
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
        </svg>
      {:else}
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25" />
        </svg>
      {/if}
      {formatPercent(growth)}
    </span>
  {/if}
</div>
