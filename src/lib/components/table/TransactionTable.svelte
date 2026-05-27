<script lang="ts">
  import { filters, updateFilter, resetFilters, dateRangeMs } from '$lib/stores/filters';
  import type { Transaction } from '$lib/db/types';
  import { formatDate, formatNumber, formatCurrency, formatArea, formatRate } from '$lib/utils/format';
  import { exportTransactions } from '$lib/db/queries';
  import { base } from '$app/paths';
  import { isAuthenticated, openSignIn } from '$lib/stores/auth';
  import { supabaseEnabled } from '$lib/supabase';

  let exporting = $state(false);

  async function handleExport() {
    exporting = true;
    try {
      const range = $dateRangeMs;
      const rows = await exportTransactions($filters, range.start, range.end);

      const headers = [
        'Date', 'District', 'Community', 'Project',
        'Property Type', 'Layout', 'Area (sqft)',
        'Price (AED)', 'Rate (AED/sqft)', 'Sale Type', 'Sale Sequence'
      ];

      const escape = (v: unknown) => {
        const s = v == null ? '' : String(v);
        return s.includes(',') || s.includes('"') || s.includes('\n')
          ? `"${s.replace(/"/g, '""')}"`
          : s;
      };

      const csvRows = [
        headers.join(','),
        ...rows.map((r) => [
          r.sale_date, r.district, r.community, r.project_name,
          r.property_type, r.layout, r.area_sqft ?? '',
          r.price_aed, r.rate_per_sqft ?? '', r.sale_type, r.sale_sequence
        ].map(escape).join(','))
      ];

      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `adinteract-${range.start}-to-${range.end}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      exporting = false;
    }
  }

  let {
    transactions = [] as Transaction[],
    totalCount = 0,
    loading = false
  } = $props();

  interface Column {
    key: string;
    label: string;
    subLabel?: string;
    sortable: boolean;
    align: 'left' | 'right' | 'center';
    width?: string;
  }

  const columns: Column[] = [
    { key: 'sale_date', label: 'DATE', sortable: true, align: 'left', width: 'w-[100px]' },
    { key: 'project_name', label: 'LOCATION', sortable: true, align: 'left' },
    { key: 'price_aed', label: 'PRICE (AED)', sortable: true, align: 'right', width: 'w-[160px]' },
    { key: 'property_type', label: 'TYPE', sortable: true, align: 'center', width: 'w-[100px]' },
    { key: 'layout', label: 'BEDS', sortable: true, align: 'center', width: 'w-[90px]' },
    { key: 'area_sqft', label: 'AREA (SQFT)', sortable: true, align: 'right', width: 'w-[110px]' },
    { key: 'sale_type',     label: 'SALE SCENARIO', sortable: true, align: 'center', width: 'w-[130px]' },
    { key: 'sale_sequence', label: 'SEQUENCE',      sortable: true, align: 'center', width: 'w-[110px]' },
  ];

  let currentPage = $derived($filters.page);
  let pageSize = $derived($filters.pageSize);
  let totalPages = $derived(Math.max(1, Math.ceil(totalCount / pageSize)));
  let showStart = $derived((currentPage - 1) * pageSize + 1);
  let showEnd = $derived(Math.min(currentPage * pageSize, totalCount));

  let sortOptions = [
    { value: 'sale_date:desc', label: 'Newest' },
    { value: 'sale_date:asc', label: 'Oldest' },
    { value: 'price_aed:desc', label: 'High price' },
    { value: 'price_aed:asc', label: 'Low price' },
    { value: 'rate_per_sqft:desc', label: 'High price /sqft' },
    { value: 'rate_per_sqft:asc', label: 'Low price /sqft' },
  ];

  let currentSort = $derived(`${$filters.sortColumn}:${$filters.sortDirection}`);

  function handleSortChange(e: Event) {
    const val = (e.target as HTMLSelectElement).value;
    const [col, dir] = val.split(':');
    updateFilter({ sortColumn: col, sortDirection: dir as 'asc' | 'desc', page: 1 });
  }

  function handleColumnSort(column: string) {
    const currentCol = $filters.sortColumn;
    const currentDir = $filters.sortDirection;
    if (currentCol === column) {
      updateFilter({ sortColumn: column, sortDirection: currentDir === 'asc' ? 'desc' : 'asc', page: 1 });
    } else {
      updateFilter({ sortColumn: column, sortDirection: 'desc', page: 1 });
    }
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      updateFilter({ page });
    }
  }

  function formatLayout(layout: string): string {
    if (!layout || layout === 'unclassified') return '-';
    return layout.charAt(0).toUpperCase() + layout.slice(1);
  }

  let paginationPages = $derived(() => {
    const pages: (number | '...')[] = [];
    const total = totalPages;
    const current = currentPage;

    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      if (current > 3) pages.push('...');
      const start = Math.max(2, current - 1);
      const end = Math.min(total - 1, current + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (current < total - 2) pages.push('...');
      pages.push(total);
    }
    return pages;
  });

  // Condensed pagination for mobile (prev/next + current page indicator only)
  let mobilePaginationPages = $derived(() => {
    const pages: (number | '...')[] = [];
    const total = totalPages;
    const current = currentPage;
    if (total <= 5) {
      for (let i = 1; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      if (current > 2) pages.push('...');
      if (current !== 1 && current !== total) pages.push(current);
      if (current < total - 1) pages.push('...');
      pages.push(total);
    }
    return pages;
  });

  const skeletonRows = Array.from({ length: 10 });

  let locked = $derived(supabaseEnabled && !$isAuthenticated);
</script>

<div class="rounded-2xl bg-white shadow-sm border border-white/80 overflow-hidden">
  <!-- Sort bar -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 gap-3">
    <div class="flex items-center gap-2 min-w-0">
      <label for="sort-select" class="hidden sm:block text-sm text-gray-500 whitespace-nowrap flex-shrink-0">Sort by</label>
      <select
        id="sort-select"
        value={currentSort}
        onchange={handleSortChange}
        class="text-sm font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 min-w-0"
      >
        {#each sortOptions as opt}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>
    {#if totalCount > 0}
      <div class="flex items-center gap-2 flex-shrink-0">
        <span class="text-xs sm:text-sm text-gray-500 whitespace-nowrap">
          {totalCount.toLocaleString()} <span class="hidden sm:inline">transactions</span>
        </span>
        <button
          type="button"
          onclick={handleExport}
          disabled={exporting || loading}
          title="Export CSV"
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-gray-600 shadow-sm transition-colors hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#if exporting}
            <svg class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            <span class="hidden sm:inline">Exporting...</span>
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span class="hidden sm:inline">Export CSV</span>
          {/if}
        </button>
      </div>
    {/if}
  </div>

  <!-- ─── DATA ROWS (gated when not signed in) ──────────────────────────── -->
  <div class="relative">
    <!-- Blur + wash overlay -->
    {#if locked}
      <div class="absolute inset-0 bg-white/50 z-[5]"></div>
      <div class="absolute inset-0 flex items-center justify-center z-10">
        <button
          type="button"
          onclick={openSignIn}
          class="inline-flex items-center gap-2 rounded-full bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-brand-600 transition-colors"
        >
          <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
          Sign In to view transactions
        </button>
      </div>
    {/if}

  <!-- ─── MOBILE CARD VIEW (< md) ─────────────────────────────────────────── -->
  <div class={`block md:hidden${locked ? ' blur-md pointer-events-none select-none' : ''}`}>
    {#if loading}
      <div class="divide-y divide-gray-50">
        {#each skeletonRows as _}
          <div class="animate-pulse px-4 py-4 space-y-2">
            <div class="flex justify-between">
              <div class="h-4 w-36 bg-gray-100 rounded"></div>
              <div class="h-4 w-24 bg-gray-100 rounded"></div>
            </div>
            <div class="h-3 w-24 bg-gray-100 rounded"></div>
            <div class="flex gap-2 mt-1">
              <div class="h-3 w-16 bg-gray-100 rounded"></div>
              <div class="h-3 w-12 bg-gray-100 rounded"></div>
            </div>
          </div>
        {/each}
      </div>
    {:else if transactions.length === 0}
      <div class="px-4 py-16 text-center">
        <div class="flex flex-col items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
            <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-semibold text-gray-700">No transactions match these filters</p>
            <p class="mt-1 text-xs text-gray-400">Try broadening the date range or removing a filter</p>
          </div>
          <button
            type="button"
            onclick={resetFilters}
            class="mt-1 inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
          >
            Clear all filters
          </button>
        </div>
      </div>
    {:else}
      <div class="divide-y divide-gray-50">
        {#each transactions as row}
          <div class="px-4 py-3.5">
            <!-- Top row: project name + price -->
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-gray-900 truncate leading-snug">
                  {row.project_name || 'Private'}
                </p>
                {#if row.district}
                  <p class="text-xs text-gray-400 mt-0.5 truncate">
                    <a href="{base}/area/{encodeURIComponent(row.district)}"
                       class="text-brand-600 hover:underline">{row.district}</a>
                    {#if row.community && row.community !== row.district}
                      <span class="text-gray-300 mx-1">›</span>{row.community}
                    {/if}
                  </p>
                {/if}
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-sm font-bold text-gray-900">{formatCurrency(row.price_aed)}</p>
                {#if row.rate_per_sqft}
                  <p class="text-xs text-gray-400 mt-0.5">
                    AED {formatRate(row.rate_per_sqft).replace(' AED/sqft', '')} /sqft
                  </p>
                {/if}
              </div>
            </div>

            <!-- Bottom row: meta chips -->
            <div class="mt-2 flex items-center gap-x-2 gap-y-1 flex-wrap">
              <span class="text-xs text-gray-400">{formatDate(row.sale_date)}</span>

              {#if row.layout && row.layout !== 'unclassified'}
                <span class="text-gray-200">·</span>
                <span class="text-xs text-gray-600">{formatLayout(row.layout)}</span>
              {/if}

              {#if row.area_sqft}
                <span class="text-gray-200">·</span>
                <span class="text-xs text-gray-500">{formatArea(row.area_sqft)} sqft</span>
              {/if}

              {#if row.sale_type}
                <span class="text-gray-200">·</span>
                <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium
                  {row.sale_type === 'off-plan' ? 'bg-brand-50 text-brand-700 border border-brand-200' :
                   row.sale_type === 'ready' ? 'bg-navy/5 text-navy border border-navy/20' :
                   'bg-gray-100 text-gray-600 border border-gray-200'}">
                  {row.sale_type === 'off-plan' ? 'Off-plan' :
                   row.sale_type === 'ready' ? 'Ready' :
                   row.sale_type.charAt(0).toUpperCase() + row.sale_type.slice(1)}
                </span>
              {/if}

              {#if row.sale_sequence}
                <span class="text-gray-200">·</span>
                <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium
                  {row.sale_sequence === 'primary'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-purple-50 text-purple-700 border border-purple-200'}">
                  {row.sale_sequence.charAt(0).toUpperCase() + row.sale_sequence.slice(1)}
                </span>
              {/if}

              {#if row.project_name && row.project_name.toLowerCase() !== 'private'}
                <a
                  href="{base}/project/{encodeURIComponent(row.project_name)}"
                  class="ml-auto text-xs font-medium text-brand-600 hover:text-brand-700 whitespace-nowrap"
                >
                  Explore →
                </a>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- ─── DESKTOP TABLE VIEW (md+) ────────────────────────────────────────── -->
  <div class={`hidden md:block overflow-x-auto${locked ? ' blur-md pointer-events-none select-none' : ''}`}>
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 bg-gray-50/60">
          {#each columns as col}
            <th
              class="px-4 py-3 text-[11px] font-semibold tracking-wider uppercase
                     {$filters.sortColumn === col.key ? 'text-brand-600' : 'text-gray-500'}
                     {col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                     {col.width || ''}
                     {col.sortable ? 'cursor-pointer select-none hover:text-brand-500 transition-colors group' : ''}"
              onclick={() => col.sortable && col.key && handleColumnSort(col.key)}
            >
              <span class="inline-flex items-center gap-1 {col.align === 'right' ? 'justify-end' : col.align === 'center' ? 'justify-center' : ''}">
                {#if col.subLabel && !col.label}
                  {col.subLabel}
                {:else}
                  {col.label}
                {/if}
                {#if col.sortable}
                  {#if $filters.sortColumn === col.key}
                    <svg class="h-3.5 w-3.5 text-brand-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      {#if $filters.sortDirection === 'asc'}
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                      {:else}
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      {/if}
                    </svg>
                  {:else}
                    <span class="flex flex-col gap-px opacity-30 group-hover:opacity-60 transition-opacity flex-shrink-0">
                      <svg class="h-2 w-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                      </svg>
                      <svg class="h-2 w-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </span>
                  {/if}
                {/if}
              </span>
            </th>
          {/each}
          <th class="px-4 py-3 w-[80px]"></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        {#if loading}
          {#each skeletonRows as _, i}
            <tr class="animate-pulse">
              {#each columns as col}
                <td class="px-4 py-4">
                  <div class="h-4 rounded bg-gray-100 {col.align === 'right' ? 'ml-auto w-20' : 'w-24'}"></div>
                </td>
              {/each}
              <td class="px-4 py-4"><div class="h-4 w-12 rounded bg-gray-100 ml-auto"></div></td>
            </tr>
          {/each}
        {:else if transactions.length === 0}
          <tr>
            <td colspan={columns.length + 1} class="px-4 py-16 text-center">
              <div class="flex flex-col items-center gap-3">
                <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                  <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-700">No transactions match these filters</p>
                  <p class="mt-1 text-xs text-gray-400">Try broadening the date range or removing a filter</p>
                </div>
                <button
                  type="button"
                  onclick={resetFilters}
                  class="mt-1 inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
                >
                  Clear all filters
                </button>
              </div>
            </td>
          </tr>
        {:else}
          {#each transactions as row, i}
            <tr class="hover:bg-gray-50/80 transition-colors">
              <!-- Date -->
              <td class="px-4 py-4 text-gray-500 whitespace-nowrap align-top">
                <div class="text-sm">{formatDate(row.sale_date)}</div>
              </td>

              <!-- Location: Project + Community > District -->
              <td class="px-4 py-4 align-top">
                <div class="text-sm font-medium text-gray-900">
                  {row.project_name || 'Private'}
                </div>
                <div class="text-xs text-gray-400 mt-0.5">
                  {#if row.community && row.district}
                    <a href="{base}/area/{encodeURIComponent(row.district)}" class="text-brand-600 hover:text-brand-700 hover:underline">{row.district}</a>
                    {#if row.community !== row.district}
                      <span class="text-gray-300 mx-1">&rsaquo;</span>
                      <span>{row.community}</span>
                    {/if}
                  {:else if row.district}
                    <a href="{base}/area/{encodeURIComponent(row.district)}" class="text-brand-600 hover:text-brand-700 hover:underline">{row.district}</a>
                  {/if}
                </div>
              </td>

              <!-- Price + Rate -->
              <td class="px-4 py-4 text-right align-top whitespace-nowrap">
                <div class="text-sm font-semibold text-gray-900">{formatCurrency(row.price_aed)}</div>
                {#if row.rate_per_sqft}
                  <div class="text-xs text-gray-400 mt-0.5">AED {formatRate(row.rate_per_sqft).replace(' AED/sqft', '')} /sqft</div>
                {/if}
              </td>

              <!-- Type -->
              <td class="px-4 py-4 text-center align-top">
                <span class="text-sm text-gray-700">{row.property_type}</span>
              </td>

              <!-- Beds / Layout -->
              <td class="px-4 py-4 text-center align-top">
                <span class="text-sm text-gray-700">{formatLayout(row.layout)}</span>
              </td>

              <!-- Built-up Area -->
              <td class="px-4 py-4 text-right align-top whitespace-nowrap">
                <span class="text-sm text-gray-700 tabular-nums">{row.area_sqft ? formatArea(row.area_sqft) : '-'}</span>
              </td>

              <!-- Sale Scenario -->
              <td class="px-4 py-4 text-center align-top">
                {#if row.sale_type}
                  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                    {row.sale_type === 'off-plan' ? 'bg-brand-50 text-brand-700 border border-brand-200' :
                     row.sale_type === 'ready' ? 'bg-navy/5 text-navy border border-navy/20' :
                     'bg-gray-100 text-gray-600 border border-gray-200'}">
                    {row.sale_type === 'off-plan' ? 'Off-plan' :
                     row.sale_type === 'ready' ? 'Ready' :
                     row.sale_type.charAt(0).toUpperCase() + row.sale_type.slice(1)}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>

              <!-- Sale Sequence -->
              <td class="px-4 py-4 text-center align-top">
                {#if row.sale_sequence}
                  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                    {row.sale_sequence === 'primary'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : row.sale_sequence === 'secondary'
                        ? 'bg-purple-50 text-purple-700 border border-purple-200'
                        : 'bg-gray-100 text-gray-600 border border-gray-200'}">
                    {row.sale_sequence.charAt(0).toUpperCase() + row.sale_sequence.slice(1)}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>

              <!-- Project link -->
              <td class="px-4 py-4 text-right align-top">
                {#if row.project_name && row.project_name.toLowerCase() !== 'private'}
                  <a
                    href="{base}/project/{encodeURIComponent(row.project_name)}"
                    title="Open project analytics for {row.project_name}"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-gray-200 text-xs font-medium text-gray-600 hover:border-brand-400 hover:text-brand-700 hover:bg-brand-50 transition-all whitespace-nowrap"
                  >
                    <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                    </svg>
                    Explore
                  </a>
                {/if}
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  </div><!-- end gated data rows -->

  <!-- Pagination -->
  {#if totalCount > 0}
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gray-200 bg-gray-50/50 px-4 py-3">
      <p class="text-sm text-gray-500 hidden sm:block">
        Showing <span class="font-medium text-gray-700">{showStart.toLocaleString()}</span>
        – <span class="font-medium text-gray-700">{showEnd.toLocaleString()}</span>
        of <span class="font-medium text-gray-700">{totalCount.toLocaleString()}</span>
      </p>
      <!-- Mobile: compact count -->
      <p class="text-xs text-gray-500 sm:hidden">
        {showStart}–{showEnd} of {totalCount.toLocaleString()}
      </p>

      <!-- Desktop: full pagination -->
      <nav class="hidden sm:inline-flex items-center gap-1">
        <button
          type="button"
          onclick={() => goToPage(currentPage - 1)}
          disabled={currentPage <= 1}
          class="inline-flex items-center justify-center rounded-md px-2 py-1.5 text-sm text-gray-500 hover:bg-white hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Prev
        </button>

        {#each paginationPages() as page}
          {#if page === '...'}
            <span class="px-2 py-1 text-sm text-gray-400">...</span>
          {:else}
            <button
              type="button"
              onclick={() => goToPage(page as number)}
              class="inline-flex items-center justify-center rounded-md min-w-[32px] px-2 py-1 text-sm font-medium transition-colors
                     {currentPage === page
                       ? 'bg-brand-600 text-white shadow-sm'
                       : 'text-gray-600 hover:bg-white hover:text-gray-900'}"
            >
              {page}
            </button>
          {/if}
        {/each}

        <button
          type="button"
          onclick={() => goToPage(currentPage + 1)}
          disabled={currentPage >= totalPages}
          class="inline-flex items-center justify-center rounded-md px-2 py-1.5 text-sm text-gray-500 hover:bg-white hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </nav>

      <!-- Mobile: compact prev / page / next -->
      <nav class="flex sm:hidden items-center gap-1">
        <button
          type="button"
          onclick={() => goToPage(currentPage - 1)}
          disabled={currentPage <= 1}
          class="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Prev
        </button>

        {#each mobilePaginationPages() as page}
          {#if page === '...'}
            <span class="px-1 text-sm text-gray-400">…</span>
          {:else}
            <button
              type="button"
              onclick={() => goToPage(page as number)}
              class="inline-flex items-center justify-center rounded-md min-w-[32px] px-2 py-1.5 text-sm font-medium transition-colors
                     {currentPage === page
                       ? 'bg-brand-600 text-white shadow-sm'
                       : 'text-gray-600 border border-gray-200 bg-white hover:bg-gray-50'}"
            >
              {page}
            </button>
          {/if}
        {/each}

        <button
          type="button"
          onclick={() => goToPage(currentPage + 1)}
          disabled={currentPage >= totalPages}
          class="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </nav>
    </div>
  {/if}
</div>
