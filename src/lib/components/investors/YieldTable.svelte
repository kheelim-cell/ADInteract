<script lang="ts">
  import type { YieldRow } from '$lib/db/investor_queries';
  import { base } from '$app/paths';
  import { m } from '$lib/paraglide/messages.js';

  let {
    rows,
    loading,
  }: {
    rows: YieldRow[];
    loading: boolean;
  } = $props();

  function fmtCurrency(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    return `AED ${Math.round(n).toLocaleString()}`;
  }

  function googleSearchUrl(community: string, district: string): string {
    return `https://www.google.com/search?q=${encodeURIComponent(community + ' ' + district)}`;
  }

  // Colour-code gross yield
  function yieldBadge(pct: number): string {
    if (pct >= 8) return 'bg-emerald-100 text-emerald-800';
    if (pct >= 6) return 'bg-brand-50 text-brand-700';
    if (pct >= 4) return 'bg-amber-50 text-amber-700';
    return 'bg-gray-100 text-gray-600';
  }

  // Yield bar width (cap at 12% for visual scale)
  function yieldBar(pct: number): number {
    return Math.min(100, Math.round((pct / 12) * 100));
  }

  const INITIAL_LIMIT = 5;
  let expanded = $state(false);
  let visibleRows = $derived(expanded ? rows : rows.slice(0, INITIAL_LIMIT));
</script>

<div class="rounded-2xl bg-white shadow-sm ring-1 ring-black/5 overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-gray-100">
    <h3 class="text-sm font-bold text-navy">{m.yield_table_title()}</h3>
    <p class="text-xs text-gray-400 mt-0.5">
      {m.yield_table_subtitle()}
    </p>
  </div>

  <!-- ─── Desktop table ──────────────────────────────────────────────────── -->
  <div class="hidden md:block overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-gray-50 border-b border-gray-100">
          <th class="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wider text-gray-400">#</th>
          <th class="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_district()}</th>
          <th class="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_community()}</th>
          <th class="px-5 py-3 text-end text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_median_sale_price()}</th>
          <th class="px-5 py-3 text-end text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_median_annual_rent()}</th>
          <th class="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 w-44">{m.yield_table_th_gross_yield()}</th>
          <th class="px-5 py-3 text-end text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_sales()}</th>
          <th class="px-5 py-3 text-end text-xs font-semibold uppercase tracking-wider text-gray-400">{m.yield_table_th_projects()}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">

        {#if loading}
          {#each Array(8) as _}
            <tr class="animate-pulse">
              {#each Array(8) as _}
                <td class="px-5 py-3.5"><div class="h-3.5 rounded bg-gray-100 w-20"></div></td>
              {/each}
            </tr>
          {/each}

        {:else if rows.length === 0}
          <tr>
            <td colspan="8" class="px-5 py-16 text-center text-sm text-gray-400">
              {m.yield_table_no_data_desktop()}
            </td>
          </tr>

        {:else}
          {#each visibleRows as row, i}
            <tr class="hover:bg-gray-50/80 transition-colors">
              <td class="px-5 py-3.5 text-xs text-gray-400 tabular-nums">{i + 1}</td>
              <td class="px-5 py-3.5 whitespace-nowrap">
                <a
                  href="{base}/area/{encodeURIComponent(row.district)}"
                  class="text-brand-600 hover:text-brand-700 hover:underline text-sm"
                >
                  {row.district}
                </a>
              </td>
              <td class="px-5 py-3.5 whitespace-nowrap">
                <a
                  href={googleSearchUrl(row.community, row.district)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={m.yield_table_search_title()}
                  class="font-medium text-gray-900 hover:text-brand-600 hover:underline"
                >
                  {row.community}
                </a>
              </td>
              <td class="px-5 py-3.5 text-end text-gray-700 whitespace-nowrap tabular-nums">
                {fmtCurrency(row.medianSalePrice)}
              </td>
              <td class="px-5 py-3.5 text-end text-gray-700 whitespace-nowrap tabular-nums">
                {fmtCurrency(row.medianAnnualRent)}/yr
              </td>
              <td class="px-5 py-3.5">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                    <div
                      class="h-full rounded-full bg-brand-500"
                      style="width: {yieldBar(row.grossYieldPct)}%"
                    ></div>
                  </div>
                  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold flex-shrink-0 tabular-nums {yieldBadge(row.grossYieldPct)}">
                    {row.grossYieldPct.toFixed(1)}%
                  </span>
                </div>
              </td>
              <td class="px-5 py-3.5 text-end text-xs text-gray-500 tabular-nums">{row.saleCount.toLocaleString()}</td>
              <td class="px-5 py-3.5 text-end text-xs text-gray-500 tabular-nums">{row.projectCount}</td>
            </tr>
          {/each}
        {/if}

      </tbody>
    </table>

    {#if !loading && rows.length > INITIAL_LIMIT}
      <button
        type="button"
        onclick={() => (expanded = !expanded)}
        class="w-full py-3 border-t border-gray-100 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1.5"
      >
        {#if expanded}
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" /></svg>
          {m.yield_table_show_fewer()}
        {:else}
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
          {m.yield_table_show_all({ count: String(rows.length) })}
        {/if}
      </button>
    {/if}
  </div>

  <!-- ─── Mobile cards ──────────────────────────────────────────────────── -->
  <div class="block md:hidden">
    {#if loading}
      {#each Array(6) as _}
        <div class="px-4 py-4 border-b border-gray-50 animate-pulse space-y-2.5">
          <div class="flex justify-between">
            <div class="h-4 w-36 bg-gray-100 rounded"></div>
            <div class="h-6 w-16 bg-gray-100 rounded-full"></div>
          </div>
          <div class="h-3 w-24 bg-gray-100 rounded"></div>
          <div class="grid grid-cols-2 gap-3">
            <div class="h-8 bg-gray-100 rounded"></div>
            <div class="h-8 bg-gray-100 rounded"></div>
          </div>
        </div>
      {/each}

    {:else if rows.length === 0}
      <div class="px-4 py-12 text-center text-sm text-gray-400">{m.yield_table_no_data_mobile()}</div>

    {:else}
      <div class="divide-y divide-gray-50">
        {#each visibleRows as row, i}
          <div class="px-4 py-4">
            <!-- District + Community + yield -->
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-300 tabular-nums font-semibold">#{i + 1}</span>
                  <a
                    href="{base}/area/{encodeURIComponent(row.district)}"
                    class="text-sm font-semibold text-brand-600 hover:underline truncate"
                  >
                    {row.district}
                  </a>
                </div>
                <a
                  href={googleSearchUrl(row.community, row.district)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={m.yield_table_search_title()}
                  class="text-xs text-gray-500 hover:text-brand-600 hover:underline mt-0.5 block"
                >
                  {row.community} ↗
                </a>
              </div>
              <span class="flex-shrink-0 inline-flex items-center rounded-full px-3 py-1.5 text-sm font-bold tabular-nums {yieldBadge(row.grossYieldPct)}">
                {row.grossYieldPct.toFixed(1)}%
              </span>
            </div>

            <!-- Yield bar -->
            <div class="mt-2.5 h-1 rounded-full bg-gray-100 overflow-hidden">
              <div class="h-full rounded-full bg-brand-500" style="width: {yieldBar(row.grossYieldPct)}%"></div>
            </div>

            <!-- Sale price + rent -->
            <div class="mt-2.5 grid grid-cols-2 gap-x-4 text-xs">
              <div>
                <p class="text-gray-400">{m.yield_table_sale_price_label()}</p>
                <p class="font-semibold text-gray-800 tabular-nums">{fmtCurrency(row.medianSalePrice)}</p>
              </div>
              <div>
                <p class="text-gray-400">{m.yield_table_annual_rent_label()}</p>
                <p class="font-semibold text-gray-800 tabular-nums">{fmtCurrency(row.medianAnnualRent)}</p>
              </div>
            </div>
          </div>
        {/each}
      </div>

      {#if !loading && rows.length > INITIAL_LIMIT}
        <button
          type="button"
          onclick={() => (expanded = !expanded)}
          class="w-full py-3 border-t border-gray-100 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1.5"
        >
          {#if expanded}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" /></svg>
            {m.yield_table_show_fewer()}
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
            {m.yield_table_show_all({ count: String(rows.length) })}
          {/if}
        </button>
      {/if}
    {/if}
  </div>

</div>
