<script lang="ts">
  import { rentalFilters } from '$lib/stores/rental_filters';
  import { dbReady, rentalMetadata } from '$lib/stores/db';
  import {
    queryRentalStats,
    queryRentalTrend,
    queryRentalNewVsRenew,
    queryRentalProjects
  } from '$lib/db/rental_queries';
  import RentalFilterBar from './RentalFilterBar.svelte';
  import RentalStatsGrid from './RentalStatsGrid.svelte';
  import RentalTrendChart from './RentalTrendChart.svelte';
  import RentalNewVsRenewChart from './RentalNewVsRenewChart.svelte';

  import RentalTable from './RentalTable.svelte';
  import type {
    RentalStatsResult,
    RentalTrendPoint,
    NewVsRenewRow,
    RentalProjectRow
  } from '$lib/db/rental_types';

  let stats: RentalStatsResult | null = $state(null);
  let trendData: RentalTrendPoint[] = $state([]);
  let newVsRenewData: NewVsRenewRow[] = $state([]);
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

  // Effect 1: stats + charts — re-runs when filters change
  $effect(() => {
    const f    = $rentalFilters;
    const meta = $rentalMetadata;
    const ly   = meta?.latestYear ?? new Date().getFullYear();
    if (!$dbReady || !meta) return;

    chartsLoading = true;
    const timer = setTimeout(() => {
      Promise.all([
        queryRentalStats(f, ly),
        queryRentalTrend(f, ly),
        queryRentalNewVsRenew(f, ly)
      ])
        .then(([s, trend, nvr]) => {
          stats          = s;
          trendData      = trend;
          newVsRenewData = nvr;
        })
        .finally(() => { chartsLoading = false; });
    }, 200);
    return () => clearTimeout(timer);
  });

  // Effect 2: project table — re-runs when filters OR sort/page change
  $effect(() => {
    const f    = $rentalFilters;
    const meta = $rentalMetadata;
    const ly   = meta?.latestYear ?? new Date().getFullYear();
    // Read these in the effect body so Svelte 5 tracks them as dependencies
    const col  = tableSortCol;
    const dir  = tableSortDir;
    const pg   = tablePage;
    if (!$dbReady || !meta) return;

    loading = true;
    const timer = setTimeout(() => {
      queryRentalProjects(f, ly, col, dir, pg, PAGE_SIZE)
        .then((proj) => {
          projectRows   = proj.rows;
          totalProjects = proj.total;
        })
        .finally(() => { loading = false; });
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

  <!-- Row 1: Trend + New vs Renewal -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-1">Median Rent Trend</h3>
      <p class="text-xs text-gray-400 mb-4">Year-on-year median across selected filters</p>
      {#if chartsLoading && trendData.length === 0}
        <div class="flex items-center justify-center" style="height:280px">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <RentalTrendChart data={trendData} />
      {/if}
    </div>

    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-1">New Contract vs Renewal</h3>
      <p class="text-xs text-gray-400 mb-4">Annual rent (AED) — how much more new tenants pay vs renewals</p>
      {#if chartsLoading && newVsRenewData.length === 0}
        <div class="flex items-center justify-center" style="height:280px">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <RentalNewVsRenewChart data={newVsRenewData} />
      {/if}
    </div>
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
