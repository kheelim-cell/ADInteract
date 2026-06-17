<script lang="ts">
  import rawScores from '$lib/data/district_scores.json';

  let { district }: { district: string } = $props();

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

  let entry = $derived(scores[district] ?? null);

  function scoreColor(score: number): string {
    if (score >= 75) return '#16a34a';
    if (score >= 50) return '#d97706';
    return '#dc2626';
  }

  function scoreBg(score: number): string {
    if (score >= 75) return 'bg-green-50 border-green-100';
    if (score >= 50) return 'bg-amber-50 border-amber-100';
    return 'bg-red-50 border-red-100';
  }

  function trendIcon(dir: string): string {
    if (dir === 'up') return '↑';
    if (dir === 'down') return '↓';
    return '→';
  }

  function trendColor(dir: string): string {
    if (dir === 'up') return 'text-green-600';
    if (dir === 'down') return 'text-red-600';
    return 'text-gray-500';
  }
</script>

{#if entry}
<div class="rounded-xl border {scoreBg(entry.score)} px-5 py-4 mb-6">
  <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-500 mb-3">Investment Score</p>

  <div class="flex items-end gap-4 mb-3">
    <span class="text-4xl font-extrabold leading-none" style="color: {scoreColor(entry.score)}">
      {entry.score}
    </span>
    <span class="text-sm text-gray-400 font-medium pb-1">/ 100</span>
  </div>

  <!-- Progress bar -->
  <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
    <div
      class="h-full rounded-full transition-all"
      style="width: {entry.score}%; background: {scoreColor(entry.score)}"
    ></div>
  </div>

  <!-- Sub-scores -->
  <div class="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
    <div class="flex items-center justify-between">
      <span class="text-gray-500">Price trend</span>
      <span class="font-semibold {trendColor(entry.trend_direction)}">
        {trendIcon(entry.trend_direction)} {entry.score_trend}/25
      </span>
    </div>
    <div class="flex items-center justify-between">
      <span class="text-gray-500">Volume</span>
      <span class="font-semibold text-gray-700">{entry.score_volume}/25</span>
    </div>
    <div class="flex items-center justify-between">
      <span class="text-gray-500">Value vs AD</span>
      <span class="font-semibold text-gray-700">{entry.score_value}/25</span>
    </div>
    <div class="flex items-center justify-between">
      <span class="text-gray-500">Off-plan</span>
      <span class="font-semibold text-gray-700">{entry.score_offplan}/25</span>
    </div>
  </div>

  <p class="mt-3 text-[10px] text-gray-400">
    Based on {entry.tx_count_12m.toLocaleString('en-AE')} transactions · last 12 months · ADREC data
  </p>
</div>
{/if}
