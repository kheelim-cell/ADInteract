<script lang="ts">
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import {
    queryTopDistrictsByGrowth,
    queryTopProjectsByGrowth,
    queryTopRentalProjectsByGrowth,
    queryRentalYieldByCommunity,
    type GrowthRow,
    type YieldRow,
    type InvestorFilterState
  } from '$lib/db/investor_queries';
  import GrowthLeaderboard from '$lib/components/investors/GrowthLeaderboard.svelte';
  import YieldTable from '$lib/components/investors/YieldTable.svelte';
  import ServiceChargeTable from '$lib/components/investors/ServiceChargeTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import GatedBlur from '$lib/components/auth/GatedBlur.svelte';
  import OffplanCalculator from '$lib/components/investors/OffplanCalculator.svelte';
  import ReadyCalculator from '$lib/components/investors/ReadyCalculator.svelte';

  // ── Year derivation ────────────────────────────────────────────────────────
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

  // ── Filter options from metadata ────────────────────────────────────────────
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

  // ── Query state ────────────────────────────────────────────────────────────
  let districtRows      = $state<GrowthRow[]>([]);
  let salesProjectRows  = $state<GrowthRow[]>([]);
  let rentalProjectRows = $state<GrowthRow[]>([]);
  let yieldRows         = $state<YieldRow[]>([]);

  let loadingSales  = $state(true);
  let loadingRental = $state(true);
  let loadingYield  = $state(true);

  // ── Sales queries ──────────────────────────────────────────────────────────
  $effect(() => {
    const cy = salesYear;
    const py = prevSalesYear;
    const f  = filters;
    loadingSales = true;

    Promise.all([
      queryTopDistrictsByGrowth(cy, py, 5, f),
      queryTopProjectsByGrowth(cy, py, 5, f),
    ])
      .then(([districts, projects]) => {
        districtRows     = districts;
        salesProjectRows = projects;
      })
      .catch(() => {
        districtRows     = [];
        salesProjectRows = [];
      })
      .finally(() => { loadingSales = false; });
  });

  // ── Rental growth query ────────────────────────────────────────────────────
  $effect(() => {
    const ry = rentalYear;
    const f  = filters;
    loadingRental = true;

    queryTopRentalProjectsByGrowth(ry, 5, f)
      .then(rows => { rentalProjectRows = rows; })
      .catch(() => { rentalProjectRows = []; })
      .finally(() => { loadingRental = false; });
  });

  // ── Yield query ────────────────────────────────────────────────────────────
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

  // ── Shared select style ────────────────────────────────────────────────────
  const sel = 'text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]';

  // ── Calculator tab ─────────────────────────────────────────────────────────
  let calcTab = $state<'offplan' | 'ready'>('offplan');
</script>

<!-- ── Hero ────────────────────────────────────────────────────────────────── -->
<div class="bg-gradient-to-b from-[#0a2318] to-[#0e2d45] border-b border-white/5">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
      <div>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 px-3 py-1 text-xs font-bold text-emerald-400 tracking-wider uppercase mb-3">
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
          </svg>
          Investor Intelligence
        </span>
        <h2 class="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
          Abu Dhabi Property Investment Insights
        </h2>
        <p class="text-sm text-white/45 mt-1.5 max-w-xl">
          Year-on-year price growth, rental returns, and yield benchmarks sourced from ADREC transaction data.
        </p>
      </div>

      <!-- Year comparison pill -->
      {#if salesYear}
        <div class="flex-shrink-0 flex items-center gap-2 rounded-2xl bg-white/6 border border-white/12 px-4 py-2.5">
          <div class="text-center">
            <p class="text-[10px] font-semibold text-white/35 uppercase tracking-wider">Comparison</p>
            <p class="text-base font-black text-white/70 tabular-nums leading-none mt-0.5">
              {prevSalesYear}
              <span class="text-white/30 font-light mx-1">→</span>
              <span class="text-emerald-400">{salesYear}</span>
            </p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- ── Content ─────────────────────────────────────────────────────────────── -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-10">

  <!-- ── Filter bar ──────────────────────────────────────────────────────────── -->
  <div>
  <div class="flex flex-wrap items-center gap-3">
    <!-- District -->
    <select bind:value={filterDistrict} class={sel}>
      <option value="">All Districts</option>
      {#each districts as d}
        <option value={d}>{d}</option>
      {/each}
    </select>

    <!-- Property Type -->
    <select bind:value={filterPropertyType} class={sel}>
      <option value="">All Property Types</option>
      {#each propertyTypes as pt}
        <option value={pt}>{pt}</option>
      {/each}
    </select>

    <!-- Layout -->
    <select bind:value={filterLayout} class={sel}>
      <option value="">All Layouts</option>
      {#each layouts as l}
        <option value={l}>{LAYOUT_DISPLAY[l.toLowerCase()] ?? l}</option>
      {/each}
    </select>

    <!-- Reset -->
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

  <!-- Section 1: Growth leaderboards (3-col grid on lg) -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Year-on-Year Price Growth ({prevSalesYear} → {salesYear})
    </h3>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <GatedSection proOnly={true}>
        <GatedBlur>
          <GrowthLeaderboard
            title="Top Districts · Sale Rate Growth"
            subtitle="Median AED/sqft · min 10 transactions each year"
            rows={districtRows}
            loading={loadingSales}
            valueLabel="/sqft"
            linkPrefix="area"
          />
        </GatedBlur>
      </GatedSection>

      <GatedSection proOnly={true}>
        <GatedBlur>
          <GrowthLeaderboard
            title="Top Projects · Sale Rate Growth"
            subtitle="Median AED/sqft · min 5 transactions each year"
            rows={salesProjectRows}
            loading={loadingSales}
            valueLabel="/sqft"
            linkPrefix="project"
          />
        </GatedBlur>
      </GatedSection>

      <GatedSection proOnly={true}>
        <GatedBlur>
          <GrowthLeaderboard
            title="Top Projects · Rental Growth"
            subtitle="Median annual rent · {rentalYear - 1} → {rentalYear}"
            rows={rentalProjectRows}
            loading={loadingRental}
            valueLabel="/yr"
            linkPrefix="project"
          />
        </GatedBlur>
      </GatedSection>

    </div>
  </section>

  <!-- Section 2: Gross Rental Yield table -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Gross Rental Yield by Community ({rentalYear} rents ÷ {salesYear} sale prices)
    </h3>
    <GatedSection proOnly={true}>
      <GatedBlur>
        <YieldTable rows={yieldRows} loading={loadingYield} />
      </GatedBlur>
    </GatedSection>
  </section>

  <!-- Section 3: Service Charges -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Annual Service Charges · ADREC Registered Projects
    </h3>
    <GatedSection proOnly={true}>
      <GatedBlur>
        <ServiceChargeTable district={filterDistrict} />
      </GatedBlur>
    </GatedSection>
  </section>

  <!-- Section 4: Investment Calculators -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Investment Return Calculators
    </h3>
    <GatedSection proOnly={true}>
      <!-- Tab switcher -->
      <div class="flex gap-2 mb-4">
        <button
          type="button"
          onclick={() => { calcTab = 'offplan'; }}
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all {calcTab === 'offplan' ? 'bg-amber-500/15 border-amber-500/40 text-amber-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'}"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          Offplan
        </button>
        <button
          type="button"
          onclick={() => { calcTab = 'ready'; }}
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all {calcTab === 'ready' ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'}"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          Ready Property
        </button>
      </div>

      {#if calcTab === 'offplan'}
        <OffplanCalculator />
      {:else}
        <ReadyCalculator />
      {/if}
    </GatedSection>
  </section>

</div>
