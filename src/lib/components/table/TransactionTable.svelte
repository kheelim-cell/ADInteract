<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';
  import type { Transaction } from '$lib/db/types';
  import { formatDate, formatNumber, formatCurrency, formatArea, formatRate } from '$lib/utils/format';
  import { base } from '$app/paths';

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
    { key: 'area_sqft', label: 'AREA (SQFT)', subLabel: 'BUILT-UP', sortable: true, align: 'right', width: 'w-[110px]' },
    { key: 'land_area_sqft', label: '', subLabel: 'PLOT', sortable: true, align: 'right', width: 'w-[100px]' },
    { key: 'sale_sequence', label: 'SEQUENCE', sortable: true, align: 'center', width: 'w-[100px]' },
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

<div class="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
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
      <span class="text-sm text-gray-500">
        {totalCount.toLocaleString()} transactions
      </span>
    {/if}
  </div>

  <!-- Table -->
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 bg-gray-50/60">
          {#each columns as col}
            <th
              class="px-4 py-3 text-[11px] font-semibold tracking-wider text-gray-400 uppercase
                     {col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                     {col.width || ''}
                     {col.sortable ? 'cursor-pointer select-none hover:text-gray-600 transition-colors' : ''}"
              onclick={() => col.sortable && col.key && handleColumnSort(col.key)}
            >
              <span class="inline-flex items-center gap-1 {col.align === 'right' ? 'justify-end' : col.align === 'center' ? 'justify-center' : ''}">
                {#if col.subLabel && !col.label}
                  {col.subLabel}
                {:else}
                  {col.label}
                {/if}
                {#if col.sortable && $filters.sortColumn === col.key}
                  <svg class="h-3 w-3 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    {#if $filters.sortDirection === 'asc'}
                      <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                    {:else}
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                    {/if}
                  </svg>
                {/if}
              </span>
            </th>
          {/each}
          <th class="px-4 py-3 w-[80px]"></th>
        </tr>
        <!-- Area sub-header row -->
        <tr class="border-b border-gray-100 bg-gray-50/40">
          {#each columns as col}
            <th class="px-4 py-1 text-[10px] font-medium tracking-wider text-gray-300 uppercase
                       {col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                       {col.width || ''}">
              {#if col.subLabel && col.label}
                {col.subLabel}
              {/if}
            </th>
          {/each}
          <th class="px-4 py-1 w-[80px]"></th>
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

              <!-- Plot Area -->
              <td class="px-4 py-4 text-right align-top whitespace-nowrap">
                <span class="text-sm text-gray-700 tabular-nums">{row.land_area_sqft ? formatArea(row.land_area_sqft) : '-'}</span>
              </td>

              <!-- Sequence -->
              <td class="px-4 py-4 text-center align-top">
                <span class="text-sm text-gray-700">{formatSaleSequence(row.sale_sequence)}</span>
              </td>

              <!-- View Button -->
              <td class="px-4 py-4 text-right align-top">
                {#if row.project_name && row.project_name.toLowerCase() !== 'private'}
                  <a
                    href="{base}/project/{encodeURIComponent(row.project_name)}"
                    class="inline-flex items-center px-3 py-1 rounded-md border border-brand-600 text-xs font-semibold text-brand-600 hover:bg-brand-50 transition-colors"
                  >
                    VIEW
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
