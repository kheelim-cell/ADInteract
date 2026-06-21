<script lang="ts">
  import rawData from '$lib/data/market_structure.json';

  type ProfessionRow = { label: string; count: number };
  type Sample = { name: string; classification: string };
  type MarketStructure = {
    generated_at: string;
    total_licensed: number;
    by_profession: ProfessionRow[];
    developer_breakdown: Record<string, number>;
    samples: Record<string, Sample[]>;
  };

  const data = rawData as MarketStructure;

  const maxCount = Math.max(...data.by_profession.map(p => p.count));

  function fmt(n: number) {
    return n.toLocaleString('en-AE');
  }

  const primaryDevelopers = data.developer_breakdown['Primary Developer'] ?? 0;
  const secondaryDevelopers = data.developer_breakdown['Secondary Developer'] ?? 0;

  const sampleProfessions = Object.keys(data.samples).filter(label => (data.samples[label] ?? []).length > 0);

  const PAGE_SIZE = 10;
  let filterProfession = $state('');
  let showAllSamples = $state(false);

  let filteredSamples = $derived(
    filterProfession
      ? (data.samples[filterProfession] ?? [])
      : sampleProfessions.flatMap(label => data.samples[label] ?? [])
  );

  let visibleSamples = $derived(
    showAllSamples ? filteredSamples : filteredSamples.slice(0, PAGE_SIZE)
  );

  function onFilterChange() {
    showAllSamples = false;
  }
</script>

<svelte:head>
  <title>Abu Dhabi Real Estate Market Structure — Licensed Brokers, Agencies & Developers | ADInteract</title>
  <meta name="description" content="Who's actually active in Abu Dhabi real estate: licensed broker, agency and developer counts straight from DARI's public professions directory." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <div class="mb-2">
    <h1 class="text-xl font-bold text-gray-900 mb-1">Market Structure</h1>
    <p class="text-sm text-gray-500 max-w-2xl">
      <span class="font-medium text-gray-700">{fmt(data.total_licensed)}</span> licensed real estate professionals active in Abu Dhabi, sourced from DARI's public professions directory — not estimated.
    </p>
  </div>

  <!-- ── KPI strip ──────────────────────────────────────────────────────── -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
    <div class="rounded-xl border border-gray-100 bg-white px-4 py-3.5 shadow-sm">
      <p class="text-xs text-gray-500 mb-1">Total licensed</p>
      <p class="text-xl font-bold text-gray-900">{fmt(data.total_licensed)}</p>
    </div>
    <div class="rounded-xl border border-gray-100 bg-white px-4 py-3.5 shadow-sm">
      <p class="text-xs text-gray-500 mb-1">Brokers</p>
      <p class="text-xl font-bold text-gray-900">{fmt(data.by_profession.find(p => p.label === 'Brokers')?.count ?? 0)}</p>
    </div>
    <div class="rounded-xl border border-gray-100 bg-white px-4 py-3.5 shadow-sm">
      <p class="text-xs text-gray-500 mb-1">Developers</p>
      <p class="text-xl font-bold text-gray-900">{fmt(data.by_profession.find(p => p.label === 'Developers')?.count ?? 0)}</p>
    </div>
    <div class="rounded-xl border border-gray-100 bg-white px-4 py-3.5 shadow-sm">
      <p class="text-xs text-gray-500 mb-1">Surveyors</p>
      <p class="text-xl font-bold text-gray-900">{fmt(data.by_profession.find(p => p.label === 'Surveyors')?.count ?? 0)}</p>
    </div>
  </div>

  <!-- ── Breakdown by profession type ──────────────────────────────────── -->
  <div class="rounded-2xl border border-gray-200 bg-white px-5 py-4">
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Breakdown by profession type</h3>
    <div class="space-y-3">
      {#each data.by_profession as p}
        <div class="flex items-center gap-3">
          <span class="w-32 flex-shrink-0 text-sm text-gray-600">{p.label}</span>
          <div class="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
            <div class="h-full rounded-full bg-emerald-500" style="width:{maxCount ? (p.count / maxCount * 100) : 0}%"></div>
          </div>
          <span class="w-16 flex-shrink-0 text-right text-sm font-semibold text-gray-900">{fmt(p.count)}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- ── Developer split ────────────────────────────────────────────────── -->
  {#if primaryDevelopers || secondaryDevelopers}
    <div class="rounded-2xl border border-gray-200 bg-white px-5 py-4">
      <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Developer registration type</h3>
      <p class="text-xs text-gray-400 mb-4">Primary developers hold the main project registration. Secondary developers build within an established master project.</p>
      <div class="flex gap-3">
        <div class="flex-1 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3">
          <p class="text-xs text-emerald-700 font-semibold mb-1">Primary developers</p>
          <p class="text-xl font-bold text-emerald-900">{fmt(primaryDevelopers)}</p>
        </div>
        <div class="flex-1 rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <p class="text-xs text-blue-700 font-semibold mb-1">Secondary developers</p>
          <p class="text-xl font-bold text-blue-900">{fmt(secondaryDevelopers)}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- ── Directory sample ───────────────────────────────────────────────── -->
  {#if sampleProfessions.length > 0}
    <div class="rounded-2xl border border-gray-200 bg-white px-5 py-4">
      <div class="flex items-center justify-between gap-3 mb-4">
        <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">Directory sample</h3>
        <select
          bind:value={filterProfession}
          onchange={onFilterChange}
          class="text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All professions</option>
          {#each sampleProfessions as label}
            <option value={label}>{label}</option>
          {/each}
        </select>
      </div>

      {#if visibleSamples.length === 0}
        <p class="text-sm text-gray-400 py-4 text-center">No sample entries for this profession</p>
      {:else}
        <div class="divide-y divide-gray-100">
          {#each visibleSamples as s}
            <div class="flex items-center justify-between gap-3 py-2.5">
              <span class="text-sm text-gray-800 truncate">{s.name}</span>
              <span class="text-[10px] font-bold rounded-full px-2 py-0.5 bg-gray-100 text-gray-600 flex-shrink-0">{s.classification}</span>
            </div>
          {/each}
        </div>

        {#if filteredSamples.length > PAGE_SIZE}
          <div class="mt-3 flex justify-center">
            <button
              type="button"
              onclick={() => showAllSamples = !showAllSamples}
              class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 hover:border-brand-300 hover:text-brand-700 transition-colors"
            >
              {showAllSamples ? `Show top ${PAGE_SIZE} only` : `Show all ${filteredSamples.length}`}
              <svg class="w-3.5 h-3.5 transition-transform {showAllSamples ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
          </div>
        {/if}
      {/if}
    </div>
  {/if}

  <!-- ── v2 teaser ──────────────────────────────────────────────────────── -->
  <div class="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-5 py-4">
    <div class="flex items-center gap-2 mb-1">
      <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25z" />
      </svg>
      <p class="text-sm font-semibold text-gray-600">Top agencies by broker headcount — coming soon</p>
    </div>
    <p class="text-xs text-gray-400">Requires a per-company detail fetch (employee list) on top of this directory scrape. Held for a follow-up build.</p>
  </div>

  <p class="mt-1 text-[10px] text-gray-400">Source: DARI public professions directory (dari.ae) via ADInteract.co · updated monthly · counts only, not unit/transaction data</p>

</div>
