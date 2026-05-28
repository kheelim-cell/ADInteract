<script lang="ts">
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import {
    queryTopDistrictsByGrowth,
    queryTopProjectsByGrowth,
    queryTopRentalProjectsByGrowth,
    queryRentalYieldByCommunity,
    type GrowthRow,
    type YieldRow
  } from '$lib/db/investor_queries';
  import GrowthLeaderboard from '$lib/components/investors/GrowthLeaderboard.svelte';
  import YieldTable from '$lib/components/investors/YieldTable.svelte';

  // ── Year derivation ────────────────────────────────────────────────────────
  // Use the last FULL calendar year so stats are complete.
  // If data only reaches e.g. 2024, use 2024; if it reaches 2026+, use 2025.
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

  // ── Query state ────────────────────────────────────────────────────────────
  let districtRows     = $state<GrowthRow[]>([]);
  let salesProjectRows = $state<GrowthRow[]>([]);
  let rentalProjectRows = $state<GrowthRow[]>([]);
  let yieldRows        = $state<YieldRow[]>([]);

  let loadingSales  = $state(true);
  let loadingRental = $state(true);
  let loadingYield  = $state(true);

  // ── Sales queries (districts + projects growth) ───────────────────────────
  $effect(() => {
    const cy = salesYear;
    const py = prevSalesYear;
    loadingSales = true;

    Promise.all([
      queryTopDistrictsByGrowth(cy, py, 5),
      queryTopProjectsByGrowth(cy, py, 5),
    ])
      .then(([districts, projects]) => {
        districtRows = districts;
        salesProjectRows = projects;
      })
      .catch(() => {
        districtRows = [];
        salesProjectRows = [];
      })
      .finally(() => {
        loadingSales = false;
      });
  });

  // ── Rental growth query ───────────────────────────────────────────────────
  $effect(() => {
    const ry = rentalYear;
    loadingRental = true;

    queryTopRentalProjectsByGrowth(ry, 5)
      .then(rows => { rentalProjectRows = rows; })
      .catch(() => { rentalProjectRows = []; })
      .finally(() => { loadingRental = false; });
  });

  // ── Yield query ───────────────────────────────────────────────────────────
  $effect(() => {
    const sy = salesYear;
    const ry = rentalYear;
    loadingYield = true;

    queryRentalYieldByCommunity(sy, sy, 5)
      .then(rows => { yieldRows = rows; })
      .catch(() => { yieldRows = []; })
      .finally(() => { loadingYield = false; });
  });
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

  <!-- Section 1: Growth leaderboards (3-col grid on lg) -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Year-on-Year Price Growth ({prevSalesYear} → {salesYear})
    </h3>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

      <!-- Top Districts by Sales Rate Growth -->
      <GrowthLeaderboard
        title="Top Districts · Sale Rate Growth"
        subtitle="Median AED/sqft · min 10 transactions each year"
        rows={districtRows}
        loading={loadingSales}
        valueLabel="/sqft"
        linkPrefix="area"
      />

      <!-- Top Projects by Sales Rate Growth -->
      <GrowthLeaderboard
        title="Top Projects · Sale Rate Growth"
        subtitle="Median AED/sqft · min 5 transactions each year"
        rows={salesProjectRows}
        loading={loadingSales}
        valueLabel="/sqft"
        linkPrefix="project"
      />

      <!-- Top Projects by Rental Growth -->
      <GrowthLeaderboard
        title="Top Projects · Rental Growth"
        subtitle="Median annual rent · {rentalYear - 1} → {rentalYear}"
        rows={rentalProjectRows}
        loading={loadingRental}
        valueLabel="/yr"
        linkPrefix="project"
      />

    </div>
  </section>

  <!-- Section 2: Gross Rental Yield table -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
      Gross Rental Yield by Community ({salesYear} rents ÷ {salesYear} sale prices)
    </h3>
    <YieldTable rows={yieldRows} loading={loadingYield} />
  </section>

</div>
