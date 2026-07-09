<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';
  import { onMount } from 'svelte';
  import { query } from '$lib/db/duckdb';
  import { dbReady } from '$lib/stores/db';
  import VisaBadge from '$lib/components/investors/VisaBadge.svelte';
  import ShareToolButton from '$lib/components/ui/ShareToolButton.svelte';

  let priceInput = $state('');
  let price = $derived(priceInput ? parseFloat(priceInput.replace(/,/g, '')) : null);

  interface DistrictVisaRow { district: string; below: number; above: number; total: number; }

  let loading = $state(false);
  let districtRows = $state<DistrictVisaRow[]>([]);
  let totalBelow = $derived(districtRows.reduce((s, r) => s + r.below, 0));
  let totalAbove = $derived(districtRows.reduce((s, r) => s + r.above, 0));
  let grandTotal = $derived(totalBelow + totalAbove);

  async function loadData() {
    if (!$dbReady) return;
    loading = true;
    try {
      const now = new Date();
      const d365 = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 365).toISOString().slice(0, 10);
      const today = now.toISOString().slice(0, 10);
      const rows = await query<{ district: string; below: number; above: number; total: number }>(`
        SELECT district,
               SUM(CASE WHEN price_aed < 2000000 THEN 1 ELSE 0 END) AS below,
               SUM(CASE WHEN price_aed >= 2000000 THEN 1 ELSE 0 END) AS above,
               COUNT(*) AS total
        FROM transactions
        WHERE sale_date >= '${d365}' AND sale_date <= '${today}'
          AND price_aed > 0
          AND district IS NOT NULL AND district != ''
        GROUP BY district
        HAVING COUNT(*) >= 10
        ORDER BY above DESC
        LIMIT 20
      `);
      districtRows = rows.map(r => ({
        district: r.district,
        below: Number(r.below),
        above: Number(r.above),
        total: Number(r.total),
      }));
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if ($dbReady) loadData();
  });

  function fmt(n: number) { return n.toLocaleString('en-AE'); }
  function pct(part: number, total: number) { return total > 0 ? ((part / total) * 100).toFixed(0) + '%' : '—'; }
</script>

<svelte:head>
  <title>{m.seo_visa_title()}</title>
  <meta name="description" content={m.seo_visa_description()} />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="flex items-start justify-between gap-4 mb-6">
    <div>
      <h1 class="text-xl font-bold text-gray-900 mb-1">{m.visa_page_title()}</h1>
      <p class="text-sm text-gray-500">{m.visa_page_subtitle()}</p>
    </div>
    <div class="flex-shrink-0">
      <ShareToolButton />
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

    <!-- Left: calculator -->
    <div>
      <div class="rounded-2xl border border-gray-200 bg-white p-6">
        <label class="block text-sm font-semibold text-gray-700 mb-2">{m.visa_threshold_label()}</label>
        <input
          type="text"
          inputmode="numeric"
          bind:value={priceInput}
          placeholder={m.visa_threshold_placeholder()}
          class="w-full rounded-xl border border-gray-200 px-4 py-3 text-lg font-semibold focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />

        <div class="mt-4">
          <VisaBadge {price} />
        </div>

        {#if price != null && price >= 2_000_000}
          <div class="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4">
            <h3 class="text-sm font-bold text-amber-900 mb-2">{m.visa_conditions_title()}</h3>
            <ul class="space-y-1.5">
              {#each [m.visa_condition_1(), m.visa_condition_2(), m.visa_condition_3(), m.visa_condition_4()] as cond}
                <li class="flex items-start gap-2 text-xs text-amber-800">
                  <svg class="w-3.5 h-3.5 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {cond}
                </li>
              {/each}
            </ul>
          </div>
        {:else if price != null && price < 2_000_000}
          <div class="mt-4 rounded-xl bg-gray-50 border border-gray-200 p-4">
            <p class="text-xs text-gray-500">
              You need <span class="font-bold text-gray-800">AED {fmt(2_000_000 - price)}</span> more to reach the Golden Visa threshold.
            </p>
          </div>
        {/if}
      </div>

      <!-- About the visa -->
      <div class="mt-4 rounded-2xl border border-gray-100 bg-gray-50 p-5">
        <h3 class="text-sm font-bold text-gray-800 mb-2">{m.visa_info_title()}</h3>
        <p class="text-xs text-gray-600 leading-relaxed">{m.visa_info_body()}</p>
      </div>
    </div>

    <!-- Right: market context -->
    <div>
      <h2 class="text-sm font-bold text-gray-800 mb-1">{m.visa_market_title()}</h2>
      <p class="text-xs text-gray-500 mb-4">{m.visa_market_subtitle()}</p>

      {#if loading}
        <div class="flex items-center gap-2 text-sm text-gray-500 py-8">
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
          </svg>
          {m.visa_market_loading()}
        </div>
      {:else if districtRows.length > 0}
        <!-- Summary totals -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4">
            <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{m.visa_market_above()}</p>
            <p class="text-xl font-bold text-amber-600">{fmt(totalAbove)}</p>
            <p class="text-xs text-gray-400">{pct(totalAbove, grandTotal)} of all tx</p>
          </div>
          <div class="rounded-xl border border-gray-200 bg-white p-4">
            <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{m.visa_market_below()}</p>
            <p class="text-xl font-bold text-gray-600">{fmt(totalBelow)}</p>
            <p class="text-xs text-gray-400">{pct(totalBelow, grandTotal)} of all tx</p>
          </div>
        </div>

        <!-- By district table -->
        <h3 class="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">{m.visa_market_by_district()}</h3>
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <table class="w-full text-xs">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="px-4 py-2.5 text-start font-semibold text-gray-500 uppercase tracking-wider text-[10px]">District</th>
                <th class="px-4 py-2.5 text-end font-semibold text-amber-600 uppercase tracking-wider text-[10px]">≥ AED 2M</th>
                <th class="px-4 py-2.5 text-end font-semibold text-gray-500 uppercase tracking-wider text-[10px]">Below</th>
                <th class="px-4 py-2.5 text-end font-semibold text-gray-500 uppercase tracking-wider text-[10px]">%</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              {#each districtRows as r}
                <tr class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-2.5 font-medium text-gray-800">{r.district}</td>
                  <td class="px-4 py-2.5 text-end font-bold text-amber-700">{fmt(r.above)}</td>
                  <td class="px-4 py-2.5 text-end text-gray-500">{fmt(r.below)}</td>
                  <td class="px-4 py-2.5 text-end">
                    <div class="flex items-center justify-end gap-1.5">
                      <div class="w-12 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                        <div class="h-full rounded-full bg-amber-400" style="width: {pct(r.above, r.total)}"></div>
                      </div>
                      <span class="text-[10px] font-semibold text-amber-700">{pct(r.above, r.total)}</span>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
          <div class="px-4 py-2 border-t border-gray-100 bg-gray-50">
            <p class="text-[10px] text-gray-400">{m.visa_market_total_tx({ total: String(fmt(grandTotal)) })}</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>
