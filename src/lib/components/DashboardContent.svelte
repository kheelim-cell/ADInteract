<script lang="ts">
  import { filters, dateRangeMs, prevDateRange } from '$lib/stores/filters';
  import { dbReady } from '$lib/stores/db';
  import {
    queryStats,
    queryChartData,
    queryTopDistricts,
    queryTopProjects,
    queryPriceDistribution,
    queryLayoutSummary,
    queryComparableProjects,
    queryTransactions,
    queryTransactionCount
  } from '$lib/db/queries';
  import { resetFilters } from '$lib/stores/filters';
  import FilterBar from '$lib/components/filters/FilterBar.svelte';
  import StatsGrid from '$lib/components/stats/StatsGrid.svelte';
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import GatedBlur from '$lib/components/auth/GatedBlur.svelte';
  import PriceTrendChart from '$lib/components/charts/PriceTrendChart.svelte';
  import VolumeChart from '$lib/components/charts/VolumeChart.svelte';
  import TopAreasChart from '$lib/components/charts/TopAreasChart.svelte';
  import PriceDistributionChart from '$lib/components/charts/PriceDistributionChart.svelte';
  import LayoutTable from '$lib/components/project/LayoutTable.svelte';
  import ComparableProjects from '$lib/components/project/ComparableProjects.svelte';
  import TransactionTable from '$lib/components/table/TransactionTable.svelte';
  import type {
    StatsResult,
    ChartDataPoint,
    DistrictSummary,
    PriceDistributionPoint,
    Transaction,
    LayoutSummaryRow,
    ComparableProject
  } from '$lib/db/types';

  let {
    topAreasLabel   = 'Top Areas by Volume',
    topAreasClickable = true,
    useTopProjects  = false,
    projectName     = ''
  }: {
    topAreasLabel?: string;
    topAreasClickable?: boolean;
    useTopProjects?: boolean;
    projectName?: string;
  } = $props();

  // Whether we're on a project detail page (changes bottom 2 charts)
  let isProjectPage = $derived(!!projectName);

  let stats             = $state<StatsResult | null>(null);
  let chartData         = $state<ChartDataPoint[]>([]);
  let topAreas          = $state<DistrictSummary[]>([]);
  let priceDistribution = $state<PriceDistributionPoint[]>([]);
  let layoutSummary     = $state<LayoutSummaryRow[]>([]);
  let comparables       = $state<ComparableProject[]>([]);
  let transactions      = $state<Transaction[]>([]);
  let totalCount        = $state(0);
  let loading           = $state(false);
  let chartsLoading     = $state(false);

  // True once a query has resolved with zero results (not during initial load)
  let noResults = $derived(!loading && !chartsLoading && totalCount === 0 && stats !== null);

  $effect(() => {
    const ready = $dbReady;
    const f     = $filters;
    const range = $dateRangeMs;
    const prev  = $prevDateRange;
    if (!ready) return;

    loading = true;
    chartsLoading = true;

    const timer = setTimeout(() => {
      // On project pages: run comparables + layout summary instead of top areas + boxplot
      const topAreasQuery = isProjectPage
        ? Promise.resolve([])
        : useTopProjects
          ? queryTopProjects(f, range.start, range.end)
          : queryTopDistricts(f, range.start, range.end);

      const bottomLeft  = isProjectPage
        ? queryComparableProjects(projectName, range.start, range.end)
        : topAreasQuery;
      const bottomRight = isProjectPage
        ? queryLayoutSummary(f, range.start, range.end)
        : queryPriceDistribution(f, range.start, range.end);

      Promise.all([
        queryStats(f, range.start, range.end, prev.start, prev.end),
        queryChartData(f, range.start, range.end),
        topAreasQuery,
        bottomLeft,
        bottomRight,
        queryTransactions(f, range.start, range.end),
        queryTransactionCount(f, range.start, range.end)
      ])
        .then(([s, c, ta, bl, br, t, cnt]) => {
          stats     = s;
          chartData = c;
          if (isProjectPage) {
            comparables   = bl as ComparableProject[];
            layoutSummary = br as LayoutSummaryRow[];
          } else {
            topAreas          = ta as DistrictSummary[];
            priceDistribution = br as PriceDistributionPoint[];
          }
          transactions = t;
          totalCount   = cnt;
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
  <!-- Filters -->
  <FilterBar />

  <!-- Stats (gated) -->
  <div class="mt-6">
    <GatedSection>
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
        <StatsGrid {stats} />
      {/if}
    </GatedSection>
  </div>

  <!-- Zero-result empty state banner -->
  {#if noResults}
    <div class="mt-6 rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-10 text-center">
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
        <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
        </svg>
      </div>
      <p class="mt-3 text-sm font-semibold text-gray-700">No transactions match these filters</p>
      <p class="mt-1 text-xs text-gray-400">Try broadening the date range or removing a filter</p>
      <button
        type="button"
        onclick={resetFilters}
        class="mt-4 inline-flex items-center gap-1.5 rounded-full px-5 py-2 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
      >
        Clear all filters
      </button>
    </div>
  {/if}

  <!-- Primary charts: Price Trend + Volume (gated) -->
  <GatedSection>
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-4">Median Price Trend</h3>
      {#if chartsLoading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else if noResults}
        <div class="h-64 flex flex-col items-center justify-center gap-2 text-center">
          <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm text-gray-400">No data for current filters</p>
        </div>
      {:else}
        <GatedBlur><PriceTrendChart data={chartData} /></GatedBlur>
      {/if}
    </div>

    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-4">Transaction Volume</h3>
      {#if chartsLoading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else if noResults}
        <div class="h-64 flex flex-col items-center justify-center gap-2 text-center">
          <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm text-gray-400">No data for current filters</p>
        </div>
      {:else}
        <GatedBlur><VolumeChart data={chartData} /></GatedBlur>
      {/if}
    </div>
  </div>
  </GatedSection>

  <!-- Transaction Table (always visible — teaser) -->
  <div class="mt-8">
    <TransactionTable {transactions} {totalCount} {loading} />
  </div>

  <!-- Bottom charts (gated) -->
  <GatedSection>
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    {#if isProjectPage}
      <!-- Project page: Comparable Projects + Layout Breakdown -->
      <div class="chart-card">
        <h3 class="text-sm font-semibold text-navy mb-4">Comparable Projects</h3>
        <p class="text-xs text-gray-400 mb-4 -mt-2">Closest AED/sqft in the same district</p>
        {#if chartsLoading && comparables.length === 0}
          <div class="h-48 flex items-center justify-center">
            <div class="animate-pulse text-gray-400 text-sm">Loading...</div>
          </div>
        {:else}
          <ComparableProjects data={comparables} />
        {/if}
      </div>

      <div class="chart-card">
        <h3 class="text-sm font-semibold text-navy mb-4">Price by Layout</h3>
        {#if chartsLoading && layoutSummary.length === 0}
          <div class="h-48 flex items-center justify-center">
            <div class="animate-pulse text-gray-400 text-sm">Loading...</div>
          </div>
        {:else}
          <LayoutTable data={layoutSummary} />
        {/if}
      </div>
    {:else}
      <!-- Default: Top Areas chart + Price Distribution boxplot -->
      <div class="chart-card">
        <h3 class="text-sm font-semibold text-navy mb-4">{topAreasLabel}</h3>
        {#if chartsLoading && topAreas.length === 0}
          <div class="h-64 flex items-center justify-center">
            <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
          </div>
        {:else if noResults}
          <div class="h-64 flex flex-col items-center justify-center gap-2 text-center">
            <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <p class="text-sm text-gray-400">No data for current filters</p>
          </div>
        {:else}
          <GatedBlur><TopAreasChart data={topAreas} clickable={topAreasClickable} /></GatedBlur>
        {/if}
      </div>

      <div class="chart-card">
        <h3 class="text-sm font-semibold text-navy mb-4">Price per Sqft by Layout</h3>
        {#if chartsLoading && priceDistribution.length === 0}
          <div class="h-64 flex items-center justify-center">
            <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
          </div>
        {:else if noResults}
          <div class="h-64 flex flex-col items-center justify-center gap-2 text-center">
            <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <p class="text-sm text-gray-400">No data for current filters</p>
          </div>
        {:else}
          <GatedBlur><PriceDistributionChart data={priceDistribution} /></GatedBlur>
        {/if}
      </div>
    {/if}
  </div>
  </GatedSection>
</div>
