<script lang="ts">
  import { base } from '$app/paths';
  import rawPipeline from '$lib/data/project_pipeline.json';

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
    if (status === 'accelerating') return { label: 'Accelerating', cls: 'bg-emerald-100 text-emerald-800' };
    if (status === 'new_launch')   return { label: 'New launch',   cls: 'bg-blue-100 text-blue-800' };
    if (status === 'slowing')      return { label: 'Slowing',      cls: 'bg-amber-100 text-amber-800' };
    if (status === 'stale')        return { label: 'Stale',        cls: 'bg-gray-100 text-gray-500' };
    return                                 { label: 'Steady',      cls: 'bg-violet-100 text-violet-800' };
  }

  const accelerating = data.projects.filter(p => p.status === 'accelerating').length;
  const stale = data.projects.filter(p => p.status === 'stale').length;
</script>

<svelte:head>
  <title>Abu Dhabi Off-Plan Project Pipeline — Registered Sales Velocity | ADInteract</title>
  <meta name="description" content="Off-plan project pipeline for Abu Dhabi: registered-sales velocity per project, recent vs prior 90-day momentum, and days since last registration. Sourced from ADREC transaction data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <div class="mb-2">
    <h1 class="text-xl font-bold text-gray-900 mb-1">Off-Plan Project Pipeline</h1>
    <p class="text-sm text-gray-500 max-w-2xl">
      <span class="font-medium text-gray-700">{data.project_count}</span> active off-plan projects, ranked by registered-sales activity in the last 90 days.
      Updated daily from ADREC transaction data as of {data.as_of_date}.
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
        <p class="text-sm font-semibold text-gray-800">What this tracks — and what it can't tell you</p>
        <p class="mt-0.5 text-xs leading-relaxed text-gray-500">
          This is <strong class="text-gray-700">registered-sales velocity</strong>, not unit absorption. ADREC's transaction export has no field for total units per project,
          so we can't report a "% sold" or true absorption rate — anyone quoting one from this data source is estimating, not reporting.
          What we do report straight from registrations: how many off-plan sales a project has logged in the <strong class="text-gray-700">last 90 days vs. the prior 90 days</strong> (momentum),
          and how many days since its <strong class="text-gray-700">last registered sale</strong> (a 0-sale 90+ day gap is flagged "stale" — sold out, paused, or struggling; we can't tell which).
        </p>
      </div>
    </div>
  </div>

  <!-- ── KPI strip ──────────────────────────────────────────────────────── -->
  <div class="flex flex-wrap items-center gap-x-8 gap-y-2 rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm shadow-sm">
    <div class="flex items-center gap-2">
      <span class="text-gray-500">Projects tracked</span>
      <span class="font-semibold text-gray-900">{data.project_count}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">All-time registered sales</span>
      <span class="font-semibold text-gray-900">{fmt(data.total_registered_sales_alltime)}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">Accelerating</span>
      <span class="font-semibold text-emerald-700">{accelerating}</span>
    </div>
    <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
    <div class="flex items-center gap-2">
      <span class="text-gray-500">Stale (90+ days, no sales)</span>
      <span class="font-semibold text-gray-500">{stale}</span>
    </div>
  </div>

  <!-- ── Filters ────────────────────────────────────────────────────────── -->
  <div class="flex flex-wrap items-center gap-3">
    <select bind:value={filterDistrict} class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]">
      <option value="">All Districts</option>
      {#each districts as d}
        <option value={d}>{d}</option>
      {/each}
    </select>

    <select bind:value={filterStatus} class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]">
      <option value="">All Statuses</option>
      <option value="accelerating">Accelerating</option>
      <option value="new_launch">New launch</option>
      <option value="steady">Steady</option>
      <option value="slowing">Slowing</option>
      <option value="stale">Stale</option>
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
        Clear filters
      </button>
    {/if}

    <span class="text-xs text-gray-400 ml-auto">{filtered.length} of {data.project_count} projects</span>
  </div>

  <!-- ── Desktop table (md+) ─────────────────────────────────────────── -->
  <div class="hidden md:block rounded-2xl border border-gray-200 overflow-hidden bg-white">
    <div class="grid grid-cols-[1.4fr_8rem_7rem_6rem_6rem_6rem_6rem] items-center gap-2 px-5 py-3 bg-gray-50 border-b border-gray-100 text-[10px] font-bold uppercase tracking-widest text-gray-400">
      <span>Project</span>
      <span>Status</span>
      <span class="text-right">Last 90d sales</span>
      <span class="text-right">Momentum</span>
      <span class="text-right">All-time sales</span>
      <span class="text-right">AED/sqft</span>
      <span class="text-right">Last sale</span>
    </div>

    {#each filtered as p}
      {@const s = statusMeta(p.status)}
      <div class="grid grid-cols-[1.4fr_8rem_7rem_6rem_6rem_6rem_6rem] items-center gap-2 px-5 py-4 border-b border-gray-100 last:border-0 bg-white hover:bg-gray-50 transition-colors">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-gray-900 truncate">{p.project_name}</p>
          <p class="text-[10px] text-gray-400 truncate">{p.district ?? '—'}</p>
        </div>
        <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {s.cls} w-fit">{s.label}</span>
        <span class="text-sm text-right font-semibold text-gray-900">{p.sales_last_90d}</span>
        <span class="text-sm text-right {p.momentum_pct == null ? 'text-gray-400' : p.momentum_pct >= 0 ? 'text-emerald-600' : 'text-red-500'} font-semibold">
          {p.momentum_pct == null ? '—' : `${p.momentum_pct >= 0 ? '+' : ''}${p.momentum_pct}%`}
        </span>
        <span class="text-sm text-right text-gray-600">{fmt(p.registered_sales_alltime)}</span>
        <span class="text-sm text-right text-gray-600">{fmt(p.median_psf)}</span>
        <span class="text-sm text-right text-gray-600">{p.days_since_last_sale === 0 ? 'today' : `${p.days_since_last_sale}d ago`}</span>
      </div>
    {/each}

    {#if filtered.length === 0}
      <div class="px-5 py-10 text-center text-sm text-gray-400">No projects match these filters</div>
    {/if}
  </div>

  <!-- ── Mobile cards (< md) ─────────────────────────────────────────── -->
  <div class="md:hidden space-y-2">
    {#each filtered as p}
      {@const s = statusMeta(p.status)}
      <div class="rounded-xl border border-gray-200 bg-white px-4 py-3.5">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-gray-900 truncate leading-tight">{p.project_name}</p>
            <p class="text-[10px] text-gray-400 truncate">{p.district ?? '—'}</p>
          </div>
          <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {s.cls} flex-shrink-0">{s.label}</span>
        </div>
        <div class="mt-2.5 grid grid-cols-3 gap-2 text-center">
          <div>
            <p class="text-base font-black text-gray-900 leading-none">{p.sales_last_90d}</p>
            <p class="text-[9px] text-gray-400 mt-0.5">last 90d</p>
          </div>
          <div>
            <p class="text-base font-black leading-none {p.momentum_pct == null ? 'text-gray-400' : p.momentum_pct >= 0 ? 'text-emerald-600' : 'text-red-500'}">
              {p.momentum_pct == null ? '—' : `${p.momentum_pct >= 0 ? '+' : ''}${p.momentum_pct}%`}
            </p>
            <p class="text-[9px] text-gray-400 mt-0.5">momentum</p>
          </div>
          <div>
            <p class="text-base font-black text-gray-900 leading-none">{fmt(p.median_psf)}</p>
            <p class="text-[9px] text-gray-400 mt-0.5">AED/sqft</p>
          </div>
        </div>
        <p class="mt-2 text-[10px] text-gray-400">{fmt(p.registered_sales_alltime)} all-time sales · last sale {p.days_since_last_sale === 0 ? 'today' : `${p.days_since_last_sale}d ago`}</p>
      </div>
    {/each}

    {#if filtered.length === 0}
      <div class="px-5 py-10 text-center text-sm text-gray-400">No projects match these filters</div>
    {/if}
  </div>

  <p class="mt-1 text-[10px] text-gray-400">Source: ADREC via ADInteract.co · registered off-plan sales only · updated daily</p>

</div>
