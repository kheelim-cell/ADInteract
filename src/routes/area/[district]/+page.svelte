<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { filters, dateRangeMs, prevDateRange, updateFilter } from '$lib/stores/filters';
  import { dbReady } from '$lib/stores/db';
  import {
    queryStats,
    queryChartData,
    queryTopProjects,
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

  let districtName = $derived(decodeURIComponent($page.params.district));

  let stats = $state<StatsResult | null>(null);
  let chartData = $state<ChartDataPoint[]>([]);
  let topDistricts = $state<DistrictSummary[]>([]);
  let priceDistribution = $state<PriceDistributionPoint[]>([]);
  let transactions = $state<Transaction[]>([]);
  let totalCount = $state(0);
  let loading = $state(false);

  onMount(() => {
    updateFilter({ district: districtName });
  });

  $effect(() => {
    const ready = $dbReady;
    const f = $filters;
    const range = $dateRangeMs;
    const prev = $prevDateRange;
    if (!ready) return;

    loading = true;

    Promise.all([
      queryStats(f, range.start, range.end, prev.start, prev.end),
      queryChartData(f, range.start, range.end),
      queryTopProjects(f, range.start, range.end),
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
      });
  });
</script>

<svelte:head>
  <title>{districtName} - ADInteract</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-6">
    <a href="/" class="hover:text-brand-600 transition-colors">Home</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="text-gray-900 font-medium">{districtName}</span>
  </nav>

  <!-- Page Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">{districtName}</h1>
      <p class="text-sm text-gray-500 mt-1">District-level real estate analytics</p>
    </div>
    <a
      href="/"
      class="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-brand-600 transition-colors bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-brand-300"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      Back to Overview
    </a>
  </div>

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

  <!-- Charts -->
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Median Price Trend</h3>
      {#if loading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <PriceTrendChart data={chartData} />
      {/if}
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Transaction Volume</h3>
      {#if loading && chartData.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <VolumeChart data={chartData} />
      {/if}
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Top Projects by Volume</h3>
      {#if loading && topDistricts.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <TopAreasChart data={topDistricts} clickable={false} />
      {/if}
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Price per Sqft by Layout</h3>
      {#if loading && priceDistribution.length === 0}
        <div class="h-64 flex items-center justify-center">
          <div class="animate-pulse text-gray-400 text-sm">Loading chart...</div>
        </div>
      {:else}
        <PriceDistributionChart data={priceDistribution} />
      {/if}
    </div>
  </div>

  <!-- Transaction Table -->
  <div class="mt-8">
    <TransactionTable {transactions} {totalCount} {loading} />
  </div>
</div>
