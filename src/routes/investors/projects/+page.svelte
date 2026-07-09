<script lang="ts">
  import { base } from '$app/paths';
  import { m } from '$lib/paraglide/messages.js';
  import { metadata, dbReady } from '$lib/stores/db';
  import { query } from '$lib/db/duckdb';
  import ShareToolButton from '$lib/components/ui/ShareToolButton.svelte';
  import WatchlistButton from '$lib/components/investors/WatchlistButton.svelte';

  let search = $state('');
  let districtFilter = $state('');

  interface ProjectRow {
    project_name: string;
    district: string;
    tx_count: number;
    median_psf: number | null;
    offplan_pct: number;
    last_sale: string;
  }

  let allRows = $state<ProjectRow[]>([]);
  let loading = $state(false);
  let loaded = $state(false);

  async function loadAll() {
    if (!$dbReady || loaded) return;
    loading = true;
    try {
      const rows = await query<{
        project_name: string;
        district: string;
        tx_count: number;
        median_psf: number | null;
        offplan_pct: number;
        last_sale: string;
      }>(`
        SELECT
          project_name,
          ANY_VALUE(district) AS district,
          COUNT(*) AS tx_count,
          ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft > 0), 0) AS median_psf,
          ROUND(SUM(CASE WHEN sale_type = 'off-plan' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 0) AS offplan_pct,
          MAX(sale_date::VARCHAR) AS last_sale
        FROM transactions
        WHERE project_name IS NOT NULL AND project_name != ''
          AND LOWER(project_name) != 'private'
        GROUP BY project_name
        ORDER BY tx_count DESC
      `);
      allRows = rows.map(r => ({
        project_name: r.project_name,
        district: r.district,
        tx_count: Number(r.tx_count),
        median_psf: r.median_psf,
        offplan_pct: Number(r.offplan_pct),
        last_sale: r.last_sale,
      }));
      loaded = true;
    } finally {
      loading = false;
    }
  }

  $effect(() => { if ($dbReady) loadAll(); });

  let districts = $derived([...new Set(allRows.map(r => r.district).filter(Boolean))].sort());

  let filtered = $derived(
    allRows.filter(r => {
      const q = search.toLowerCase().trim();
      if (q && !r.project_name.toLowerCase().includes(q)) return false;
      if (districtFilter && r.district !== districtFilter) return false;
      return true;
    })
  );

  const PAGE_SIZE = 50;
  let page = $state(1);
  let paginated = $derived(filtered.slice(0, page * PAGE_SIZE));
  let hasMore = $derived(filtered.length > paginated.length);

  function fmt(n: number) { return n.toLocaleString('en-AE'); }
  function fmtDate(s: string) { return s ? s.slice(0, 7) : '—'; }
</script>

<svelte:head>
  <title>{m.seo_projects_title()}</title>
  <meta name="description" content={m.seo_projects_description()} />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <h1 class="text-xl font-bold text-gray-900 mb-1">{m.projects_page_title()}</h1>
      <p class="text-sm text-gray-500">{m.projects_page_subtitle({ count: String(allRows.length) })}</p>
    </div>
    <ShareToolButton />
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3 mb-6">
    <input
      type="text"
      bind:value={search}
      oninput={() => { page = 1; }}
      placeholder={m.projects_search_placeholder()}
      class="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50"
    />
    <select
      bind:value={districtFilter}
      onchange={() => { page = 1; }}
      class="rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-400 bg-white"
    >
      <option value="">{m.projects_filter_district()}</option>
      {#each districts as d}
        <option value={d}>{d}</option>
      {/each}
    </select>
  </div>

  {#if loading}
    <div class="flex items-center gap-2 text-sm text-gray-500 py-8">
      <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
      </svg>
      {m.projects_loading()}
    </div>
  {:else if filtered.length === 0}
    <p class="text-sm text-gray-500 py-8 text-center">{m.projects_no_results()}</p>
  {:else}
    <div class="rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-4 py-3 text-start text-[11px] font-semibold text-gray-500 uppercase tracking-wider">{m.projects_th_project()}</th>
            <th class="px-4 py-3 text-start text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">{m.projects_th_district()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider">{m.projects_th_tx_count()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">{m.projects_th_median_psf()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">{m.projects_th_offplan_pct()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">{m.projects_th_last_sale()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          {#each paginated as r}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-gray-900 text-sm leading-snug">{r.project_name}</span>
                  <span class="hidden sm:inline text-xs text-gray-400">{r.district}</span>
                </div>
                <span class="sm:hidden text-xs text-gray-400">{r.district}</span>
              </td>
              <td class="px-4 py-3 text-gray-500 hidden sm:table-cell">{r.district}</td>
              <td class="px-4 py-3 text-end font-semibold text-gray-700">{fmt(r.tx_count)}</td>
              <td class="px-4 py-3 text-end text-gray-600 hidden md:table-cell">{r.median_psf != null ? fmt(r.median_psf) : '—'}</td>
              <td class="px-4 py-3 text-end hidden md:table-cell">
                <span class="text-xs font-semibold {r.offplan_pct >= 50 ? 'text-blue-700' : 'text-gray-500'}">{r.offplan_pct}%</span>
              </td>
              <td class="px-4 py-3 text-end text-gray-400 text-xs hidden lg:table-cell">{fmtDate(r.last_sale)}</td>
              <td class="px-4 py-3 text-end">
                <div class="flex items-center justify-end gap-1.5">
                  <WatchlistButton project_name={r.project_name} district={r.district} />
                  <a
                    href="{base}/project/{encodeURIComponent(r.project_name)}"
                    class="text-xs font-semibold text-emerald-600 hover:text-emerald-800"
                  >{m.projects_view()}</a>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
      {#if hasMore}
        <div class="px-4 py-3 border-t border-gray-100 bg-gray-50 text-center">
          <button
            type="button"
            onclick={() => { page++; }}
            class="text-sm font-semibold text-emerald-600 hover:text-emerald-800"
          >
            Load more ({filtered.length - paginated.length} remaining)
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>
