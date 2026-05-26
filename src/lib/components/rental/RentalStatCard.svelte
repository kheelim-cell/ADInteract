<script lang="ts">
  import { growthPercent, formatPercent } from '$lib/utils/format';

  let {
    label,
    value,
    sub             = '',
    currentRaw      = 0,
    previousRaw     = 0,
    comparisonLabel = ''
  }: {
    label: string;
    value: string;
    sub?: string;
    currentRaw?: number;
    previousRaw?: number;
    comparisonLabel?: string;
  } = $props();

  let growth     = $derived(growthPercent(currentRaw, previousRaw));
  let showBadge  = $derived(previousRaw > 0 && currentRaw > 0 && growth !== null);
  let isPositive = $derived(growth !== null && growth > 0);
  let isFlat     = $derived(growth !== null && growth === 0);
</script>

<div class="stat-card flex flex-col gap-3">
  <span class="text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider sm:tracking-widest text-navy/40">
    {label}
  </span>
  <p class="text-2xl sm:text-3xl font-bold text-navy leading-none">{value}</p>

  {#if showBadge}
    {#if isFlat}
      <span class="inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-500 ring-1 ring-gray-200">
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
        </svg>
        0.0%{comparisonLabel ? ` · ${comparisonLabel}` : ''}
      </span>
    {:else}
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
        {formatPercent(growth)}{comparisonLabel ? ` · ${comparisonLabel}` : ''}
      </span>
    {/if}
  {:else if sub}
    <span class="text-xs text-navy/40 font-medium">{sub}</span>
  {/if}
</div>
