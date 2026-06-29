<script lang="ts">
  import { base } from '$app/paths';
  import rawScores from '$lib/data/district_scores.json';
  import ScoreMethodology from '$lib/components/ui/ScoreMethodology.svelte';
  import PdfLeadMagnet from '$lib/components/ui/PdfLeadMagnet.svelte';
  import { m } from '$lib/paraglide/messages.js';

  type ScoreEntry = {
    slug: string;
    district_name: string;
    score: number;
    score_type?: 'yield_stability' | 'growth_early_cycle' | 'both';
    ready_pct_alltime?: number;
    trend_direction: string;
    color: string;
    tx_count_12m: number;
    median_psf_12m: number | null;
    offplan_pct: number;
    ys?: { total: number };
    gec?: { total: number };
  };

  const scores = rawScores as Record<string, ScoreEntry>;

  const ranked = Object.values(scores).sort((a, b) => b.score - a.score);
  const totalCount = ranked.length;
  const PAGE_SIZE = 10;

  let showAll = $state(false);
  let visible = $derived(showAll ? ranked : ranked.slice(0, PAGE_SIZE));

  function scoreColor(score: number) {
    if (score >= 75) return { text: 'text-emerald-600', bar: 'bg-emerald-500' };
    if (score >= 50) return { text: 'text-amber-600',   bar: 'bg-amber-400' };
    return              { text: 'text-red-600',          bar: 'bg-red-500' };
  }

  function trendIcon(dir: string) {
    if (dir === 'up') return { icon: '↑', cls: 'text-emerald-600' };
    if (dir === 'down') return { icon: '↓', cls: 'text-red-500' };
    return { icon: '→', cls: 'text-gray-400' };
  }

  function fmt(n: number | null) {
    if (n == null) return '—';
    return n.toLocaleString('en-AE');
  }

  function scoreTypeLabel(type: string | undefined) {
    if (type === 'yield_stability')    return { label: m.districts_legend_yield_stability(),    cls: 'bg-emerald-100 text-emerald-800' };
    if (type === 'growth_early_cycle') return { label: m.districts_legend_growth_early_cycle(), cls: 'bg-blue-100 text-blue-800' };
    if (type === 'both')               return { label: m.districts_legend_dual_market(),          cls: 'bg-violet-100 text-violet-800' };
    return                                    { label: m.districts_score_type_na(),                    cls: 'bg-gray-100 text-gray-500' };
  }
</script>

<svelte:head>
  <title>Abu Dhabi District Investment Rankings — All Districts | ADInteract</title>
  <meta name="description" content="Every Abu Dhabi district ranked by investment score using a dual scoring model: Yield & Stability for established districts, Growth & Early-Cycle for new freehold areas. Powered by live ADREC data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="mb-6">
    <h1 class="text-xl font-bold text-gray-900 mb-1">{m.districts_page_title()}</h1>
    <p class="text-sm text-gray-500 max-w-2xl">
      {m.districts_page_intro({ count: String(totalCount), pageSize: String(Math.min(PAGE_SIZE, totalCount)) })}
    </p>
  </div>

  <!-- Score type legend -->
  <div class="flex flex-wrap gap-2 mb-5 text-xs">
    <span class="flex items-center gap-1.5 rounded-full bg-emerald-100 text-emerald-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block"></span>
      {m.districts_legend_yield_stability()}
    </span>
    <span class="flex items-center gap-1.5 rounded-full bg-blue-100 text-blue-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-blue-600 inline-block"></span>
      {m.districts_legend_growth_early_cycle()}
    </span>
    <span class="flex items-center gap-1.5 rounded-full bg-violet-100 text-violet-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-violet-600 inline-block"></span>
      {m.districts_legend_dual_market()}
    </span>
  </div>

  <!-- ── Desktop table (md+) ─────────────────────────────────────────── -->
  <div class="hidden md:block rounded-2xl border border-gray-200 overflow-hidden bg-white">
    <div class="grid grid-cols-[2rem_1fr_9rem_5rem_5rem_6rem_5rem_7rem] items-center gap-2 px-5 py-3 bg-gray-50 border-b border-gray-100 text-[10px] font-bold uppercase tracking-widest text-gray-400">
      <span>{m.districts_th_rank()}</span>
      <span>{m.districts_th_district()}</span>
      <span>{m.districts_th_score_type()}</span>
      <span class="text-center">{m.districts_th_score()}</span>
      <span class="text-center">{m.districts_th_trend()}</span>
      <span class="text-end">{m.districts_th_psf()}</span>
      <span class="text-end">{m.districts_th_sales_12m()}</span>
      <span class="text-end">{m.districts_th_offplan_pct()}</span>
    </div>

    {#each visible as district, i}
      {@const c = scoreColor(district.score)}
      {@const t = trendIcon(district.trend_direction)}
      {@const st = scoreTypeLabel(district.score_type)}
      <a
        href="{base}/area/{district.slug}"
        class="grid grid-cols-[2rem_1fr_9rem_5rem_5rem_6rem_5rem_7rem] items-center gap-2 px-5 py-4 border-b border-gray-100 last:border-0 bg-white hover:bg-gray-50 transition-colors no-underline group"
      >
        <span class="text-sm font-bold {i < 3 ? 'text-amber-500' : 'text-gray-300'}">{i + 1}</span>

        <div class="min-w-0">
          <p class="text-sm font-semibold text-gray-900 group-hover:text-brand-700 transition-colors truncate">{district.district_name}</p>
          <div class="mt-1.5 flex flex-col gap-0.5 w-full max-w-[12rem]">
            {#if district.ys}
              <div class="h-1 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full rounded-full bg-emerald-400/80" style="width:{district.ys.total}%"></div>
              </div>
            {/if}
            {#if district.gec}
              <div class="h-1 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full rounded-full bg-blue-400/80" style="width:{district.gec?.total ?? 0}%"></div>
              </div>
            {/if}
          </div>
        </div>

        <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {st.cls} truncate">{st.label}</span>

        <div class="flex flex-col items-center gap-0.5">
          {#if district.score_type === 'both' && district.ys && district.gec}
            <div class="flex flex-col items-center gap-0.5 w-full">
              <div class="flex items-center gap-1">
                <span class="text-[9px] font-bold text-emerald-600">Y&S</span>
                <span class="text-sm font-black text-emerald-600">{district.ys.total}</span>
              </div>
              <div class="w-8 h-0.5 rounded-full bg-gray-100 overflow-hidden">
                <div class="bg-emerald-400 h-full rounded-full" style="width:{district.ys.total}%"></div>
              </div>
              <div class="flex items-center gap-1 mt-0.5">
                <span class="text-[9px] font-bold text-blue-600">G&EC</span>
                <span class="text-sm font-black text-blue-600">{district.gec.total}</span>
              </div>
              <div class="w-8 h-0.5 rounded-full bg-gray-100 overflow-hidden">
                <div class="bg-blue-400 h-full rounded-full" style="width:{district.gec.total}%"></div>
              </div>
            </div>
          {:else}
            <span class="text-base font-black {c.text}">{district.score}</span>
            <div class="w-8 h-1 rounded-full bg-gray-100 overflow-hidden">
              <div class="{c.bar} h-full rounded-full" style="width:{district.score}%"></div>
            </div>
          {/if}
        </div>

        <span class="text-base font-bold text-center {t.cls}">{t.icon}</span>
        <span class="text-sm text-end text-gray-600">{district.median_psf_12m ? fmt(district.median_psf_12m) : '—'}</span>
        <span class="text-sm text-end text-gray-600">{fmt(district.tx_count_12m)}</span>
        <span class="text-sm text-end text-gray-600">{district.offplan_pct ?? '—'}%</span>
      </a>
    {/each}
  </div>

  <!-- ── Mobile cards (< md) ─────────────────────────────────────────── -->
  <div class="md:hidden space-y-2">
    {#each visible as district, i}
      {@const c = scoreColor(district.score)}
      {@const t = trendIcon(district.trend_direction)}
      {@const st = scoreTypeLabel(district.score_type)}
      <a
        href="{base}/area/{district.slug}"
        class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3.5 no-underline hover:bg-gray-50 transition-colors group"
      >
        <!-- Rank -->
        <span class="text-sm font-black w-5 flex-shrink-0 {i < 3 ? 'text-amber-500' : 'text-gray-300'}">{i + 1}</span>

        <!-- District info -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-gray-900 group-hover:text-brand-700 truncate leading-tight">{district.district_name}</p>
          <div class="mt-1 flex items-center gap-1.5 flex-wrap">
            <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {st.cls}">{st.label}</span>
            <span class="text-[10px] {t.cls} font-bold">{t.icon}</span>
          </div>
          <div class="mt-1.5 flex flex-col gap-0.5 w-full max-w-[10rem]">
            {#if district.ys}
              <div class="h-1 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full rounded-full bg-emerald-400/80" style="width:{district.ys.total}%"></div>
              </div>
            {/if}
            {#if district.gec}
              <div class="h-1 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full rounded-full bg-blue-400/80" style="width:{district.gec?.total ?? 0}%"></div>
              </div>
            {/if}
          </div>
        </div>

        <!-- Score -->
        <div class="flex flex-col items-center flex-shrink-0 w-14">
          {#if district.score_type === 'both' && district.ys && district.gec}
            <div class="flex items-center gap-1">
              <span class="text-[9px] font-bold text-emerald-600">Y&S</span>
              <span class="text-base font-black text-emerald-600 leading-none">{district.ys.total}</span>
            </div>
            <div class="w-8 h-0.5 rounded-full bg-gray-100 overflow-hidden mt-0.5">
              <div class="bg-emerald-400 h-full rounded-full" style="width:{district.ys.total}%"></div>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span class="text-[9px] font-bold text-blue-600">G&EC</span>
              <span class="text-base font-black text-blue-600 leading-none">{district.gec.total}</span>
            </div>
            <div class="w-8 h-0.5 rounded-full bg-gray-100 overflow-hidden mt-0.5">
              <div class="bg-blue-400 h-full rounded-full" style="width:{district.gec.total}%"></div>
            </div>
          {:else}
            <span class="text-xl font-black {c.text} leading-none">{district.score}</span>
            <span class="text-[9px] text-gray-400 mt-0.5">/ 100</span>
            <div class="w-8 h-1 rounded-full bg-gray-100 overflow-hidden mt-1">
              <div class="{c.bar} h-full rounded-full" style="width:{district.score}%"></div>
            </div>
          {/if}
        </div>
      </a>
    {/each}
  </div>

  {#if !showAll && totalCount > PAGE_SIZE}
    <div class="mt-4 flex justify-center">
      <button
        type="button"
        onclick={() => showAll = true}
        class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 hover:border-brand-300 hover:text-brand-700 transition-colors"
      >
        {m.districts_show_all({ count: String(totalCount) })}
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
    </div>
  {:else if showAll && totalCount > PAGE_SIZE}
    <div class="mt-4 flex justify-center">
      <button
        type="button"
        onclick={() => showAll = false}
        class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 hover:border-brand-300 hover:text-brand-700 transition-colors"
      >
        {m.districts_show_top({ pageSize: String(PAGE_SIZE) })}
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" />
        </svg>
      </button>
    </div>
  {/if}

  <p class="mt-3 text-[10px] text-gray-400">{m.districts_tap_hint()}</p>
  <p class="mt-1 text-[10px] text-gray-400">{m.districts_source_footer()}</p>

  <!-- PDF lead magnet -->
  <div class="mt-8">
    <PdfLeadMagnet />
  </div>

  <!-- Methodology -->
  <div class="mt-10 pt-8 border-t border-gray-100">
    <h2 class="text-base font-bold text-gray-900 mb-1">{m.districts_methodology_title()}</h2>
    <p class="text-sm text-gray-500 mb-4">{m.districts_methodology_subtitle()}</p>
    <ScoreMethodology compact={false} />
  </div>

</div>
