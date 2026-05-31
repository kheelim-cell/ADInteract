<script lang="ts">
  import { filters, dateRangeMs, prevDateRange } from '$lib/stores/filters';
  import { dbReady } from '$lib/stores/db';
  import {
    queryStats,
    queryTransactions,
    queryTransactionCount
  } from '$lib/db/queries';
  import FilterBar from '$lib/components/filters/FilterBar.svelte';
  import TransactionTable from '$lib/components/table/TransactionTable.svelte';
  import AdStrip from '$lib/components/ads/AdStrip.svelte';
  import { formatCurrencyShort, formatNumber, formatRate } from '$lib/utils/format';
  import type { StatsResult, Transaction } from '$lib/db/types';

  let stats = $state<StatsResult | null>(null);
  let transactions = $state<Transaction[]>([]);
  let totalCount = $state(0);
  let loading = $state(false);

  $effect(() => {
    const ready = $dbReady;
    const f = $filters;
    const range = $dateRangeMs;
    const prev = $prevDateRange;
    if (!ready) return;

    loading = true;

    Promise.all([
      queryStats(f, range.start, range.end, prev.start, prev.end),
      queryTransactions(f, range.start, range.end),
      queryTransactionCount(f, range.start, range.end)
    ])
      .then(([s, t, cnt]) => {
        stats = s;
        transactions = t;
        totalCount = cnt;
      })
      .finally(() => {
        loading = false;
      });
  });
</script>

<svelte:head>
  <title>Abu Dhabi Property Transaction Explorer — Search 96K+ Sales | ADInteract</title>
  <meta name="description" content="Search and filter every Abu Dhabi property sale registered with ADREC. Sort by district, project, layout, price, and date — 96,000+ transactions with median AED/sqft data." />
  <meta property="og:title" content="Abu Dhabi Property Transaction Explorer — Search 96K+ Sales | ADInteract" />
  <meta property="og:description" content="Explore every Abu Dhabi property transaction registered with ADREC. Filter by district, project, layout, price range, and sale type — live data updated daily." />
  <meta property="og:url" content="https://adinteract.co/transactions" />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
  <!-- Page Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Transaction Explorer</h1>
      <p class="text-sm text-gray-500 mt-1">Browse and filter all Abu Dhabi real estate transactions</p>
    </div>
    <a
      href="/"
      class="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-brand-600 transition-colors bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-brand-300"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      Dashboard
    </a>
  </div>

  <!-- Filters -->
  <FilterBar />

  <!-- Compact Stats Summary Bar -->
  <div class="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 px-4 py-3">
    {#if loading && !stats}
      <div class="flex items-center gap-6 animate-pulse">
        {#each Array(4) as _}
          <div class="flex items-center gap-2">
            <div class="h-3 w-16 bg-gray-200 rounded"></div>
            <div class="h-4 w-20 bg-gray-200 rounded"></div>
          </div>
        {/each}
      </div>
    {:else if stats}
      <div class="flex flex-wrap items-center gap-x-8 gap-y-2 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Transactions</span>
          <span class="font-semibold text-gray-900">{formatNumber(stats.totalVolume)}</span>
        </div>
        <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Total Value</span>
          <span class="font-semibold text-gray-900">{formatCurrencyShort(stats.totalValue)} AED</span>
        </div>
        <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Median Price</span>
          <span class="font-semibold text-gray-900">{formatCurrencyShort(stats.medianPrice)} AED</span>
        </div>
        <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500">Median Rate</span>
          <span class="font-semibold text-gray-900">{formatRate(stats.medianRatePerSqft)}</span>
        </div>
      </div>
    {/if}
  </div>

  <!-- Sponsored ad strip — sales context -->
  <AdStrip context="sales" />

  <!-- Full-Width Transaction Table -->
  <div class="mt-6">
    <TransactionTable {transactions} {totalCount} {loading} />
  </div>
</div>
