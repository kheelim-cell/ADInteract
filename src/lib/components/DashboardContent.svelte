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
  import FilterBar from '$lib/components/filters/FilterBar.svelte';
  import StatsGrid from '$lib/components/stats/StatsGrid.svelte';
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

  <!-- Stats -->
  <div class="mt-6">
    {#if loading && !stats}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
  </div>

  <!-- Primary charts: Price Trend + Volume -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-4">Median Price Trend</h3>
      {#if chartsLoading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <PriceTrendChart data={chartData} />
      {/if}
    </div>

    <div class="chart-card">
      <h3 class="text-sm font-semibold text-navy mb-4">Transaction Volume</h3>
      {#if chartsLoading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <VolumeChart data={chartData} />
      {/if}
    </div>
  </div>

  <!-- Transaction Table -->
  <div class="mt-8">
    <TransactionTable {transactions} {totalCount} {loading} />
  </div>

  <!-- Bottom charts -->
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
        {:else}
          <TopAreasChart data={topAreas} clickable={topAreasClickable} />
        {/if}
      </div>

      <div class="chart-card">
        <h3 class="text-sm font-semibold text-navy mb-4">Price per Sqft by Layout</h3>
        {#if chartsLoading && priceDistribution.length === 0}
          <div class="h-64 flex items-center justify-center">
            <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
          </div>
        {:else}
          <PriceDistributionChart data={priceDistribution} />
        {/if}
      </div>
    {/if}
  </div>
</div>
