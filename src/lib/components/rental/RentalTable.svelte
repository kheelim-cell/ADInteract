<script lang="ts">
  import type { RentalProjectRow } from '$lib/db/rental_types';
  import { resetRentalFilters } from '$lib/stores/rental_filters';
  import { m } from '$lib/paraglide/messages.js';

  let {
    rows,
    total,
    loading,
    page,
    pageSize,
    sortCol,
    sortDir,
    onSort,
    onSortFull,
    onPage
  }: {
    rows: RentalProjectRow[];
    total: number;
    loading: boolean;
    page: number;
    pageSize: number;
    sortCol: string;
    sortDir: 'asc' | 'desc';
    onSort: (col: string) => void;
    onSortFull: (col: string, dir: 'asc' | 'desc') => void;
    onPage: (p: number) => void;
  } = $props();

  const mobileSortOptions = [
    { value: 'median_rent:desc', label: m.rental_table_sort_median_desc() },
    { value: 'median_rent:asc',  label: m.rental_table_sort_median_asc() },
    { value: 'yoy_change:desc',  label: m.rental_table_sort_yoy_desc() },
    { value: 'yoy_change:asc',   label: m.rental_table_sort_yoy_asc() },
  ];

  let mobileSortValue = $derived(`${sortCol}:${sortDir}`);

  function handleMobileSortChange(e: Event) {
    const val = (e.target as HTMLSelectElement).value;
    const [col, dir] = val.split(':') as [string, 'asc' | 'desc'];
    onSortFull(col, dir);
  }

  function fmt(n: number | null): string {
    if (n === null || n === undefined) return '—';
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n).toLocaleString('en-US')}`;
    return `AED ${n}`;
  }

  function fmtYoY(n: number | null): string {
    if (n === null || n === undefined) return '—';
    return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
  }

  const totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));
  const showing = $derived({
    from: total === 0 ? 0 : (page - 1) * pageSize + 1,
    to:   Math.min(page * pageSize, total)
  });

  function sortArrow(col: string): string {
    if (sortCol !== col) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  }

  const HEADERS: { label: string; col: string; align: string }[] = [
    { label: m.rental_table_col_project(),  col: 'project_name', align: 'left'  },
    { label: m.rental_table_col_district(), col: 'district',     align: 'left'  },
    { label: m.rental_table_col_type(),     col: 'typology',     align: 'left'  },
    { label: m.rental_table_col_layout(),   col: 'layout',       align: 'left'  },
    { label: m.rental_table_col_lower(),    col: 'lower_rent',   align: 'right' },
    { label: m.rental_table_col_median(),   col: 'median_rent',  align: 'right' },
    { label: m.rental_table_col_upper(),    col: 'upper_rent',   align: 'right' },
    { label: m.rental_table_col_yoy(),      col: 'yoy_change',   align: 'right' }
  ];

  // Mobile page numbers
  function mobilePaginationPages(): (number | '…')[] {
    if (totalPages <= 5) return Array.from({ length: totalPages }, (_, i) => i + 1);
    const pages: (number | '…')[] = [1];
    if (page > 3) pages.push('…');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push('…');
    if (totalPages > 1) pages.push(totalPages);
    return pages;
  }
</script>

<div class="rounded-2xl bg-white shadow-sm ring-1 ring-black/5 overflow-hidden">

  <!-- Header row -->
  <div class="px-4 sm:px-6 py-4 border-b border-gray-100 flex items-center justify-between gap-4">
    <div>
      <h3 class="text-sm font-semibold text-navy">{m.rental_table_title()}</h3>
      {#if !loading}
        <p class="text-xs text-gray-400 mt-0.5">
          {m.rental_table_showing({ from: String(showing.from), to: String(showing.to), total: total.toLocaleString('en-US') })}
        </p>
      {/if}
    </div>
    <!-- Mobile sort dropdown (hidden on md+, desktop sorts via column headers) -->
    <div class="flex md:hidden items-center gap-2 flex-shrink-0">
      <select
        value={mobileSortValue}
        onchange={handleMobileSortChange}
        class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        {#each mobileSortOptions as opt}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>
  </div>

  <!-- Desktop table -->
  <div class="hidden md:block overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-gray-50 border-b border-gray-100">
          {#each HEADERS as h}
            <th
              class="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-400 cursor-pointer hover:text-gray-700 whitespace-nowrap
                     {h.align === 'right' ? 'text-end' : 'text-start'}"
              onclick={() => onSort(h.col)}
            >
              {h.label}{sortArrow(h.col)}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        {#if loading}
          {#each Array(5) as _}
            <tr class="animate-pulse">
              {#each HEADERS as _}
                <td class="px-4 py-3">
                  <div class="h-3.5 bg-gray-100 rounded w-24"></div>
                </td>
              {/each}
            </tr>
          {/each}
        {:else if rows.length === 0}
          <tr>
            <td colspan={HEADERS.length} class="px-4 py-16 text-center">
              <div class="flex flex-col items-center gap-3">
                <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                  <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-700">{m.rental_no_results_title()}</p>
                  <p class="mt-1 text-xs text-gray-400">{m.rental_no_results_sub()}</p>
                </div>
                <button
                  type="button"
                  onclick={resetRentalFilters}
                  class="mt-1 inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
                >
                  {m.rental_clear_all_filters()}
                </button>
              </div>
            </td>
          </tr>
        {:else}
          {#each rows as row}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-900 max-w-[220px] truncate">{row.project_name}</td>
              <td class="px-4 py-3 text-gray-600 whitespace-nowrap">{row.district}</td>
              <td class="px-4 py-3 text-gray-500 whitespace-nowrap capitalize">{row.typology || '—'}</td>
              <td class="px-4 py-3 text-gray-500 whitespace-nowrap capitalize">{row.layout}</td>
              <td class="px-4 py-3 text-end text-gray-600 whitespace-nowrap">{fmt(row.lower_rent)}</td>
              <td class="px-4 py-3 text-end font-semibold text-gray-900 whitespace-nowrap">{fmt(row.median_rent)}</td>
              <td class="px-4 py-3 text-end text-gray-600 whitespace-nowrap">{fmt(row.upper_rent)}</td>
              <td class="px-4 py-3 text-end whitespace-nowrap">
                {#if row.yoy_change !== null && row.yoy_change !== undefined}
                  <span class="inline-flex items-center gap-1 text-xs font-semibold rounded-full px-2 py-0.5
                               {row.yoy_change > 0
                                 ? 'bg-emerald-50 text-emerald-700'
                                 : row.yoy_change < 0
                                 ? 'bg-red-50 text-red-700'
                                 : 'bg-gray-50 text-gray-500'}">
                    {fmtYoY(row.yoy_change)}
                  </span>
                {:else}
                  <span class="text-gray-300 text-xs">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <!-- Mobile cards -->
  <div class="block md:hidden">
    {#if loading}
      {#each Array(5) as _}
        <div class="px-4 py-3.5 border-b border-gray-50 animate-pulse">
          <div class="flex justify-between gap-3">
            <div class="h-4 bg-gray-100 rounded w-36 mb-2"></div>
            <div class="h-4 bg-gray-100 rounded w-20"></div>
          </div>
          <div class="h-3 bg-gray-100 rounded w-24"></div>
        </div>
      {/each}
    {:else if rows.length === 0}
      <div class="px-4 py-16 flex flex-col items-center gap-3 text-center">
        <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
          <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
          </svg>
        </div>
        <div>
          <p class="text-sm font-semibold text-gray-700">No rental listings match these filters</p>
          <p class="mt-1 text-xs text-gray-400">Try broadening the year range or removing a filter</p>
        </div>
        <button
          type="button"
          onclick={resetRentalFilters}
          class="mt-1 inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          Clear all filters
        </button>
      </div>
    {:else}
      <div class="divide-y divide-gray-50">
        {#each rows as row}
          <div class="px-4 py-3.5">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-gray-900 truncate">{row.project_name}</p>
                <p class="text-xs text-gray-400 mt-0.5">
                  {row.district}{row.typology ? ` · ${row.typology}` : ''} · <span class="capitalize">{row.layout}</span>
                </p>
              </div>
              <div class="text-end flex-shrink-0">
                <p class="text-sm font-bold text-gray-900">{fmt(row.median_rent)}</p>
                <p class="text-xs text-gray-400">{m.rental_table_median_per_year()}</p>
              </div>
            </div>
            <div class="mt-1.5 flex items-center gap-2 text-xs text-gray-500 flex-wrap">
              {#if row.lower_rent !== null}
                <span>{fmt(row.lower_rent)} – {fmt(row.upper_rent)}</span>
              {/if}
              {#if row.yoy_change !== null && row.yoy_change !== undefined}
                <span class="inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold
                             {row.yoy_change > 0 ? 'bg-emerald-50 text-emerald-700' : row.yoy_change < 0 ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-500'}">
                  {fmtYoY(row.yoy_change)} {m.rental_table_yoy_suffix()}
                </span>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="px-4 sm:px-6 py-3 border-t border-gray-100 flex items-center justify-between gap-4">
      <span class="text-xs text-gray-400 hidden sm:block">
        {m.rental_table_page_of({ page: String(page), totalPages: String(totalPages) })}
      </span>
      <div class="flex items-center gap-1 mx-auto sm:mx-0">
        <button
          type="button"
          onclick={() => onPage(page - 1)}
          disabled={page <= 1}
          class="rounded-lg px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {m.rental_table_prev()}
        </button>
        {#each mobilePaginationPages() as p}
          {#if p === '…'}
            <span class="px-2 text-gray-400 text-xs">…</span>
          {:else}
            <button
              type="button"
              onclick={() => onPage(p as number)}
              class="rounded-lg w-8 h-8 text-xs font-medium transition-colors
                     {page === p ? 'bg-brand-600 text-white' : 'text-gray-600 hover:bg-gray-100'}"
            >
              {p}
            </button>
          {/if}
        {/each}
        <button
          type="button"
          onclick={() => onPage(page + 1)}
          disabled={page >= totalPages}
          class="rounded-lg px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {m.rental_table_next()}
        </button>
      </div>
    </div>
  {/if}

</div>
