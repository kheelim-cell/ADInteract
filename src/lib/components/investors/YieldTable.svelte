<script lang="ts">
  import type { YieldRow } from '$lib/db/investor_queries';
  import { base } from '$app/paths';

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
</script>

<div class="rounded-2xl bg-white shadow-sm ring-1 ring-black/5 overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-gray-100">
    <h3 class="text-sm font-bold text-navy">Gross Rental Yield by Community</h3>
    <p class="text-xs text-gray-400 mt-0.5">
      Median annual rent ÷ median sale price · Communities with ≥ 5 sales and rental benchmark data
    </p>
  </div>

  <!-- ─── Desktop table ──────────────────────────────────────────────────── -->
  <div class="hidden md:block overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-gray-50 border-b border-gray-100">
          <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">#</th>
          <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">District</th>
          <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Community ↗</th>
          <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Median Sale Price</th>
          <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Median Annual Rent</th>
          <th class="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 w-44">Gross Yield</th>
          <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400"># Sales</th>
          <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400"># Projects</th>
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
              No communities found with both sales and rental benchmark data.
            </td>
          </tr>

        {:else}
          {#each rows as row, i}
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
                  class="font-medium text-gray-900 hover:text-brand-600 hover:underline"
                >
                  {row.community}
                </a>
              </td>
              <td class="px-5 py-3.5 text-right text-gray-700 whitespace-nowrap tabular-nums">
                {fmtCurrency(row.medianSalePrice)}
              </td>
              <td class="px-5 py-3.5 text-right text-gray-700 whitespace-nowrap tabular-nums">
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
              <td class="px-5 py-3.5 text-right text-xs text-gray-500 tabular-nums">{row.saleCount.toLocaleString()}</td>
              <td class="px-5 py-3.5 text-right text-xs text-gray-500 tabular-nums">{row.projectCount}</td>
            </tr>
          {/each}
        {/if}

      </tbody>
    </table>
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
      <div class="px-4 py-12 text-center text-sm text-gray-400">No data available.</div>

    {:else}
      <div class="divide-y divide-gray-50">
        {#each rows as row, i}
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
                <p class="text-gray-400">Sale price</p>
                <p class="font-semibold text-gray-800 tabular-nums">{fmtCurrency(row.medianSalePrice)}</p>
              </div>
              <div>
                <p class="text-gray-400">Annual rent</p>
                <p class="font-semibold text-gray-800 tabular-nums">{fmtCurrency(row.medianAnnualRent)}</p>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

</div>
