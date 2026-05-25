<script lang="ts">
  import { rentalFilters } from '$lib/stores/rental_filters';
  import { dbReady, rentalMetadata } from '$lib/stores/db';
  import {
    queryRentalStats,
    queryRentalByLayout,
    queryRentalTrend,
    queryTopRentalDistricts,
    queryRentalProjects
  } from '$lib/db/rental_queries';
  import RentalFilterBar from './RentalFilterBar.svelte';
  import RentalStatsGrid from './RentalStatsGrid.svelte';
  import RentalTrendChart from './RentalTrendChart.svelte';
  import RentalLayoutChart from './RentalLayoutChart.svelte';
  import RentalDistrictChart from './RentalDistrictChart.svelte';
  import RentalTable from './RentalTable.svelte';
  import type {
    RentalStatsResult,
    RentalLayoutRow,
    RentalTrendPoint,
    RentalDistrictRow,
    RentalProjectRow
  } from '$lib/db/rental_types';

  let stats: RentalStatsResult | null = $state(null);
  let layoutData: RentalLayoutRow[] = $state([]);
  let trendData: RentalTrendPoint[] = $state([]);
  let districtData: RentalDistrictRow[] = $state([]);
  let projectRows: RentalProjectRow[] = $state([]);
  let totalProjects = $state(0);
  let loading = $state(false);
  let chartsLoading = $state(false);

  // Table state
  let tablePage    = $state(1);
  let tableSortCol = $state('median_rent');
  let tableSortDir = $state<'asc' | 'desc'>('desc');
  const PAGE_SIZE = 50;

  function handleSort(col: string) {
    if (tableSortCol === col) {
      tableSortDir = tableSortDir === 'asc' ? 'desc' : 'asc';
    } else {
      tableSortCol = col;
      tableSortDir = 'desc';
    }
    tablePage = 1;
  }

  $effect(() => {
    const ready      = $dbReady;
    const f          = $rentalFilters;
    const meta       = $rentalMetadata;
    const latestYear = meta?.latestYear ?? new Date().getFullYear();

    if (!ready || !meta) return;

    loading       = true;
    chartsLoading = true;

    const timer = setTimeout(() => {
      Promise.all([
        queryRentalStats(f, latestYear),
        queryRentalByLayout(f, latestYear),
        queryRentalTrend(f, latestYear),
        queryTopRentalDistricts(f, latestYear),
        queryRentalProjects(f, latestYear, tableSortCol, tableSortDir, tablePage, PAGE_SIZE)
      ])
        .then(([s, lay, trend, dist, proj]) => {
          stats        = s;
          layoutData   = lay;
          trendData    = trend;
          districtData = dist;
          projectRows  = proj.rows;
          totalProjects = proj.total;
        })
        .finally(() => {
          loading       = false;
          chartsLoading = false;
        });
    }, 200);

    return () => clearTimeout(timer);
  });
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">

  <RentalFilterBar />

  <!-- Data year badge -->
  {#if $rentalMetadata}
    <div class="mt-4 flex items-center gap-2">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-blue-50 border border-blue-200 px-3 py-1 text-xs font-medium text-blue-700">
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        Annual rent benchmarks · {$rentalFilters.year ?? $rentalMetadata.latestYear} · {$rentalMetadata.rowCount.toLocaleString('en-US')} records
      </span>
      <span class="text-xs text-gray-400">Source: ADREC</span>
    </div>
  {/if}

  <!-- Stats -->
  <div class="mt-6">
    {#if loading && !stats}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {#each Array(4) as _}
          <div class="stat-card animate-pulse">
            <div class="h-3 w-20 bg-gray-200 rounded mb-3"></div>
            <div class="h-7 w-28 bg-gray-200 rounded mb-2"></div>
            <div class="h-3 w-16 bg-gray-200 rounded"></div>
          </div>
        {/each}
      </div>
    {:else if stats}
      <RentalStatsGrid {stats} />
    {/if}
  </div>

  <!-- Charts: Trend + Layout -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-1">Median Rent Trend</h3>
      <p class="text-xs text-gray-400 mb-4">Year-on-year median across selected filters</p>
      {#if chartsLoading && trendData.length === 0}
        <div class="h-52 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <RentalTrendChart data={trendData} />
      {/if}
    </div>

    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-1">Rent by Bed Size</h3>
      <p class="text-xs text-gray-400 mb-4">Lower / Median / Upper annual rent (AED)</p>
      {#if chartsLoading && layoutData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <RentalLayoutChart data={layoutData} />
      {/if}
    </div>
  </div>

  <!-- Top Districts chart -->
  <div class="mt-6 chart-card">
    <h3 class="text-sm font-semibold text-navy mb-1">Top Districts by Median Rent</h3>
    <p class="text-xs text-gray-400 mb-4">Click a bar to filter. Annual rent (AED) · {$rentalFilters.year ?? $rentalMetadata?.latestYear}</p>
    {#if chartsLoading && districtData.length === 0}
      <div class="h-64 flex items-center justify-center">
        <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
      </div>
    {:else}
      <RentalDistrictChart data={districtData} />
    {/if}
  </div>

  <!-- Project table -->
  <div class="mt-8">
    <RentalTable
      rows={projectRows}
      total={totalProjects}
      {loading}
      page={tablePage}
      pageSize={PAGE_SIZE}
      sortCol={tableSortCol}
      sortDir={tableSortDir}
      onSort={handleSort}
      onPage={(p) => (tablePage = p)}
    />
  </div>

</div>
