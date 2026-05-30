<script lang="ts">
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import {
    queryRentalYieldByCommunity,
    type YieldRow,
    type InvestorFilterState
  } from '$lib/db/investor_queries';
  import YieldTable from '$lib/components/investors/YieldTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import GatedBlur from '$lib/components/auth/GatedBlur.svelte';

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

  $effect(() => {
    const sy = salesYear;
    const ry = rentalYear;
    const f  = filters;
    loadingYield = true;

    queryRentalYieldByCommunity(sy, ry, 5, f)
      .then(rows => { yieldRows = rows; })
      .catch(() => { yieldRows = []; })
      .finally(() => { loadingYield = false; });
  });
</script>

<svelte:head>
  <title>Rental Yield — ADInteract Investor Intelligence</title>
  <meta name="description" content="Gross rental yield benchmarks by Abu Dhabi community from ADREC registered rents and sale prices." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <!-- ── Filter bar ──────────────────────────────────────────────────────── -->
  <div>
    <div class="flex flex-wrap items-center gap-3">
      <select bind:value={filterDistrict} class={sel}>
        <option value="">All Districts</option>
        {#each districts as d}
          <option value={d}>{d}</option>
        {/each}
      </select>

      <select bind:value={filterPropertyType} class={sel}>
        <option value="">All Property Types</option>
        {#each propertyTypes as pt}
          <option value={pt}>{pt}</option>
        {/each}
      </select>

      <select bind:value={filterLayout} class={sel}>
        <option value="">All Layouts</option>
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
          Clear filters
        </button>
      {/if}
    </div>
    <PopularAreaChips activeDistrict={filterDistrict || null} onSelect={(d) => { filterDistrict = d; }} />
  </div>

  <!-- ── Section heading ─────────────────────────────────────────────────── -->
  <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">
    Gross Rental Yield by Community ({rentalYear} rents ÷ {salesYear} sale prices)
  </h3>

  <!-- ── Yield table ─────────────────────────────────────────────────────── -->
  <GatedSection proOnly={true}>
    <GatedBlur>
      <YieldTable rows={yieldRows} loading={loadingYield} />
    </GatedBlur>
  </GatedSection>

</div>
