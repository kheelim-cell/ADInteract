<script lang="ts">
  import { rentalFilters } from '$lib/stores/rental_filters';
  import { dbReady, rentalMetadata } from '$lib/stores/db';
  import { browser } from '$app/environment';
  import {
    queryRentalStats,
    queryRentalTrend,
    queryRentalNewVsRenew,
    queryRentalProjects
  } from '$lib/db/rental_queries';
  import { resetRentalFilters } from '$lib/stores/rental_filters';
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

  // True once a query resolves with zero results
  let noResults = $derived(!loading && !chartsLoading && totalProjects === 0 && stats !== null);

  // Table state — initialise from URL params if available
  function readUrlTableState(): { col: string; dir: 'asc' | 'desc'; pg: number } {
    if (!browser) return { col: 'median_rent', dir: 'desc', pg: 1 };
    const p = new URLSearchParams(window.location.search);
    const SAFE_COLS = new Set(['project_name','district','median_rent','lower_rent','upper_rent','yoy_change']);
    const col = p.get('rsort') ?? 'median_rent';
    const dir = p.get('rdir') === 'asc' ? 'asc' : 'desc';
    const pg  = Math.max(1, parseInt(p.get('rpage') ?? '1', 10) || 1);
    return { col: SAFE_COLS.has(col) ? col : 'median_rent', dir, pg };
  }

  const _init = readUrlTableState();
  let tablePage    = $state(_init.pg);
  let tableSortCol = $state(_init.col);
  let tableSortDir = $state<'asc' | 'desc'>(_init.dir);
  const PAGE_SIZE = 50;

  // Sync table sort/page back to URL without navigation
  $effect(() => {
    const col = tableSortCol;
    const dir = tableSortDir;
    const pg  = tablePage;
    if (!browser) return;
    const url = new URL(window.location.href);
    url.searchParams.set('rsort', col);
    url.searchParams.set('rdir',  dir);
    if (pg === 1) {
      url.searchParams.delete('rpage');
    } else {
      url.searchParams.set('rpage', String(pg));
    }
    window.history.replaceState({}, '', url.toString());
  });

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

  <!-- Zero-result empty state banner -->
  {#if noResults}
    <div class="mt-6 rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-10 text-center">
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
        <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
        </svg>
      </div>
      <p class="mt-3 text-sm font-semibold text-gray-700">No rental listings match these filters</p>
      <p class="mt-1 text-xs text-gray-400">Try broadening the year range or removing a filter</p>
      <button
        type="button"
        onclick={resetRentalFilters}
        class="mt-4 inline-flex items-center gap-1.5 rounded-full px-5 py-2 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
      >
        Clear all filters
      </button>
    </div>
  {/if}

  <!-- Row 1: Trend + New vs Renewal -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-1">Median Rent Trend</h3>
      <p class="text-xs text-gray-400 mb-4">Year-on-year median across selected filters</p>
      {#if chartsLoading && trendData.length === 0}
        <div class="flex items-center justify-center" style="height:280px">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else if noResults}
        <div class="flex flex-col items-center justify-center gap-2 text-center" style="height:280px">
          <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm text-gray-400">No data for current filters</p>
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
      {:else if noResults}
        <div class="flex flex-col items-center justify-center gap-2 text-center" style="height:280px">
          <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm text-gray-400">No data for current filters</p>
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
