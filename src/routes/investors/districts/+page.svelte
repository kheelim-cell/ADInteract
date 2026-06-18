<script lang="ts">
  import { base } from '$app/paths';
  import rawScores from '$lib/data/district_scores.json';
  import ScoreMethodology from '$lib/components/ui/ScoreMethodology.svelte';

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

  const ranked = Object.values(scores)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

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
    if (type === 'yield_stability')    return { label: 'Yield & Stability',    cls: 'bg-emerald-100 text-emerald-800' };
    if (type === 'growth_early_cycle') return { label: 'Growth & Early-Cycle', cls: 'bg-blue-100 text-blue-800' };
    if (type === 'both')               return { label: 'Dual market',          cls: 'bg-violet-100 text-violet-800' };
    return                                    { label: '—',                    cls: 'bg-gray-100 text-gray-500' };
  }
</script>

<svelte:head>
  <title>Abu Dhabi District Investment Rankings — Top 10 | ADInteract</title>
  <meta name="description" content="Top 10 Abu Dhabi districts ranked by investment score using a dual scoring model: Yield & Stability for established districts, Growth & Early-Cycle for new freehold areas. Powered by live ADREC data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="mb-6">
    <h1 class="text-xl font-bold text-gray-900 mb-1">District Investment Rankings</h1>
    <p class="text-sm text-gray-500 max-w-2xl">
      Top 10 Abu Dhabi districts ranked by a dual scoring model calibrated to each district's market maturity.
      Scores update daily from ADREC transaction data.
    </p>
  </div>

  <!-- Score type legend -->
  <div class="flex flex-wrap gap-2 mb-5 text-xs">
    <span class="flex items-center gap-1.5 rounded-full bg-emerald-100 text-emerald-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block"></span>
      Yield &amp; Stability
    </span>
    <span class="flex items-center gap-1.5 rounded-full bg-blue-100 text-blue-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-blue-600 inline-block"></span>
      Growth &amp; Early-Cycle
    </span>
    <span class="flex items-center gap-1.5 rounded-full bg-violet-100 text-violet-800 px-3 py-1 font-semibold">
      <span class="w-1.5 h-1.5 rounded-full bg-violet-600 inline-block"></span>
      Dual market
    </span>
  </div>

  <!-- ── Desktop table (md+) ─────────────────────────────────────────── -->
  <div class="hidden md:block rounded-2xl border border-gray-200 overflow-hidden bg-white">
    <div class="grid grid-cols-[2rem_1fr_9rem_5rem_5rem_6rem_5rem_7rem] items-center gap-2 px-5 py-3 bg-gray-50 border-b border-gray-100 text-[10px] font-bold uppercase tracking-widest text-gray-400">
      <span>#</span>
      <span>District</span>
      <span>Score type</span>
      <span class="text-center">Score</span>
      <span class="text-center">Trend</span>
      <span class="text-right">AED/sqft</span>
      <span class="text-right">Sales 12m</span>
      <span class="text-right">Off-plan %</span>
    </div>

    {#each ranked as district, i}
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
          <div class="mt-1.5 flex gap-0.5 h-1.5">
            {#if district.ys}
              <div class="rounded-full bg-emerald-400/80" style="width:{district.ys.total}%; max-width:50%"></div>
            {/if}
            {#if district.gec}
              <div class="rounded-full bg-blue-400/80" style="width:{district.gec?.total ?? 0}%; max-width:50%"></div>
            {/if}
          </div>
          <p class="mt-0.5 text-[9px] text-gray-400">
            {district.score_type === 'both' ? 'Y&S · G&EC' : district.score_type === 'yield_stability' ? 'yield · liquidity · stability' : 'velocity · momentum · appreciation'}
          </p>
        </div>

        <span class="text-[10px] font-bold rounded-full px-2 py-0.5 {st.cls} truncate">{st.label}</span>

        <div class="flex flex-col items-center gap-1">
          <span class="text-base font-black {c.text}">{district.score}</span>
          <div class="w-8 h-1 rounded-full bg-gray-100 overflow-hidden">
            <div class="{c.bar} h-full rounded-full" style="width:{district.score}%"></div>
          </div>
        </div>

        <span class="text-base font-bold text-center {t.cls}">{t.icon}</span>
        <span class="text-sm text-right text-gray-600">{district.median_psf_12m ? fmt(district.median_psf_12m) : '—'}</span>
        <span class="text-sm text-right text-gray-600">{fmt(district.tx_count_12m)}</span>
        <span class="text-sm text-right text-gray-600">{district.offplan_pct ?? '—'}%</span>
      </a>
    {/each}
  </div>

  <!-- ── Mobile cards (< md) ─────────────────────────────────────────── -->
  <div class="md:hidden space-y-2">
    {#each ranked as district, i}
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
          <div class="mt-1.5 flex gap-0.5 h-1">
            {#if district.ys}
              <div class="rounded-full bg-emerald-400/80" style="width:{district.ys.total}%; max-width:50%"></div>
            {/if}
            {#if district.gec}
              <div class="rounded-full bg-blue-400/80" style="width:{district.gec?.total ?? 0}%; max-width:50%"></div>
            {/if}
          </div>
        </div>

        <!-- Score -->
        <div class="flex flex-col items-center flex-shrink-0 w-12">
          <span class="text-xl font-black {c.text} leading-none">{district.score}</span>
          <span class="text-[9px] text-gray-400 mt-0.5">/ 100</span>
          <div class="w-8 h-1 rounded-full bg-gray-100 overflow-hidden mt-1">
            <div class="{c.bar} h-full rounded-full" style="width:{district.score}%"></div>
          </div>
        </div>
      </a>
    {/each}
  </div>

  <p class="mt-3 text-[10px] text-gray-400">Tap any district to view the full report with per-factor breakdown →</p>
  <p class="mt-1 text-[10px] text-gray-400">Source: ADREC via ADInteract.co · scores recalculated daily</p>

  <!-- Methodology -->
  <div class="mt-10 pt-8 border-t border-gray-100">
    <h2 class="text-base font-bold text-gray-900 mb-1">Score methodology</h2>
    <p class="text-sm text-gray-500 mb-4">Dual scoring logic, factor weights, global benchmark comparison, and FAQs.</p>
    <ScoreMethodology compact={false} />
  </div>

</div>
