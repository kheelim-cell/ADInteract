<script lang="ts">
  import { base } from '$app/paths';
  import { onMount } from 'svelte';

  interface Project {
    project_name: string;
    project_number: string;
    district: string;
    developer_name: string;
    category: string;
    sc_avg: number | null;
    sc_min: number | null;
    sc_max: number | null;
    latest_year: number | null;
    primary_fee: number | null;
  }

  let projects: Project[] = $state([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let lastUpdated = $state('');

  // ── Filters ────────────────────────────────────────────────────────────────
  let filterDistrict = $state('');
  let searchQuery    = $state('');

  // ── Sort ───────────────────────────────────────────────────────────────────
  let sortCol: 'project_name' | 'district' | 'developer_name' | 'sc_avg' = $state('sc_avg');
  let sortDir = $state<'asc' | 'desc'>('desc');

  function setSort(col: typeof sortCol) {
    if (sortCol === col) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortCol = col;
      sortDir = col === 'project_name' || col === 'district' || col === 'developer_name' ? 'asc' : 'desc';
    }
  }

  // ── Derived ────────────────────────────────────────────────────────────────
  let districts = $derived(
    [...new Set(projects.map(p => p.district))].filter(Boolean).sort()
  );

  let filtered = $derived(() => {
    let rows = projects;

    if (filterDistrict) {
      rows = rows.filter(p => p.district === filterDistrict);
    }
    if (searchQuery.trim().length >= 2) {
      const q = searchQuery.trim().toLowerCase();
      rows = rows.filter(p =>
        p.project_name.toLowerCase().includes(q) ||
        p.developer_name.toLowerCase().includes(q) ||
        p.district.toLowerCase().includes(q)
      );
    }

    // Sort
    rows = [...rows].sort((a, b) => {
      let av: string | number | null;
      let bv: string | number | null;
      if (sortCol === 'project_name')   { av = a.project_name;   bv = b.project_name; }
      else if (sortCol === 'district')  { av = a.district;        bv = b.district; }
      else if (sortCol === 'developer_name') { av = a.developer_name; bv = b.developer_name; }
      else                              { av = a.sc_avg;          bv = b.sc_avg; }

      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });

    return rows;
  });

  // ── Formatting ─────────────────────────────────────────────────────────────
  function toTitleCase(str: string): string {
    return str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }

  function fmtFee(n: number | null): string {
    if (n === null || n === undefined) return '—';
    return n.toFixed(2);
  }

  function feeBadge(fee: number | null): string {
    if (fee === null) return 'bg-gray-100 text-gray-400';
    if (fee >= 20) return 'bg-red-100 text-red-700';
    if (fee >= 10) return 'bg-amber-50 text-amber-700';
    if (fee >= 5)  return 'bg-brand-50 text-brand-700';
    return 'bg-emerald-100 text-emerald-800';
  }

  function sortIcon(col: string): string {
    if (sortCol !== col) return '↕';
    return sortDir === 'asc' ? '↑' : '↓';
  }

  let hasFilter = $derived(!!(filterDistrict || searchQuery.trim()));

  function resetFilters() {
    filterDistrict = '';
    searchQuery    = '';
  }

  const INITIAL_LIMIT = 10;
  let expanded = $state(false);
  let visibleRows = $derived(expanded ? filtered() : filtered().slice(0, INITIAL_LIMIT));

  // Collapse when filters change
  $effect(() => {
    filterDistrict; searchQuery;
    expanded = false;
  });

  // ── Load data ──────────────────────────────────────────────────────────────
  onMount(async () => {
    try {
      const res = await fetch(`${base}/data/service_charges.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      projects    = json.projects ?? [];
      lastUpdated = json.last_updated ?? '';
    } catch (e) {
      error = 'Failed to load service charge data.';
    } finally {
      loading = false;
    }
  });

  const thClass  = 'px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400 cursor-pointer select-none hover:text-gray-600 transition-colors whitespace-nowrap';
  const thRClass = 'px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400 cursor-pointer select-none hover:text-gray-600 transition-colors whitespace-nowrap';
</script>

<div class="rounded-2xl bg-white shadow-sm ring-1 ring-black/5 overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-gray-100">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h3 class="text-sm font-bold text-navy">Service Charges by Project</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          Annual service charge fees (AED/sqft) · Source: ADREC
          {#if lastUpdated}· Updated {lastUpdated}{/if}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2 flex-shrink-0">
        <!-- Search -->
        <div class="relative">
          <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search project or developer…"
            bind:value={searchQuery}
            class="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 min-w-[180px]"
          />
        </div>

        <!-- District filter -->
        <select
          bind:value={filterDistrict}
          class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Districts</option>
          {#each districts as d}
            <option value={d}>{d}</option>
          {/each}
        </select>

        {#if hasFilter}
          <button
            type="button"
            onclick={resetFilters}
            class="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
          >
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
            Clear
          </button>
        {/if}
      </div>
    </div>
  </div>

  <!-- Error state -->
  {#if error}
    <div class="px-5 py-10 text-center text-sm text-red-500">{error}</div>

  <!-- Desktop table -->
  {:else}
    <div class="hidden md:block">
      <table class="w-full text-sm table-fixed">
        <colgroup>
          <col class="w-[40%]" />
          <col class="w-[22%]" />
          <col class="w-[28%]" />
          <col class="w-[10%]" />
        </colgroup>
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class={thClass} onclick={() => setSort('project_name')}>
              Project {sortIcon('project_name')}
            </th>
            <th class={thClass} onclick={() => setSort('district')}>
              District {sortIcon('district')}
            </th>
            <th class={thClass} onclick={() => setSort('developer_name')}>
              Developer {sortIcon('developer_name')}
            </th>
            <th class={thRClass} onclick={() => setSort('sc_avg')}>
              AED/sqft {sortIcon('sc_avg')}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">

          {#if loading}
            {#each Array(8) as _}
              <tr class="animate-pulse">
                {#each Array(4) as _}
                  <td class="px-5 py-3.5"><div class="h-3.5 rounded bg-gray-100 w-20"></div></td>
                {/each}
              </tr>
            {/each}

          {:else if filtered().length === 0}
            <tr>
              <td colspan="4" class="px-5 py-16 text-center text-sm text-gray-400">
                No projects match the current filters.
              </td>
            </tr>

          {:else}
            {#each visibleRows as project}
              <tr class="hover:bg-gray-50/80 transition-colors">
                <td class="px-5 py-3.5">
                  <p class="font-medium text-gray-900 text-sm truncate" title={toTitleCase(project.project_name)}>
                    {toTitleCase(project.project_name)}
                  </p>
                  {#if project.project_number}
                    <p class="text-xs text-gray-400 tabular-nums mt-0.5">#{project.project_number}</p>
                  {/if}
                </td>
                <td class="px-5 py-3.5">
                  <a
                    href="{base}/area/{encodeURIComponent(project.district)}"
                    class="text-brand-600 hover:text-brand-700 hover:underline text-sm truncate block"
                    title={project.district}
                  >
                    {project.district}
                  </a>
                </td>
                <td class="px-5 py-3.5">
                  <p class="text-sm text-gray-600 truncate" title={project.developer_name}>
                    {project.developer_name}
                  </p>
                </td>
                <td class="px-5 py-3.5 text-right">
                  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold tabular-nums {feeBadge(project.sc_avg)}">
                    {fmtFee(project.sc_avg)}
                  </span>
                </td>
              </tr>
            {/each}
          {/if}

        </tbody>
      </table>

      {#if !loading && filtered().length > INITIAL_LIMIT}
        <button
          type="button"
          onclick={() => (expanded = !expanded)}
          class="w-full py-3 border-t border-gray-100 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1.5"
        >
          {#if expanded}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" /></svg>
            Show fewer
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
            Show all {filtered().length} projects
          {/if}
        </button>
      {:else if !loading && filtered().length > 0}
        <div class="px-5 py-3 border-t border-gray-50 text-xs text-gray-400">
          {filtered().length} project{filtered().length === 1 ? '' : 's'}
          {#if filterDistrict || searchQuery.trim()} matching filters{/if}
        </div>
      {/if}
    </div>

    <!-- Mobile cards -->
    <div class="block md:hidden">
      {#if loading}
        {#each Array(6) as _}
          <div class="px-4 py-4 border-b border-gray-50 animate-pulse space-y-2.5">
            <div class="flex justify-between">
              <div class="h-4 w-40 bg-gray-100 rounded"></div>
              <div class="h-6 w-16 bg-gray-100 rounded-full"></div>
            </div>
            <div class="h-3 w-28 bg-gray-100 rounded"></div>
            <div class="h-3 w-20 bg-gray-100 rounded"></div>
          </div>
        {/each}

      {:else if filtered().length === 0}
        <div class="px-4 py-12 text-center text-sm text-gray-400">No projects match the current filters.</div>

      {:else}
        <div class="divide-y divide-gray-50">
          {#each visibleRows as project}
            <div class="px-4 py-4">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-gray-900 truncate" title={toTitleCase(project.project_name)}>
                    {toTitleCase(project.project_name)}
                  </p>
                  <a
                    href="{base}/area/{encodeURIComponent(project.district)}"
                    class="text-xs text-brand-600 hover:underline mt-0.5 block"
                  >
                    {project.district}
                  </a>
                  <p class="text-xs text-gray-400 mt-0.5 truncate" title={project.developer_name}>
                    {project.developer_name}
                  </p>
                </div>
                <div class="flex-shrink-0 text-right">
                  <span class="inline-flex items-center rounded-full px-3 py-1.5 text-sm font-bold tabular-nums {feeBadge(project.sc_avg)}">
                    {fmtFee(project.sc_avg)}
                  </span>
                  <p class="text-xs text-gray-400 mt-1">AED/sqft</p>
                </div>
              </div>
            </div>
          {/each}
        </div>

        {#if filtered().length > INITIAL_LIMIT}
          <button
            type="button"
            onclick={() => (expanded = !expanded)}
            class="w-full py-3 border-t border-gray-100 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1.5"
          >
            {#if expanded}
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" /></svg>
              Show fewer
            {:else}
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
              Show all {filtered().length} projects
            {/if}
          </button>
        {/if}
      {/if}
    </div>
  {/if}

</div>
