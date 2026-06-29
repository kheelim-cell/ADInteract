<script lang="ts">
  import rawPipeline from '$lib/data/project_pipeline.json';
  import { m } from '$lib/paraglide/messages.js';

  type ProjectRow = {
    slug: string;
    project_name: string;
    district: string | null;
    registered_sales_alltime: number;
    sales_last_90d: number;
    sales_prior_90d: number;
    momentum_pct: number | null;
    status: 'accelerating' | 'new_launch' | 'steady' | 'slowing' | 'stale';
    days_since_last_sale: number;
    first_sale_date: string;
    last_sale_date: string;
    median_price_aed: number | null;
    median_psf: number | null;
    completion_pct: number | null;
    property_type: string | null;
    classification: string | null;
    construction_status: string | null;
    image_url: string | null;
  };

  type Pipeline = {
    generated_at: string;
    as_of_date: string;
    project_count: number;
    total_registered_sales_alltime: number;
    projects: ProjectRow[];
  };

  const data = rawPipeline as Pipeline;

  let filterDistrict = $state('');
  let filterStatus = $state('');

  const districts = [...new Set(data.projects.map(p => p.district).filter(Boolean))].sort() as string[];

  let filtered = $derived(
    data.projects.filter(p =>
      (!filterDistrict || p.district === filterDistrict) &&
      (!filterStatus || p.status === filterStatus)
    )
  );

  let hasFilter = $derived(!!(filterDistrict || filterStatus));

  function resetFilters() {
    filterDistrict = '';
    filterStatus = '';
  }

  function fmt(n: number | null) {
    if (n == null) return '—';
    return n.toLocaleString('en-AE');
  }

  function statusMeta(status: ProjectRow['status']) {
    if (status === 'accelerating') return { label: m.pipeline_status_accelerating(), cls: 'bg-emerald-100 text-emerald-800' };
    if (status === 'new_launch')   return { label: m.pipeline_status_new_launch(),   cls: 'bg-blue-100 text-blue-800' };
    if (status === 'slowing')      return { label: m.pipeline_status_slowing(),      cls: 'bg-amber-100 text-amber-800' };
    if (status === 'stale')        return { label: m.pipeline_status_stale(),        cls: 'bg-gray-100 text-gray-500' };
    return                                 { label: m.pipeline_status_steady(),      cls: 'bg-violet-100 text-violet-800' };
  }

  const accelerating = data.projects.filter(p => p.status === 'accelerating').length;
  const stale = data.projects.filter(p => p.status === 'stale').length;

  function constructionMeta(status: string | null) {
    if (status === 'Built') return { label: m.pipeline_construction_ready(), cls: 'bg-emerald-500' };
    if (status === 'Ready') return { label: m.pipeline_construction_ready(), cls: 'bg-emerald-500' };
    return { label: m.pipeline_construction_underway(), cls: 'bg-amber-500' };
  }
</script>

<svelte:head>
  <title>Abu Dhabi Off-Plan Project Pipeline — Registered Sales Velocity | ADInteract</title>
  <meta name="description" content="Off-plan project pipeline for Abu Dhabi: registered-sales velocity per project, recent vs prior 90-day momentum, and days since last registration. Sourced from ADREC transaction data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <div class="mb-2">
    <h1 class="text-xl font-bold text-gray-900 mb-1">{m.pipeline_page_title()}</h1>
    <p class="text-sm text-gray-500 max-w-2xl">
      {m.pipeline_page_intro({ count: String(data.project_count), date: data.as_of_date })}
    </p>
  </div>

  <!-- ── Honesty note — what this is and isn't ─────────────────────────── -->
  <div class="rounded-2xl bg-gradient-to-r from-[#0a2318]/5 to-emerald-50 border border-emerald-100 px-5 py-4">
    <div class="flex items-start gap-3">
      <div class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-emerald-100">
        <svg class="h-4.5 w-4.5 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
      </div>
      <div>
        <p class="text-sm font-semibold text-gray-800">{m.pipeline_honesty_title()}</p>
        <p class="mt-0.5 text-xs leading-relaxed text-gray-500">
          {m.pipeline_honesty_part1()} <strong class="text-gray-700">{m.pipeline_honesty_velocity()}</strong>{m.pipeline_honesty_part2()} <strong class="text-gray-700">{m.pipeline_honesty_window()}</strong> {m.pipeline_honesty_part3()} <strong class="text-gray-700">{m.pipeline_honesty_last_sale()}</strong> {m.pipeline_honesty_part4()}
        </p>
      </div>
    </div>
  </div>

  <!-- ── KPI strip ──────────────────────────────────────────────────────── -->
  <div class="flex flex-wrap items-center gap-x-8 gap-y-2 rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm shadow-sm">
    <div class="flex items-center gap-2">
      <span class="text-gray-500">{m.pipeline_kpi_projects_tracked()}</span>
      <span class="font-semibold text-gray-900">{data.project_count}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">{m.pipeline_kpi_alltime_sales()}</span>
      <span class="font-semibold text-gray-900">{fmt(data.total_registered_sales_alltime)}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">{m.pipeline_kpi_accelerating()}</span>
      <span class="font-semibold text-emerald-700">{accelerating}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">{m.pipeline_kpi_stale()}</span>
      <span class="font-semibold text-gray-500">{stale}</span>
    </div>
  </div>

  <!-- ── Filters ────────────────────────────────────────────────────────── -->
  <div class="flex flex-wrap items-center gap-3">
    <select bind:value={filterDistrict} class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]">
      <option value="">{m.calc_district_all()}</option>
      {#each districts as d}
        <option value={d}>{d}</option>
      {/each}
    </select>

    <select bind:value={filterStatus} class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]">
      <option value="">{m.pipeline_all_statuses()}</option>
      <option value="accelerating">{m.pipeline_status_accelerating()}</option>
      <option value="new_launch">{m.pipeline_status_new_launch()}</option>
      <option value="steady">{m.pipeline_status_steady()}</option>
      <option value="slowing">{m.pipeline_status_slowing()}</option>
      <option value="stale">{m.pipeline_status_stale()}</option>
    </select>

    {#if hasFilter}
      <button
        type="button"
        onclick={resetFilters}
        class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
        {m.pipeline_clear_filters()}
      </button>
    {/if}

    <span class="text-xs text-gray-400 ms-auto">{m.pipeline_filtered_count({ filtered: String(filtered.length), total: String(data.project_count) })}</span>
  </div>

  <!-- ── Project card grid ─────────────────────────────────────────────── -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {#each filtered as p}
      {@const s = statusMeta(p.status)}
      {@const c = constructionMeta(p.construction_status)}
      <div class="group rounded-2xl border border-gray-200 bg-white overflow-hidden hover:shadow-md hover:border-gray-300 transition-all flex flex-col">
        <!-- Visual header: real project render from DARI's public directory when matched, otherwise a clean placeholder -->
        <div class="relative h-28 bg-gradient-to-br from-[#0a2318] to-[#0e2d45] flex items-center justify-center overflow-hidden">
          {#if p.image_url}
            <img
              src={p.image_url}
              alt={p.project_name}
              loading="lazy"
              class="absolute inset-0 w-full h-full object-cover"
              onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
          {:else}
            <svg class="w-8 h-8 text-white/25" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" />
            </svg>
          {/if}
          <span class="absolute top-2.5 start-2.5 text-[10px] font-bold text-white rounded-full px-2.5 py-1 {c.cls}">{c.label}</span>
          {#if p.property_type}
            <span class="absolute top-2.5 end-2.5 text-[10px] font-bold text-gray-700 bg-white/90 rounded-full px-2.5 py-1">{p.property_type}</span>
          {/if}
        </div>

        <div class="p-4 flex-1 flex flex-col">
          <p class="text-sm font-semibold text-gray-900 group-hover:text-brand-700 transition-colors truncate">{p.project_name}</p>
          <p class="text-xs text-gray-400 truncate mb-3">{p.district ?? '—'}</p>

          {#if p.completion_pct !== null}
            <div class="mb-2">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-gray-400 uppercase tracking-wide">{m.pipeline_construction_label()}</span>
                <span class="text-xs font-bold text-gray-700">{p.completion_pct}%</span>
              </div>
              <div class="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full rounded-full bg-emerald-500" style="width:{p.completion_pct}%"></div>
              </div>
            </div>
          {/if}

          <div class="mt-auto pt-2 flex items-center justify-between gap-2">
            <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {s.cls}">{s.label}</span>
            <span class="text-xs text-gray-500">{fmt(p.median_psf)} AED/sqft</span>
          </div>

          <div class="mt-2 pt-2 border-t border-gray-100 flex items-center justify-between text-[10px] text-gray-400">
            <span>{m.pipeline_sales_per_90d({ count: String(p.sales_last_90d) })}</span>
            <span class="{p.momentum_pct == null ? 'text-gray-400' : p.momentum_pct >= 0 ? 'text-emerald-600' : 'text-red-500'} font-semibold">
              {p.momentum_pct == null ? '—' : `${p.momentum_pct >= 0 ? '+' : ''}${p.momentum_pct}%`}
            </span>
          </div>
        </div>
      </div>
    {/each}

    {#if filtered.length === 0}
      <div class="col-span-full px-5 py-10 text-center text-sm text-gray-400">{m.pipeline_no_match()}</div>
    {/if}
  </div>

  <p class="mt-1 text-[10px] text-gray-400">{m.pipeline_source_footer()}</p>

</div>
