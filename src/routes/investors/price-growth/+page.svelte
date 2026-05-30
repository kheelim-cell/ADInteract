<script lang="ts">
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import {
    queryTopDistrictsByGrowth,
    queryTopProjectsByGrowth,
    queryTopRentalProjectsByGrowth,
    type GrowthRow,
    type InvestorFilterState
  } from '$lib/db/investor_queries';
  import GrowthLeaderboard from '$lib/components/investors/GrowthLeaderboard.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';

  const thisCalendarYear = new Date().getFullYear();

  let salesYear = $derived.by(() => {
    const maxStr = $metadata?.dateRange?.max;
    if (!maxStr) return thisCalendarYear - 1;
    const maxDataYear = new Date(maxStr).getFullYear();
    return maxDataYear >= thisCalendarYear ? thisCalendarYear - 1 : maxDataYear;
  });

  let prevSalesYear = $derived(salesYear - 1);

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
  let districtRows      = $state<GrowthRow[]>([]);
  let salesProjectRows  = $state<GrowthRow[]>([]);
  let rentalProjectRows = $state<GrowthRow[]>([]);
  let loadingSales      = $state(true);
  let loadingRental     = $state(true);

  $effect(() => {
    const cy = salesYear;
    const py = prevSalesYear;
    const f  = filters;
    loadingSales = true;

    Promise.all([
      queryTopDistrictsByGrowth(cy, py, 5, f),
      queryTopProjectsByGrowth(cy, py, 5, f),
    ])
      .then(([d, p]) => {
        districtRows     = d;
        salesProjectRows = p;
      })
      .catch(() => {
        districtRows     = [];
        salesProjectRows = [];
      })
      .finally(() => { loadingSales = false; });
  });

  $effect(() => {
    const ry = rentalYear;
    const f  = filters;
    loadingRental = true;

    queryTopRentalProjectsByGrowth(ry, 5, f)
      .then(rows => { rentalProjectRows = rows; })
      .catch(() => { rentalProjectRows = []; })
      .finally(() => { loadingRental = false; });
  });
</script>

<svelte:head>
  <title>Abu Dhabi Property Price Growth 2025 — Best Appreciating Areas | ADInteract</title>
  <meta name="description" content="Which Abu Dhabi districts and projects grew the most in value? Year-on-year price appreciation ranked by median AED/sqft — sourced from ADREC registered transactions." />
  <meta property="og:title" content="Abu Dhabi Property Price Growth 2025 — Best Appreciating Areas | ADInteract" />
  <meta property="og:description" content="Ranked year-on-year price appreciation by district and project in Abu Dhabi. Median AED/sqft growth from ADREC transaction data." />
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
    Year-on-Year Price Growth ({prevSalesYear} → {salesYear})
  </h3>

  <!-- ── Leaderboards ────────────────────────────────────────────────────── -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
    <GrowthLeaderboard
      title="Top Districts · Sale Rate Growth"
      subtitle="Median AED/sqft · min 10 transactions each year"
      rows={districtRows}
      loading={loadingSales}
      valueLabel="/sqft"
      linkPrefix="area"
    />

    <GrowthLeaderboard
      title="Top Projects · Sale Rate Growth"
      subtitle="Median AED/sqft · min 5 transactions each year"
      rows={salesProjectRows}
      loading={loadingSales}
      valueLabel="/sqft"
      linkPrefix="project"
    />

    <GrowthLeaderboard
      title="Top Projects · Rental Growth"
      subtitle="Median annual rent · {rentalYear - 1} → {rentalYear}"
      rows={rentalProjectRows}
      loading={loadingRental}
      valueLabel="/yr"
      linkPrefix="project"
    />
  </div>

</div>
