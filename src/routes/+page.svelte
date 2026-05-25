<script lang="ts">
  import { filters, dateRangeMs, prevDateRange } from '$lib/stores/filters';
  import { dbReady } from '$lib/stores/db';
  import {
    queryStats,
    queryChartData,
    queryTopDistricts,
    queryPriceDistribution,
    queryTransactions,
    queryTransactionCount
  } from '$lib/db/queries';
  import FilterBar from '$lib/components/filters/FilterBar.svelte';
  import StatsGrid from '$lib/components/stats/StatsGrid.svelte';
  import PriceTrendChart from '$lib/components/charts/PriceTrendChart.svelte';
  import VolumeChart from '$lib/components/charts/VolumeChart.svelte';
  import TopAreasChart from '$lib/components/charts/TopAreasChart.svelte';
  import PriceDistributionChart from '$lib/components/charts/PriceDistributionChart.svelte';
  import TransactionTable from '$lib/components/table/TransactionTable.svelte';
  import type {
    StatsResult,
    ChartDataPoint,
    DistrictSummary,
    PriceDistributionPoint,
    Transaction
  } from '$lib/db/types';

  let stats = $state<StatsResult | null>(null);
  let chartData = $state<ChartDataPoint[]>([]);
  let topDistricts = $state<DistrictSummary[]>([]);
  let priceDistribution = $state<PriceDistributionPoint[]>([]);
  let transactions = $state<Transaction[]>([]);
  let totalCount = $state(0);
  let loading = $state(false);
  let chartsLoading = $state(false);

  $effect(() => {
    const ready = $dbReady;
    const f = $filters;
    const range = $dateRangeMs;
    const prev = $prevDateRange;
    if (!ready) return;

    loading = true;
    chartsLoading = true;

    Promise.all([
      queryStats(f, range.start, range.end, prev.start, prev.end),
      queryChartData(f, range.start, range.end),
      queryTopDistricts(f, range.start, range.end),
      queryPriceDistribution(f, range.start, range.end),
      queryTransactions(f, range.start, range.end),
      queryTransactionCount(f, range.start, range.end)
    ])
      .then(([s, c, d, p, t, cnt]) => {
        stats = s;
        chartData = c;
        topDistricts = d;
        priceDistribution = p;
        transactions = t;
        totalCount = cnt;
      })
      .finally(() => {
        loading = false;
        chartsLoading = false;
      });
  });
</script>

<svelte:head>
  <title>ADInteract - Abu Dhabi Real Estate Analytics</title>
  <meta name="description" content="Abu Dhabi real estate transaction analytics dashboard" />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
  <!-- Filters -->
  <FilterBar />

  <!-- Stats Grid -->
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

  <!-- Charts Grid: Price Trend + Volume -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Price Trend -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Median Price Trend</h3>
      {#if chartsLoading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <PriceTrendChart data={chartData} />
      {/if}
    </div>

    <!-- Volume Chart -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Transaction Volume</h3>
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

  <!-- Secondary Charts: Top Areas + Price Distribution (below table) -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Top Areas -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Top Areas by Volume</h3>
      {#if chartsLoading && topDistricts.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <TopAreasChart data={topDistricts} />
      {/if}
    </div>

    <!-- Price Distribution -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Price per Sqft by Layout</h3>
      {#if chartsLoading && priceDistribution.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <PriceDistributionChart data={priceDistribution} />
      {/if}
    </div>
  </div>
</div>
