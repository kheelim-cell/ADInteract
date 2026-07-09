<script lang="ts">
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import {
    queryRentalYieldByCommunity,
    type YieldRow,
    type InvestorFilterState
  } from '$lib/db/investor_queries';
  import { queryRentalActivity, type RentalActivityRow } from '$lib/db/rental_queries';
  import YieldTable from '$lib/components/investors/YieldTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import { m } from '$lib/paraglide/messages.js';

  const thisCalendarYear = new Date().getFullYear();

  let salesYear = $derived.by(() => {
    const maxStr = $metadata?.dateRange?.max;
    if (!maxStr) return thisCalendarYear - 1;
    const maxDataYear = new Date(maxStr).getFullYear();
    return maxDataYear >= thisCalendarYear ? thisCalendarYear - 1 : maxDataYear;
  });

  let rentalYear = $derived.by(() => {
    const ly = $rentalMetadata?.latestYear;
    if (!ly) return thisCalendarYear - 1;
    return ly >= thisCalendarYear ? thisCalendarYear - 1 : ly;
  });

  // ── Filter state ───────────────────────────────────────────────────────────
  let filterDistrict     = $state('');
  let filterPropertyType = $state('');
  let filterLayout       = $state('');

  let filters = $derived<InvestorFilterState>({
    district:     filterDistrict     || null,
    propertyType: filterPropertyType || null,
    layout:       filterLayout       || null,
  });

  let hasFilter = $derived(!!(filterDistrict || filterPropertyType || filterLayout));

  function resetFilters() {
    filterDistrict     = '';
    filterPropertyType = '';
    filterLayout       = '';
  }

  // ── Filter options ─────────────────────────────────────────────────────────
  const EXCLUDED_PROP_TYPES = new Set(['office', 'retail']);
  const LAYOUT_ORDER = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds', '5+ beds', '6+ beds'];
  const LAYOUT_DISPLAY: Record<string, string> = { studio: 'Studio' };

  let districts     = $derived($metadata?.districts ?? []);
  let propertyTypes = $derived(($metadata?.propertyTypes ?? []).filter(pt => !EXCLUDED_PROP_TYPES.has(pt.toLowerCase())));
  let layouts       = $derived(
    ($metadata?.layouts ?? [])
      .filter(l => LAYOUT_ORDER.includes(l.toLowerCase()))
      .sort((a, b) => LAYOUT_ORDER.indexOf(a.toLowerCase()) - LAYOUT_ORDER.indexOf(b.toLowerCase()))
  );

  const sel = 'text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]';

  // ── Query state ────────────────────────────────────────────────────────────
  let yieldRows    = $state<YieldRow[]>([]);
  let loadingYield = $state(true);
  let activityRows = $state<RentalActivityRow[]>([]);

  $effect(() => {
    const sy = salesYear;
    const ry = rentalYear;
    const f  = filters;
    loadingYield = true;

    queryRentalYieldByCommunity(sy, ry, 5, f)
      .then(rows => { yieldRows = rows; })
      .catch(() => { yieldRows = []; })
      .finally(() => { loadingYield = false; });

    queryRentalActivity(ry, f.district ?? undefined)
      .then(rows => { activityRows = rows; })
      .catch(() => { activityRows = []; });
  });
</script>

<svelte:head>
  <title>{m.seo_rentalyield_title()}</title>
  <meta name="description" content={m.seo_rentalyield_description()} />
  <meta property="og:title" content={m.seo_rentalyield_title()} />
  <meta property="og:description" content={m.seo_rentalyield_og_description()} />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <!-- ── Filter bar ──────────────────────────────────────────────────────── -->
  <div>
    <div class="flex flex-wrap items-center gap-3">
      <select bind:value={filterDistrict} class={sel}>
        <option value="">{m.calc_district_all()}</option>
        {#each districts as d}
          <option value={d}>{d}</option>
        {/each}
      </select>

      <select bind:value={filterPropertyType} class={sel}>
        <option value="">{m.pricegrowth_all_property_types()}</option>
        {#each propertyTypes as pt}
          <option value={pt}>{pt}</option>
        {/each}
      </select>

      <select bind:value={filterLayout} class={sel}>
        <option value="">{m.flip_all_layouts()}</option>
        {#each layouts as l}
          <option value={l}>{LAYOUT_DISPLAY[l.toLowerCase()] ?? l}</option>
        {/each}
      </select>

      {#if hasFilter}
        <button
          type="button"
          onclick={resetFilters}
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
          {m.pipeline_clear_filters()}
        </button>
      {/if}
    </div>
    <PopularAreaChips activeDistrict={filterDistrict || null} onSelect={(d) => { filterDistrict = d; }} />
  </div>

  <!-- ── Section heading ─────────────────────────────────────────────────── -->
  <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">
    {m.rentalyield_section_heading({ rentalYear: String(rentalYear), salesYear: String(salesYear) })}
  </h3>

  <!-- ── Yield table ─────────────────────────────────────────────────────── -->
  <YieldTable rows={yieldRows} loading={loadingYield} />

  <!-- ── Rental Activity (occupancy proxy) ──────────────────────────────── -->
  {#if activityRows.length > 0}
    <div class="mt-8">
      <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">
        Rental Market Activity — Occupancy Signal by District
      </h3>
      <p class="text-xs text-gray-400 mb-4">
        New vs renewal contract split · {rentalYear} ADREC data.
        <span class="italic">True vacancy data is not published by ADREC. This signal is derived from new vs renewal contract ratios — a proxy, not a direct measure.</span>
      </p>
      <div class="rounded-xl border border-gray-200 overflow-hidden">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-4 py-2.5 text-start text-[10px] font-semibold text-gray-500 uppercase tracking-wider">District</th>
              <th class="px-4 py-2.5 text-end text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">New Contracts</th>
              <th class="px-4 py-2.5 text-end text-[10px] font-semibold text-blue-600 uppercase tracking-wider">Renewals</th>
              <th class="px-4 py-2.5 text-start text-[10px] font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Split</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each activityRows as r}
              <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-2.5 font-medium text-gray-800">{r.district}</td>
                <td class="px-4 py-2.5 text-end">
                  <span class="font-semibold text-emerald-700">{r.new_pct}%</span>
                  <span class="text-gray-400 ml-1">({r.new_count.toLocaleString('en-AE')})</span>
                </td>
                <td class="px-4 py-2.5 text-end">
                  <span class="font-semibold text-blue-700">{r.renewal_pct}%</span>
                  <span class="text-gray-400 ml-1">({r.renewal_count.toLocaleString('en-AE')})</span>
                </td>
                <td class="px-4 py-2.5 hidden sm:table-cell">
                  <div class="flex h-2 w-full rounded-full overflow-hidden bg-gray-100">
                    <div class="bg-emerald-400" style="width: {r.new_pct}%"></div>
                    <div class="bg-blue-400" style="width: {r.renewal_pct}%"></div>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
        <div class="px-4 py-2 border-t border-gray-100 bg-gray-50 flex items-center gap-4 text-[10px] text-gray-400">
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span> New contract</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block"></span> Renewal · Higher renewal % = lower vacancy signal</span>
        </div>
      </div>
    </div>
  {/if}

</div>
