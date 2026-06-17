<script lang="ts">
  import { base } from '$app/paths';
  import rawScores from '$lib/data/district_scores.json';

  type ScoreEntry = {
    slug: string;
    district_name: string;
    score: number;
    score_trend: number;
    score_volume: number;
    score_value: number;
    score_offplan: number;
    trend_direction: string;
    color: string;
    tx_count_12m: number;
    median_psf_12m: number | null;
    offplan_pct: number;
  };

  const scores = rawScores as Record<string, ScoreEntry>;

  const ranked = Object.values(scores)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

  function scoreColor(score: number) {
    if (score >= 75) return { bg: 'bg-emerald-500/15', text: 'text-emerald-400', bar: 'bg-emerald-500' };
    if (score >= 50) return { bg: 'bg-amber-500/15', text: 'text-amber-400', bar: 'bg-amber-400' };
    return { bg: 'bg-red-500/15', text: 'text-red-400', bar: 'bg-red-500' };
  }

  function trendIcon(dir: string) {
    if (dir === 'up') return { icon: '↑', cls: 'text-emerald-400' };
    if (dir === 'down') return { icon: '↓', cls: 'text-red-400' };
    return { icon: '→', cls: 'text-white/40' };
  }

  function fmt(n: number | null) {
    if (n == null) return '—';
    return n.toLocaleString('en-AE');
  }
</script>

<svelte:head>
  <title>Abu Dhabi District Investment Scores — Top 10 Ranked | ADInteract</title>
  <meta name="description" content="Top 10 Abu Dhabi districts ranked by investment score: price trend, transaction volume, value vs market, and off-plan activity. Powered by live ADREC data." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="mb-6">
    <h1 class="text-xl font-bold text-white mb-1">District Investment Scores</h1>
    <p class="text-sm text-white/40">
      Top 10 Abu Dhabi districts ranked by composite investment score — price trend, volume, value vs market, and off-plan activity.
      Scores update daily from ADREC transaction data.
    </p>
  </div>

  <!-- Leaderboard -->
  <div class="rounded-2xl border border-white/8 overflow-hidden">

    <!-- Header -->
    <div class="grid grid-cols-[2.5rem_1fr_5rem_5rem_6rem_5rem_7rem] items-center gap-3 px-5 py-3 bg-white/4 border-b border-white/8 text-[10px] font-bold uppercase tracking-widest text-white/30">
      <span>#</span>
      <span>District</span>
      <span class="text-center">Score</span>
      <span class="text-center">Trend</span>
      <span class="text-right hidden sm:block">Median AED/sqft</span>
      <span class="text-right hidden sm:block">Sales (12m)</span>
      <span class="text-right hidden sm:block">Off-plan %</span>
    </div>

    {#each ranked as district, i}
      {@const c = scoreColor(district.score)}
      {@const t = trendIcon(district.trend_direction)}
      <a
        href="{base}/area/{district.slug}"
        class="grid grid-cols-[2.5rem_1fr_5rem_5rem_6rem_5rem_7rem] items-center gap-3 px-5 py-4 border-b border-white/5 last:border-0
               bg-transparent hover:bg-white/4 transition-colors no-underline group"
      >
        <!-- Rank -->
        <span class="text-sm font-bold {i < 3 ? 'text-amber-400' : 'text-white/25'}">{i + 1}</span>

        <!-- Name + sub-scores bar -->
        <div class="min-w-0">
          <p class="text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors truncate">{district.district_name}</p>
          <!-- Sub-score bar -->
          <div class="mt-1.5 flex gap-0.5 h-1.5">
            <div class="rounded-full bg-emerald-500/70" style="width:{district.score_trend / 25 * 100}%; max-width:25%"></div>
            <div class="rounded-full bg-blue-400/70"    style="width:{district.score_volume / 25 * 100}%; max-width:25%"></div>
            <div class="rounded-full bg-violet-400/70"  style="width:{district.score_value / 25 * 100}%; max-width:25%"></div>
            <div class="rounded-full bg-amber-400/70"   style="width:{district.score_offplan / 25 * 100}%; max-width:25%"></div>
          </div>
          <p class="mt-0.5 text-[9px] text-white/20">trend · volume · value · off-plan</p>
        </div>

        <!-- Score badge -->
        <div class="flex flex-col items-center gap-1">
          <span class="text-base font-black {c.text}">{district.score}</span>
          <div class="w-10 h-1 rounded-full bg-white/10 overflow-hidden">
            <div class="{c.bar} h-full rounded-full" style="width:{district.score}%"></div>
          </div>
        </div>

        <!-- Trend -->
        <span class="text-base font-bold text-center {t.cls}">{t.icon}</span>

        <!-- Stats (hidden on mobile) -->
        <span class="text-sm text-right text-white/60 hidden sm:block">
          {district.median_psf_12m ? 'AED ' + fmt(district.median_psf_12m) : '—'}
        </span>
        <span class="text-sm text-right text-white/60 hidden sm:block">{fmt(district.tx_count_12m)}</span>
        <span class="text-sm text-right text-white/60 hidden sm:block">{district.offplan_pct ?? '—'}%</span>
      </a>
    {/each}
  </div>

  <!-- Legend -->
  <div class="mt-4 flex flex-wrap gap-4 text-[10px] text-white/30">
    <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500/70 inline-block"></span>Price trend</span>
    <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-blue-400/70 inline-block"></span>Transaction volume</span>
    <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-violet-400/70 inline-block"></span>Value vs AD median</span>
    <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-400/70 inline-block"></span>Off-plan activity</span>
    <span class="ml-auto">Click any district to view the full report →</span>
  </div>

  <p class="mt-3 text-[10px] text-white/20">Source: ADREC via ADInteract.co · scores recalculated daily</p>

</div>
