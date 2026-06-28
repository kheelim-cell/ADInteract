<script lang="ts">
  import { growthPercent, formatPercent } from '$lib/utils/format';
  import { filters } from '$lib/stores/filters';
  import { getContext } from 'svelte';
  import { m } from '$lib/paraglide/messages.js';

  const gatedCtx = getContext<{ get: () => boolean } | undefined>('gated-locked');
  let locked = $derived(gatedCtx?.get() ?? false);

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
  let isFlat = $derived(growth !== null && growth === 0);

  // Hide comparison for YTD (variable-length period) and custom ranges
  let showComparison = $derived(
    previousRaw > 0 &&
    $filters.dateRange !== 'ytd' &&
    $filters.dateRange !== 'custom'
  );

  const PRESET_PERIOD: Record<string, string> = {
    '1m':  '1M',
    '3m':  '3M',
    '6m':  '6M',
    '12m': '12M',
    '3y':  '3Y',
  };
  const PRESET_LABEL: Record<string, string> = Object.fromEntries(
    Object.entries(PRESET_PERIOD).map(([k, period]) => [k, m.stat_vs_last({ period })])
  );

  let comparisonLabel = $derived(
    showComparison ? (PRESET_LABEL[$filters.dateRange] ?? '') : ''
  );
</script>

<div class="stat-card flex flex-col gap-3">
  <!-- Label: always readable -->
  <span class="text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider sm:tracking-widest text-navy/40">{label}</span>

  <!-- Value -->
  <p class={`text-2xl sm:text-3xl font-bold text-navy leading-none${locked ? ' blur-[4px]' : ''}`}>{value}</p>

  <!-- Growth badge -->
  <div class={locked ? 'blur-[3px]' : ''}>
  {#if showComparison && growth !== null}
    {#if isFlat}
      <span class="inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-500 ring-1 ring-gray-200">
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
        </svg>
        {m.stat_flat_with_comparison({ comparison: comparisonLabel })}
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
        {m.stat_growth_with_comparison({ percent: formatPercent(growth), comparison: comparisonLabel })}
      </span>
    {/if}
  {:else if previousRaw > 0 && ($filters.dateRange === 'ytd' || $filters.dateRange === 'custom')}
    <!-- YTD / custom: show badge without comparison label -->
    <span class="inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold
                 {growth !== null && growth > 0 ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : growth !== null && growth < 0 ? 'bg-red-50 text-red-700 ring-1 ring-red-200' : 'bg-gray-50 text-gray-500 ring-1 ring-gray-200'}">
      {#if growth !== null && growth > 0}
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
        </svg>
      {:else if growth !== null && growth < 0}
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25" />
        </svg>
      {:else}
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
        </svg>
      {/if}
      {growth !== null ? formatPercent(growth) : '—'}
    </span>
  {:else}
    <span class="text-xs text-navy/30 font-medium">{m.stat_no_prior()}</span>
  {/if}
  </div><!-- end blurred growth wrapper -->
</div>
