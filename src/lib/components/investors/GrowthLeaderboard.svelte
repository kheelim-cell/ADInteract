<script lang="ts">
  import type { GrowthRow } from '$lib/db/investor_queries';
  import { base } from '$app/paths';
  import { m } from '$lib/paraglide/messages.js';

  let {
    title,
    subtitle,
    rows,
    loading,
    valueLabel,
    linkPrefix,
  }: {
    title: string;
    subtitle: string;
    rows: GrowthRow[];
    loading: boolean;
    valueLabel: string;          // e.g. '/sqft' or '/yr'
    linkPrefix: 'area' | 'project';
  } = $props();

  const rankStyle = [
    'text-amber-500 font-black',
    'text-gray-400 font-bold',
    'text-orange-400 font-bold',
    'text-gray-300 font-semibold',
    'text-gray-300 font-semibold',
  ];

  function fmtValue(v: number): string {
    if (v >= 1_000_000) return `AED ${(v / 1_000_000).toFixed(2)}M`;
    return `AED ${Math.round(v).toLocaleString()}`;
  }

  function fmtYoY(pct: number): string {
    return (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%';
  }

  let maxPct = $derived(Math.max(...rows.map(r => Math.abs(r.yoyPct)), 1));
</script>

<div class="rounded-2xl bg-white shadow-sm ring-1 ring-black/5 overflow-hidden flex flex-col h-full">

  <!-- Card header -->
  <div class="px-5 py-4 border-b border-gray-100">
    <h3 class="text-sm font-bold text-navy leading-snug">{title}</h3>
    <p class="text-xs text-gray-400 mt-0.5">{subtitle}</p>
  </div>

  <!-- Loading skeleton -->
  {#if loading}
    <div class="divide-y divide-gray-50 flex-1">
      {#each Array(5) as _}
        <div class="px-5 py-4 flex items-center gap-3 animate-pulse">
          <div class="h-3.5 w-4 rounded bg-gray-100 flex-shrink-0"></div>
          <div class="flex-1 space-y-2">
            <div class="h-3.5 w-40 rounded bg-gray-100"></div>
            <div class="h-2.5 w-28 rounded bg-gray-100"></div>
          </div>
          <div class="h-6 w-14 rounded-full bg-gray-100 flex-shrink-0"></div>
        </div>
      {/each}
    </div>

  <!-- Empty state -->
  {:else if rows.length === 0}
    <div class="flex-1 flex items-center justify-center py-12">
      <p class="text-sm text-gray-400 text-center px-6">{m.growth_leaderboard_not_enough_data()}</p>
    </div>

  <!-- Leaderboard rows -->
  {:else}
    <div class="divide-y divide-gray-50 flex-1">
      {#each rows as row, i}
        {@const barWidth = Math.round((Math.abs(row.yoyPct) / maxPct) * 100)}
        {@const isPositive = row.yoyPct >= 0}
        <div class="px-5 py-3.5">

          <!-- Top line: rank + name + YoY badge -->
          <div class="flex items-center gap-2.5">
            <span class="text-xs w-5 flex-shrink-0 text-end {rankStyle[i]}">{i + 1}</span>
            <div class="flex-1 min-w-0">
              <a
                href="{base}/{linkPrefix}/{encodeURIComponent(row.name)}"
                class="text-sm font-semibold text-gray-900 hover:text-brand-600 truncate block leading-snug transition-colors"
              >
                {row.name}
              </a>
              {#if row.district && row.district !== row.name}
                <p class="text-[11px] text-gray-400 truncate mt-0.5">{row.district}</p>
              {/if}
            </div>
            <span class="flex-shrink-0 inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold tabular-nums
              {isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}">
              {fmtYoY(row.yoyPct)}
            </span>
          </div>

          <!-- Growth bar + value comparison -->
          <div class="mt-2.5 ps-7">
            <div class="h-1 w-full rounded-full bg-gray-100 overflow-hidden mb-1.5">
              <div
                class="h-full rounded-full {isPositive ? 'bg-emerald-400' : 'bg-red-400'}"
                style="width: {barWidth}%"
              ></div>
            </div>
            <p class="text-[11px] text-gray-500 leading-none">
              <span class="font-semibold text-gray-800">{fmtValue(row.currentValue)}</span>
              <span class="text-gray-300 mx-1">{valueLabel}</span>
              <span class="text-gray-400">← {fmtValue(row.prevValue)}</span>
            </p>
          </div>

        </div>
      {/each}
    </div>
  {/if}

</div>
