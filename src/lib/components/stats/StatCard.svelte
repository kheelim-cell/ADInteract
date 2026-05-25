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

<div class="stat-card flex flex-col gap-3">
  <!-- Label -->
  <span class="text-[11px] font-semibold uppercase tracking-widest text-navy/40">{label}</span>

  <!-- Value -->
  <p class="text-3xl font-bold text-navy leading-none">{value}</p>

  <!-- Growth badge -->
  {#if !isNeutral && growth !== null}
    <span class="inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold
                 {isPositive ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : 'bg-red-50 text-red-700 ring-1 ring-red-200'}">
      {#if isPositive}
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
        </svg>
      {:else}
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25" />
        </svg>
      {/if}
      {formatPercent(growth)} vs prior period
    </span>
  {:else}
    <span class="text-xs text-navy/30 font-medium">No comparison data</span>
  {/if}
</div>
