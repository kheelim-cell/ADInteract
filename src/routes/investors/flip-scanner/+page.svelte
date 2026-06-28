<script lang="ts">
  import { metadata } from '$lib/stores/db';
  import { dbReady } from '$lib/stores/db';
  import {
    queryFlipScanner,
    type FlipRow,
    type InvestorFilterState
  } from '$lib/db/investor_queries';
  import FlipScannerTable from '$lib/components/investors/FlipScannerTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import { m } from '$lib/paraglide/messages.js';

  // ── Filter state ───────────────────────────────────────────────────────────
  let filterDistrict = $state('');
  let filterLayout   = $state('');

  let filters = $derived<InvestorFilterState>({
    district:     filterDistrict || null,
    propertyType: null,
    layout:       filterLayout   || null,
  });

  let hasFilter = $derived(!!(filterDistrict || filterLayout));

  function resetFilters() {
    filterDistrict = '';
    filterLayout   = '';
  }

  // Entry-window controls (how far back to look for off-plan registrations)
  let entryStartMonths = $state(48);
  let entryEndMonths   = $state(12);

  // ── Filter options from metadata ───────────────────────────────────────────
  const LAYOUT_ORDER = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds', '5+ beds', '6+ beds'];
  const LAYOUT_DISPLAY: Record<string, string> = { studio: 'Studio' };

  let districts = $derived($metadata?.districts ?? []);
  let layouts   = $derived(
    ($metadata?.layouts ?? [])
      .filter(l => LAYOUT_ORDER.includes(l.toLowerCase()))
      .sort((a, b) => LAYOUT_ORDER.indexOf(a.toLowerCase()) - LAYOUT_ORDER.indexOf(b.toLowerCase()))
  );

  const sel = 'text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]';

  // ── Query state ────────────────────────────────────────────────────────────
  let rows    = $state<FlipRow[]>([]);
  let loading = $state(true);

  $effect(() => {
    if (!$dbReady) return;
    const f  = filters;
    const es = entryStartMonths;
    const ee = entryEndMonths;
    loading = true;

    queryFlipScanner(f, es, ee)
      .then(r => { rows = r; })
      .catch(() => { rows = []; })
      .finally(() => { loading = false; });
  });

  // Summary stats
  let topRoi  = $derived(rows.length > 0 ? rows[0].roiPct : null);
  let avgRoi  = $derived(
    rows.length > 0
      ? rows.reduce((s, r) => s + r.roiPct, 0) / rows.length
      : null
  );
  let totalProjects = $derived(new Set(rows.map(r => r.projectName)).size);
</script>

<svelte:head>
  <title>Off-Plan Flip Scanner — Abu Dhabi Investment Opportunities | ADInteract</title>
  <meta name="description" content="Identify Abu Dhabi projects where off-plan entry prices are significantly below current secondary-market rates — sourced from ADREC registered transactions." />
  <meta property="og:title" content="Off-Plan Flip Scanner — Abu Dhabi Investment Opportunities | ADInteract" />
  <meta property="og:description" content="Compare off-plan entry prices to today's secondary-market rates. Find where Abu Dhabi investors are seeing the strongest appreciation on ADREC data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <!-- ── Explainer header ───────────────────────────────────────────────── -->
  <div class="rounded-2xl bg-gradient-to-r from-[#0a2318]/5 to-emerald-50 border border-emerald-100 px-5 py-4">
    <div class="flex items-start gap-3">
      <div class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-emerald-100">
        <svg class="h-4.5 w-4.5 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
      </div>
      <div>
        <p class="text-sm font-semibold text-gray-800">
          {m.compare_explainer_title()}
        </p>
        <p class="mt-0.5 text-xs leading-relaxed text-gray-500">
          {m.flip_explainer_part1()} <strong class="text-gray-700">{m.flip_explainer_median_offplan()}</strong> {m.flip_explainer_part2()} <strong class="text-gray-700">{m.flip_explainer_median_secondary()}</strong> {m.flip_explainer_part3()}
        </p>
      </div>
    </div>
  </div>

  <!-- ── Filters ────────────────────────────────────────────────────────── -->
  <div>
    <div class="flex flex-wrap items-center gap-3">

      <select bind:value={filterDistrict} class={sel}>
        <option value="">{m.calc_district_all()}</option>
        {#each districts as d}
          <option value={d}>{d}</option>
        {/each}
      </select>

      <select bind:value={filterLayout} class={sel}>
        <option value="">{m.flip_all_layouts()}</option>
        {#each layouts as l}
          <option value={l}>{LAYOUT_DISPLAY[l.toLowerCase()] ?? l}</option>
        {/each}
      </select>

      <!-- Entry window selector -->
      <div class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2">
        <span class="text-xs text-gray-500 whitespace-nowrap">{m.flip_offplan_window_label()}</span>
        <select
          bind:value={entryStartMonths}
          class="text-xs font-semibold text-gray-700 bg-transparent focus:outline-none"
        >
          <option value={24}>{m.flip_months_ago({ n: '24' })}</option>
          <option value={36}>{m.flip_months_ago({ n: '36' })}</option>
          <option value={48}>{m.flip_months_ago({ n: '48' })}</option>
          <option value={60}>{m.flip_months_ago({ n: '60' })}</option>
        </select>
        <span class="text-xs text-gray-400">→</span>
        <select
          bind:value={entryEndMonths}
          class="text-xs font-semibold text-gray-700 bg-transparent focus:outline-none"
        >
          <option value={6}>{m.flip_months_ago({ n: '6' })}</option>
          <option value={12}>{m.flip_months_ago({ n: '12' })}</option>
          <option value={18}>{m.flip_months_ago({ n: '18' })}</option>
          <option value={24}>{m.flip_months_ago({ n: '24' })}</option>
        </select>
      </div>

      {#if hasFilter}
        <button
          type="button"
          onclick={resetFilters}
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
          {m.flip_clear_filters()}
        </button>
      {/if}
    </div>
    <PopularAreaChips activeDistrict={filterDistrict || null} onSelect={(d) => { filterDistrict = d; }} />
  </div>

  <!-- ── Summary KPI strip ──────────────────────────────────────────────── -->
  {#if !loading && rows.length > 0}
    <div class="flex flex-wrap items-center gap-x-8 gap-y-2 rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-gray-500">{m.flip_opportunities_label()}</span>
        <span class="font-semibold text-gray-900">{m.flip_project_layout_pairs({ count: String(rows.length) })}</span>
      </div>
      <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
      <div class="flex items-center gap-2">
        <span class="text-gray-500">{m.flip_unique_projects_label()}</span>
        <span class="font-semibold text-gray-900">{totalProjects}</span>
      </div>
      <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
      <div class="flex items-center gap-2">
        <span class="text-gray-500">{m.flip_top_roi_label()}</span>
        <span class="font-semibold text-emerald-700">+{topRoi?.toFixed(1)}%</span>
      </div>
      <div class="h-4 w-px bg-gray-200 hidden sm:block"></div>
      <div class="flex items-center gap-2">
        <span class="text-gray-500">{m.flip_avg_roi_label()}</span>
        <span class="font-semibold text-gray-900">+{avgRoi?.toFixed(1)}%</span>
      </div>
    </div>
  {/if}

  <!-- ── Section heading ─────────────────────────────────────────────────── -->
  <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">
    {m.flip_section_heading()}
  </h3>

  <!-- ── Table ──────────────────────────────────────────────────────────── -->
  <FlipScannerTable {rows} {loading} />

</div>
