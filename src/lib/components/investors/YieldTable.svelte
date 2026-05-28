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

  // Copy community + district to clipboard
  let copiedKey = $state('');
  async function copyLabel(community: string, district: string) {
    const text = `${community}, ${district}`;
    try {
      await navigator.clipboard.writeText(text);
      copiedKey = text;
      setTimeout(() => { copiedKey = ''; }, 2000);
    } catch { /* clipboard unavailable */ }
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
          <th class="px-5 py-3 w-10"></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">

        {#if loading}
          {#each Array(8) as _}
            <tr class="animate-pulse">
              {#each Array(9) as _}
                <td class="px-5 py-3.5"><div class="h-3.5 rounded bg-gray-100 w-20"></div></td>
              {/each}
            </tr>
          {/each}

        {:else if rows.length === 0}
          <tr>
            <td colspan="9" class="px-5 py-16 text-center text-sm text-gray-400">
              No communities found with both sales and rental benchmark data.
            </td>
          </tr>

        {:else}
          {#each rows as row, i}
            {@const key = row.community + ', ' + row.district}
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
                  title="Search Google to find the exact location of this community"
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
              <td class="px-3 py-3.5">
                <button
                  type="button"
                  onclick={() => copyLabel(row.community, row.district)}
                  title="Copy community + district"
                  class="inline-flex items-center justify-center rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                >
                  {#if copiedKey === key}
                    <svg class="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  {:else}
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                    </svg>
                  {/if}
                </button>
              </td>
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
                  title="Search Google to find the exact location of this community"
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
