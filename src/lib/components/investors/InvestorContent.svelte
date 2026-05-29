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

  // ── Nav strip ─────────────────────────────────────────────────────────────
  const NAV_ITEMS = [
    {
      id: 'section-calculators',
      label: 'Investment ROI Calculator',
      description: 'Model net yield, capital gain CAGR, and total ROI before you commit — for both ready and off-plan properties. Auto-populated with live ADREC rent and appreciation data.',
      iconPath: 'M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V13.5Zm0 2.25h.008v.008H8.25v-.008Zm2.25-4.5h.008v.008H10.5v-.008Zm0 2.25h.008v.008H10.5V13.5Zm0 2.25h.008v.008H10.5v-.008Zm2.25-4.5h.008v.008H12.75v-.008Zm0 2.25h.008v.008H12.75V13.5Zm0 2.25h.008v.008H12.75v-.008ZM6.75 6.75h10.5v10.5H6.75V6.75ZM6 3.75A2.25 2.25 0 0 1 8.25 1.5h7.5A2.25 2.25 0 0 1 18 3.75v.75H6v-.75Z',
    },
    {
      id: 'section-growth',
      label: 'Price Growth',
      description: 'Year-on-year appreciation leaders ranked by median AED/sqft across districts, sale projects, and rental projects — sourced directly from ADREC registered transactions.',
      iconPath: 'M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941',
    },
    {
      id: 'section-yield',
      label: 'Rental Yield',
      description: 'Gross rental yield benchmarks by community: registered rents divided by sale prices. Use this to shortlist high-yield areas before running a detailed calculator scenario.',
      iconPath: 'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z',
    },
    {
      id: 'section-charges',
      label: 'Service Charges',
      description: 'Annual ADREC-registered service charge rates by project in AED/sqft. This recurring cost directly erodes net rental yield and must be verified before any purchase decision.',
      iconPath: 'M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z',
    },
  ];

  let hoveredNav = $state<string | null>(null);

  function scrollToSection(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
</script>

<!-- ── Hero ────────────────────────────────────────────────────────────────── -->
<div class="bg-gradient-to-b from-[#0a2318] to-[#0e2d45] border-b border-white/5">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-5">
    <div class="flex items-center gap-3">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400 tracking-wider uppercase flex-shrink-0">
        <svg class="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
        </svg>
        Investor Intelligence
      </span>
      <h2 class="text-base sm:text-lg font-bold text-white leading-tight">
        Abu Dhabi Property Investment Insights
      </h2>
      <p class="hidden sm:block text-xs text-white/40 border-l border-white/10 pl-3 ml-1">
        ADREC transaction data · {prevSalesYear}–{salesYear}
      </p>
    </div>
  </div>
</div>

<!-- ── Nav strip (section contents) ────────────────────────────────────────── -->
<div class="bg-[#071913] border-b border-white/8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6">

    <!-- Tab buttons -->
    <div class="flex gap-0.5 pt-3 overflow-x-auto scrollbar-none">
      {#each NAV_ITEMS as item}
        <button
          type="button"
          onclick={() => scrollToSection(item.id)}
          onmouseenter={() => { hoveredNav = item.id; }}
          onmouseleave={() => { hoveredNav = null; }}
          class="flex-shrink-0 inline-flex items-center gap-2 px-5 py-2.5 rounded-t-lg text-sm font-semibold border-b-2 transition-all duration-150
            {hoveredNav === item.id
              ? 'text-emerald-300 border-emerald-400 bg-emerald-500/8'
              : 'text-white/40 border-transparent hover:text-white/65 hover:bg-white/4'}"
        >
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d={item.iconPath} />
          </svg>
          {item.label}
          <!-- Arrow indicator -->
          <svg class="w-3 h-3 flex-shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </button>
      {/each}
    </div>

    <!-- Description strip -->
    <div class="h-9 flex items-center">
      {#if hoveredNav}
        {@const item = NAV_ITEMS.find(n => n.id === hoveredNav)}
        {#if item}
          <p class="text-[11px] leading-snug text-white/50">
            <span class="font-semibold text-emerald-400">{item.label}:</span>
            {' '}{item.description}
          </p>
        {/if}
      {:else}
        <p class="text-[11px] text-white/20">Hover a section to learn more · click to jump there</p>
      {/if}
    </div>

  </div>
</div>

<!-- ── Content ─────────────────────────────────────────────────────────────── -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-10">

  <!-- ── Section: Investment Calculators ─────────────────────────────────────── -->
  <section id="section-calculators" class="scroll-mt-8">
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Investment Return Calculators
    </h3>
    <GatedSection proOnly={true}>
      <div class="flex gap-2 mb-4">
        <button
          type="button"
          onclick={() => { calcTab = 'offplan'; }}
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all {calcTab === 'offplan' ? 'bg-amber-500/15 border-amber-500/40 text-amber-300' : 'bg-white/10 border-white/25 text-white/65 hover:border-white/40 hover:text-white/85'}"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          Offplan Property
        </button>
        <button
          type="button"
          onclick={() => { calcTab = 'ready'; }}
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all {calcTab === 'ready' ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' : 'bg-white/10 border-white/25 text-white/65 hover:border-white/40 hover:text-white/85'}"
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

  <!-- ── Filter bar ──────────────────────────────────────────────────────────── -->
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

  <!-- ── Section: Year-on-Year Price Growth ──────────────────────────────────── -->
  <section id="section-growth" class="scroll-mt-8">
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

  <!-- ── Section: Gross Rental Yield ─────────────────────────────────────────── -->
  <section id="section-yield" class="scroll-mt-8">
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Gross Rental Yield by Community ({rentalYear} rents ÷ {salesYear} sale prices)
    </h3>
    <GatedSection proOnly={true}>
      <GatedBlur>
        <YieldTable rows={yieldRows} loading={loadingYield} />
      </GatedBlur>
    </GatedSection>
  </section>

  <!-- ── Section: Service Charges ────────────────────────────────────────────── -->
  <section id="section-charges" class="scroll-mt-8">
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Annual Service Charges · ADREC Registered Projects
    </h3>
    <GatedSection proOnly={true}>
      <GatedBlur>
        <ServiceChargeTable district={filterDistrict} />
      </GatedBlur>
    </GatedSection>
  </section>

</div>
