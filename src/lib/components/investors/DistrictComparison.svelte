<script lang="ts">
  import { base } from '$app/paths';
  import { onMount } from 'svelte';
  import { metadata, rentalMetadata, dbReady } from '$lib/stores/db';
  import { queryDistrictComparison, type DistrictComparisonData } from '$lib/db/investor_queries';
  import { m } from '$lib/paraglide/messages.js';

  // ── Types ──────────────────────────────────────────────────────────────────
  interface ScProject {
    project_name: string;
    district: string;
    sc_avg: number | null;
  }

  // ── Constants ──────────────────────────────────────────────────────────────
  let LAYOUTS = $derived([
    { value: 'studio', label: m.filter_layout_studio() },
    { value: '1 bed',  label: m.filter_layout_1_bed()  },
    { value: '2 beds', label: m.filter_layout_2_beds() },
    { value: '3 beds', label: m.filter_layout_3_beds() },
  ] as const);

  const PINNED_DISTRICTS = [
    'Al Reem Island', 'Yas Island', 'Al Saadiyat Island', 'Al Rahah',
    'Khalifa City', 'Al Reef', 'Fahid Island', 'Al Hidayriyyat',
  ];

  // ── State ──────────────────────────────────────────────────────────────────
  let layout    = $state('1 bed');
  let district1 = $state('');
  let district2 = $state('');
  let district3 = $state('');
  let show3rd   = $state(false);

  let results    = $state<DistrictComparisonData[]>([]);
  let loading    = $state(false);
  let scProjects = $state<ScProject[]>([]);
  let copied     = $state(false);

  // ── Rental year (from metadata) ────────────────────────────────────────────
  const thisYear = new Date().getFullYear();
  let rentalYear = $derived.by(() => {
    const ly = $rentalMetadata?.latestYear;
    if (!ly) return thisYear - 1;
    return ly >= thisYear ? thisYear - 1 : ly;
  });

  // ── District list for selects (pinned popular areas first, rest alphabetical) ─
  let pinnedDistricts = $derived.by(() => {
    const all: string[] = $metadata?.districts ?? [];
    return PINNED_DISTRICTS.filter(p => all.some(d => d.toLowerCase() === p.toLowerCase()));
  });
  let otherDistricts = $derived.by(() => {
    const all: string[] = $metadata?.districts ?? [];
    const pinnedSet = new Set(pinnedDistricts.map((p: string) => p.toLowerCase()));
    return all.filter(d => !pinnedSet.has(d.toLowerCase())).sort();
  });

  // ── Selected districts ─────────────────────────────────────────────────────
  let selectedDistricts = $derived(
    [district1, district2, show3rd ? district3 : '']
      .filter((d): d is string => d !== '' && d !== null)
  );

  let canCompare = $derived($dbReady && selectedDistricts.length >= 2);

  // ── URL state sync (defaults to top 2 pinned districts when no URL params) ──
  onMount(() => {
    const sp = new URLSearchParams(window.location.search);
    const d1  = sp.get('d1') ?? '';
    const d2  = sp.get('d2') ?? '';
    const d3  = sp.get('d3') ?? '';
    const lay = sp.get('layout') ?? '1 bed';

    if (d1) district1 = d1;
    else    district1 = PINNED_DISTRICTS[0]; // Al Reem Island
    if (d2) district2 = d2;
    else    district2 = PINNED_DISTRICTS[1]; // Yas Island
    if (d3) { district3 = d3; show3rd = true; }
    if (LAYOUTS.some(l => l.value === lay)) layout = lay;
  });

  $effect(() => {
    if (typeof window === 'undefined') return;
    const d1v = district1;
    const d2v = district2;
    const d3v = show3rd ? district3 : '';
    const lay = layout;

    const url = new URL(window.location.href);
    if (d1v) url.searchParams.set('d1', d1v); else url.searchParams.delete('d1');
    if (d2v) url.searchParams.set('d2', d2v); else url.searchParams.delete('d2');
    if (d3v) url.searchParams.set('d3', d3v); else url.searchParams.delete('d3');
    url.searchParams.set('layout', lay);
    history.replaceState({}, '', url.toString());
  });

  // ── Query ──────────────────────────────────────────────────────────────────
  $effect(() => {
    if (!$dbReady) return;
    const dists = selectedDistricts;
    const lay   = layout;
    const ry    = rentalYear;
    if (dists.length < 2) { results = []; return; }

    loading = true;
    queryDistrictComparison(dists, lay, ry)
      .then(r => { results = r; })
      .catch(() => { results = []; })
      .finally(() => { loading = false; });
  });

  // ── Load service charges ───────────────────────────────────────────────────
  onMount(async () => {
    try {
      const res = await fetch(`${base}/data/service_charges.json`);
      if (res.ok) {
        const json = await res.json();
        scProjects = json.projects ?? [];
      }
    } catch { /* ignore — SC column shows '—' */ }
  });

  // ── SC median per district (client-side from JSON) ─────────────────────────
  function districtMedianSc(district: string): number | null {
    const vals = scProjects
      .filter(p => p.district === district && typeof p.sc_avg === 'number' && p.sc_avg > 0)
      .map(p => p.sc_avg as number)
      .sort((a, b) => a - b);
    if (vals.length === 0) return null;
    const mid = Math.floor(vals.length / 2);
    return vals.length % 2 === 0 ? (vals[mid - 1] + vals[mid]) / 2 : vals[mid];
  }

  // ── Row lookup ─────────────────────────────────────────────────────────────
  let rowByDistrict = $derived(new Map(results.map(r => [r.district, r])));

  // ── Winner indices (returns Set of column indices) ─────────────────────────
  function bestIndices(values: (number | null)[], higherIsBetter: boolean): Set<number> {
    const valid = values.map((v, i) => ({ v, i })).filter(x => x.v !== null);
    if (valid.length < 2) return new Set();
    const bestVal = higherIsBetter
      ? Math.max(...valid.map(x => x.v as number))
      : Math.min(...valid.map(x => x.v as number));
    return new Set(valid.filter(x => x.v === bestVal).map(x => x.i));
  }

  let yoyWinners   = $derived(bestIndices(selectedDistricts.map(d => rowByDistrict.get(d)?.yoyPct      ?? null), true));
  let yieldWinners = $derived(bestIndices(selectedDistricts.map(d => rowByDistrict.get(d)?.grossYieldPct ?? null), true));
  let scWinners    = $derived(bestIndices(selectedDistricts.map(d => districtMedianSc(d)),                        false));
  let volWinners   = $derived(bestIndices(selectedDistricts.map(d => rowByDistrict.get(d)?.txCount      ?? null), true));

  // ── Formatting ─────────────────────────────────────────────────────────────
  function fmtAed(v: number | null): string {
    if (v === null || !isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPsf(v: number | null): string {
    if (v === null || !isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number | null): string {
    if (v === null || !isFinite(v)) return '—';
    return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
  }
  function fmtCount(v: number): string {
    return v.toLocaleString('en-AE');
  }
  function fmtSc(v: number | null): string {
    if (v === null) return '—';
    return v.toFixed(1);
  }

  // ── Copy share link ────────────────────────────────────────────────────────
  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      copied = true;
      setTimeout(() => { copied = false; }, 2000);
    } catch { /* ignore */ }
  }

  // ── Shared select style ────────────────────────────────────────────────────
  const sel = 'text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 appearance-none cursor-pointer';
</script>

<div class="space-y-5">

  <!-- ── Explainer ──────────────────────────────────────────────────────────── -->
  <div class="rounded-2xl bg-gradient-to-r from-[#0a2318]/5 to-emerald-50 border border-emerald-100 px-5 py-4">
    <div class="flex items-start gap-3">
      <div class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-emerald-100">
        <svg class="h-4 w-4 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 3M21 7.5H7.5" />
        </svg>
      </div>
      <div>
        <p class="text-sm font-semibold text-gray-800">{m.compare_explainer_title()}</p>
        <p class="mt-0.5 text-xs leading-relaxed text-gray-500">
          {m.compare_explainer_body({ year: String(rentalYear) })} <strong class="text-gray-700">{m.compare_explainer_best_label()}</strong> / <strong class="text-gray-700">{m.compare_explainer_lowest_label()}</strong> {m.compare_explainer_badges_suffix()}
        </p>
      </div>
    </div>
  </div>

  <!-- ── Controls ───────────────────────────────────────────────────────────── -->
  <div class="rounded-2xl border border-gray-100 bg-white shadow-sm px-5 py-4 space-y-4">

    <!-- Layout chips -->
    <div>
      <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">{m.compare_bedroom_type_label()}</p>
      <div class="flex flex-wrap gap-2">
        {#each LAYOUTS as l}
          <button
            type="button"
            onclick={() => { layout = l.value; }}
            class="inline-flex items-center px-4 py-1.5 rounded-full text-xs font-semibold border transition-all
              {layout === l.value
                ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700'
                : 'bg-gray-50 border-gray-200 text-gray-500 hover:border-gray-300 hover:text-gray-700'}"
          >
            {l.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- District selectors -->
    <div>
      <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">{m.compare_districts_label()}</p>
      <div class="flex flex-wrap items-center gap-3">

        <!-- District 1 -->
        <div class="relative">
          <select bind:value={district1} class="{sel} min-w-[11rem]">
            <option value="">{m.compare_district1_placeholder()}</option>
            <optgroup label={m.compare_popular()}>
              {#each pinnedDistricts as d}
                <option value={d} disabled={d === district2 || (show3rd && d === district3)}>{d}</option>
              {/each}
            </optgroup>
            <optgroup label={m.compare_all_districts()}>
              {#each otherDistricts as d}
                <option value={d} disabled={d === district2 || (show3rd && d === district3)}>{d}</option>
              {/each}
            </optgroup>
          </select>
          <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </div>

        <span class="text-gray-300 font-bold text-sm hidden sm:block">{m.compare_vs()}</span>

        <!-- District 2 -->
        <div class="relative">
          <select bind:value={district2} class="{sel} min-w-[11rem]">
            <option value="">{m.compare_district2_placeholder()}</option>
            <optgroup label={m.compare_popular()}>
              {#each pinnedDistricts as d}
                <option value={d} disabled={d === district1 || (show3rd && d === district3)}>{d}</option>
              {/each}
            </optgroup>
            <optgroup label={m.compare_all_districts()}>
              {#each otherDistricts as d}
                <option value={d} disabled={d === district1 || (show3rd && d === district3)}>{d}</option>
              {/each}
            </optgroup>
          </select>
          <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </div>

        <!-- District 3 (optional) -->
        {#if show3rd}
          <span class="text-gray-300 font-bold text-sm hidden sm:block">{m.compare_vs()}</span>
          <div class="relative flex items-center gap-1.5">
            <select bind:value={district3} class="{sel} min-w-[11rem]">
              <option value="">{m.compare_district3_placeholder()}</option>
              <optgroup label={m.compare_popular()}>
                {#each pinnedDistricts as d}
                  <option value={d} disabled={d === district1 || d === district2}>{d}</option>
                {/each}
              </optgroup>
              <optgroup label={m.compare_all_districts()}>
                {#each otherDistricts as d}
                  <option value={d} disabled={d === district1 || d === district2}>{d}</option>
                {/each}
              </optgroup>
            </select>
            <svg class="pointer-events-none absolute right-8 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
            <button
              type="button"
              onclick={() => { show3rd = false; district3 = ''; }}
              title={m.compare_remove_3rd_title()}
              class="flex-shrink-0 rounded-full p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {:else}
          <button
            type="button"
            onclick={() => { show3rd = true; }}
            class="inline-flex items-center gap-1.5 rounded-lg border border-dashed border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-500 hover:border-gray-400 hover:text-gray-700 transition-colors"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            {m.compare_add_3rd()}
          </button>
        {/if}

      </div>
    </div>
  </div>

  <!-- ── Results ─────────────────────────────────────────────────────────────── -->
  {#if !canCompare}
    <div class="flex flex-col items-center justify-center py-16 text-center">
      <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
        <svg class="h-7 w-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 3M21 7.5H7.5" />
        </svg>
      </div>
      <p class="text-sm font-semibold text-gray-700">{m.compare_select_2_title()}</p>
      <p class="mt-1 text-xs text-gray-400">{m.compare_select_2_subtitle()}</p>
    </div>

  {:else if loading}
    <!-- Skeleton -->
    <div class="rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-100">
            <tr>
              <th class="px-2 sm:px-4 py-3 w-28 sm:w-44"></th>
              {#each selectedDistricts as d}
                <th class="px-2 sm:px-4 py-3 text-right">
                  <div class="ml-auto h-4 w-16 sm:w-24 bg-gray-200 rounded animate-pulse"></div>
                </th>
              {/each}
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each Array(7) as _}
              <tr>
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div class="h-3 w-20 sm:w-32 bg-gray-100 rounded animate-pulse mb-1.5"></div>
                </td>
                {#each selectedDistricts as __}
                  <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right">
                    <div class="ml-auto h-4 w-16 sm:w-20 bg-gray-100 rounded animate-pulse"></div>
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  {:else if results.length === 0}
    <div class="flex flex-col items-center justify-center py-12 text-center rounded-2xl border border-gray-100 bg-white">
      <svg class="h-10 w-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
      <p class="text-sm font-semibold text-gray-700">{m.compare_no_data_title()}</p>
      <p class="mt-1 text-xs text-gray-400">{m.compare_no_data_subtitle()}</p>
    </div>

  {:else}
    <!-- ── Comparison table ───────────────────────────────────────────────── -->
    <div class="rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">

          <!-- Header: district names as columns -->
          <thead class="bg-gray-50 border-b border-gray-100">
            <tr>
              <th class="px-2 sm:px-4 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest w-28 sm:w-52">
                {m.compare_metric_header()}
              </th>
              {#each selectedDistricts as d, i}
                {@const row = rowByDistrict.get(d)}
                {@const colors = ['text-sky-700', 'text-violet-700', 'text-amber-700']}
                <th class="px-2 sm:px-4 py-3 text-right">
                  <span class="block text-xs sm:text-sm font-bold {colors[i]} leading-tight">{d}</span>
                  {#if row}
                    <span class="hidden sm:block text-[10px] font-normal text-gray-400 mt-0.5">
                      {m.compare_sales_12mo({ count: fmtCount(row.txCount) })}
                    </span>
                  {:else}
                    <span class="hidden sm:block text-[10px] font-normal text-gray-400 mt-0.5">{m.compare_no_data_short()}</span>
                  {/if}
                </th>
              {/each}
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-50">

            <!-- 1. Median Sale Price (AED) — informational, no winner -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_median_sale_price()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_aed_rolling_12mo()}</span>
              </td>
              {#each selectedDistricts as d}
                {@const row = rowByDistrict.get(d)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right tabular-nums text-xs sm:text-sm font-medium text-gray-800">
                  {fmtAed(row?.medianPrice ?? null)}
                </td>
              {/each}
            </tr>

            <!-- 2. Median AED/sqft — informational, no winner -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_median_psf()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_rolling_12mo()}</span>
              </td>
              {#each selectedDistricts as d}
                {@const row = rowByDistrict.get(d)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right tabular-nums text-xs sm:text-sm font-medium text-gray-800">
                  {fmtPsf(row?.medianPsf ?? null)}
                </td>
              {/each}
            </tr>

            <!-- 3. YoY Price Growth — highest wins -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_yoy_price_growth()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_yoy_subtitle()}</span>
              </td>
              {#each selectedDistricts as d, i}
                {@const row = rowByDistrict.get(d)}
                {@const v = row?.yoyPct ?? null}
                {@const isWinner = yoyWinners.has(i)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div class="flex flex-col items-end sm:flex-row sm:items-center sm:justify-end gap-0.5 sm:gap-0">
                    <span class="tabular-nums text-xs sm:text-sm font-medium sm:mr-1
                      {isWinner ? 'text-emerald-700 font-semibold' : v !== null && v < 0 ? 'text-red-500' : 'text-gray-800'}">
                      {fmtPct(v)}
                    </span>
                    {#if isWinner}
                      <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">{m.compare_best_badge()}</span>
                    {/if}
                  </div>
                </td>
              {/each}
            </tr>

            <!-- 4. Gross Rental Yield — highest wins -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_gross_rental_yield()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_rental_yield_subtitle({ year: String(rentalYear) })}</span>
              </td>
              {#each selectedDistricts as d, i}
                {@const row = rowByDistrict.get(d)}
                {@const v = row?.grossYieldPct ?? null}
                {@const isWinner = yieldWinners.has(i)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div class="flex flex-col items-end sm:flex-row sm:items-center sm:justify-end gap-0.5 sm:gap-0">
                    <span class="tabular-nums text-xs sm:text-sm font-medium sm:mr-1
                      {isWinner ? 'text-emerald-700 font-semibold' : 'text-gray-800'}">
                      {v !== null ? v.toFixed(2) + '%' : '—'}
                    </span>
                    {#if isWinner}
                      <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">{m.compare_best_badge()}</span>
                    {/if}
                  </div>
                </td>
              {/each}
            </tr>

            <!-- 5. Median Service Charge — lowest wins -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_service_charge()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_service_charge_subtitle()}</span>
              </td>
              {#each selectedDistricts as d, i}
                {@const sc = districtMedianSc(d)}
                {@const isWinner = scWinners.has(i)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div class="flex flex-col items-end sm:flex-row sm:items-center sm:justify-end gap-0.5 sm:gap-0">
                    <span class="tabular-nums text-xs sm:text-sm font-medium sm:mr-1
                      {isWinner ? 'text-emerald-700 font-semibold' : 'text-gray-800'}">
                      {#if sc !== null}
                        {fmtSc(sc)}<span class="text-gray-400 text-[10px]">/sqft</span>
                      {:else}
                        —
                      {/if}
                    </span>
                    {#if isWinner}
                      <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">{m.compare_lowest_badge()}</span>
                    {/if}
                  </div>
                </td>
              {/each}
            </tr>

            <!-- 6. Transaction Volume — highest wins (liquidity) -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_transaction_volume()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_tx_volume_subtitle()}</span>
              </td>
              {#each selectedDistricts as d, i}
                {@const row = rowByDistrict.get(d)}
                {@const isWinner = volWinners.has(i)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5">
                  <div class="flex flex-col items-end sm:flex-row sm:items-center sm:justify-end gap-0.5 sm:gap-0">
                    <span class="tabular-nums text-xs sm:text-sm font-medium sm:mr-1
                      {isWinner ? 'text-emerald-700 font-semibold' : 'text-gray-800'}">
                      {row ? `${fmtCount(row.txCount)} ${m.compare_sales_suffix()}` : '—'}
                    </span>
                    {#if isWinner}
                      <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">{m.compare_most_liquid_badge()}</span>
                    {/if}
                  </div>
                </td>
              {/each}
            </tr>

            <!-- 7. Supply Pipeline — informational only -->
            <tr class="hover:bg-gray-50/50 transition-colors">
              <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-xs">
                <span class="font-semibold text-gray-700">{m.compare_supply_pipeline()}</span>
                <span class="hidden sm:block text-[10px] text-gray-400 mt-0.5">{m.compare_supply_pipeline_subtitle()}</span>
              </td>
              {#each selectedDistricts as d}
                {@const row = rowByDistrict.get(d)}
                <td class="px-2 sm:px-4 py-2.5 sm:py-3.5 text-right tabular-nums text-xs sm:text-sm font-medium text-gray-800">
                  {row ? `${fmtCount(row.pipelineCount)} ${m.compare_units_suffix()}` : '—'}
                </td>
              {/each}
            </tr>

          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Legend + share ─────────────────────────────────────────────────── -->
    <div class="flex flex-wrap items-center justify-between gap-4">

      <!-- Legend -->
      <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-gray-400">
        <span class="flex items-center gap-1">
          <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 font-bold text-emerald-700">{m.compare_best_badge()}</span>
          {m.compare_legend_highest()}
        </span>
        <span class="flex items-center gap-1">
          <span class="inline-flex items-center rounded-full bg-emerald-100 px-1.5 py-0.5 font-bold text-emerald-700">{m.compare_lowest_badge()}</span>
          {m.compare_legend_lowest()}
        </span>
        <span>{m.compare_legend_pipeline()}</span>
      </div>

      <!-- Share link -->
      <button
        type="button"
        onclick={copyLink}
        class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-600 hover:border-gray-300 hover:text-gray-800 transition-colors shadow-sm"
      >
        {#if copied}
          <svg class="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
          {m.compare_link_copied()}
        {:else}
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 1 1.242 7.244" />
          </svg>
          {m.compare_share_comparison()}
        {/if}
      </button>
    </div>

    <!-- ── Data attribution ───────────────────────────────────────────────── -->
    <p class="text-[10px] text-gray-400 leading-relaxed">
      <strong class="text-gray-500">{m.compare_attrib_prices_volume_label()}</strong> {m.compare_attrib_prices_volume_text()} ·
      <strong class="text-gray-500">{m.compare_attrib_rental_yield_label()}</strong> {m.compare_attrib_rental_yield_text({ year: String(rentalYear) })} ·
      <strong class="text-gray-500">{m.compare_attrib_service_charges_label()}</strong> {m.compare_attrib_service_charges_text()} ·
      <strong class="text-gray-500">{m.compare_attrib_supply_pipeline_label()}</strong> {m.compare_attrib_supply_pipeline_text()}.
      {m.compare_attrib_footer()}
    </p>

  {/if}

</div>
