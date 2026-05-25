<script lang="ts">
  import { filters, updateFilter, dateRangeMs } from '$lib/stores/filters';
  import type { Transaction } from '$lib/db/types';
  import { formatDate, formatNumber, formatCurrency, formatArea, formatRate } from '$lib/utils/format';
  import { exportTransactions } from '$lib/db/queries';
  import { base } from '$app/paths';

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
    { key: 'sale_type', label: 'SALE SCENARIO', sortable: true, align: 'center', width: 'w-[130px]' },
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

  function formatSaleSequence(seq: string): string {
    if (!seq) return '-';
    return seq.charAt(0).toUpperCase() + seq.slice(1);
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

  const skeletonRows = Array.from({ length: 10 });
</script>

<div class="rounded-2xl bg-white shadow-sm border border-white/80 overflow-hidden">
  <!-- Sort bar -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
    <div class="flex items-center gap-3">
      <label for="sort-select" class="text-sm text-gray-500">Sort by</label>
      <select
        id="sort-select"
        value={currentSort}
        onchange={handleSortChange}
        class="text-sm font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
      >
        {#each sortOptions as opt}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>
    {#if totalCount > 0}
      <div class="flex items-center gap-3">
        <span class="text-sm text-gray-500">
          {totalCount.toLocaleString()} transactions
        </span>
        <button
          type="button"
          onclick={handleExport}
          disabled={exporting || loading}
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-600 shadow-sm transition-colors hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#if exporting}
            <svg class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Exporting...
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export CSV
          {/if}
        </button>
      </div>
    {/if}
  </div>

  <!-- Table -->
  <div class="overflow-x-auto">
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
                    <!-- Active: solid directional arrow in gold -->
                    <svg class="h-3.5 w-3.5 text-brand-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      {#if $filters.sortDirection === 'asc'}
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                      {:else}
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                      {/if}
                    </svg>
                  {:else}
                    <!-- Inactive: muted up/down arrows showing column is sortable -->
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
              <div class="flex flex-col items-center gap-2">
                <svg class="h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="text-sm text-gray-500 font-medium">No transactions found</p>
                <p class="text-xs text-gray-400">Try adjusting your filters</p>
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

  <!-- Pagination -->
  {#if totalCount > 0}
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gray-200 bg-gray-50/50 px-4 py-3">
      <p class="text-sm text-gray-500">
        Showing <span class="font-medium text-gray-700">{showStart.toLocaleString()}</span>
        - <span class="font-medium text-gray-700">{showEnd.toLocaleString()}</span>
        of <span class="font-medium text-gray-700">{totalCount.toLocaleString()}</span>
      </p>

      <nav class="inline-flex items-center gap-1">
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
    </div>
  {/if}
</div>
