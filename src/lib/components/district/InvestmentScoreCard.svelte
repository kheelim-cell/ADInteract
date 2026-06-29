<script lang="ts">
  import rawScores from '$lib/data/district_scores.json';
  import ScoreMethodology from '$lib/components/ui/ScoreMethodology.svelte';

  let { district }: { district: string } = $props();

  type SubScore = { score: number; max: number; [key: string]: unknown };
  type YS = {
    total: number;
    momentum:     SubScore & { pct_change: number | null; direction: string };
    yield:        SubScore & { gross_yield_pct: number | null };
    liquidity:    SubScore & { recency_ratio: number | null };
    stability:    SubScore & { cov: number | null };
    appreciation: SubScore & { ratio: number | null };
  };
  type GEC = {
    total: number;
    velocity:    SubScore & { velocity_ratio: number | null };
    momentum:    SubScore & { pct_change: number | null; direction: string };
    appreciation:SubScore & { ratio: number | null };
    developer:   SubScore & { project_growth_ratio: number | null };
    entry:       SubScore & { entry_ratio: number | null };
  };
  type ScoreEntry = {
    slug: string;
    district_name: string;
    score: number;
    score_type: 'yield_stability' | 'growth_early_cycle' | 'both';
    ready_pct_alltime: number;
    trend_direction: string;
    tx_count_12m: number;
    median_psf_12m: number | null;
    offplan_pct: number;
    color: string;
    ys?: YS;
    gec?: GEC;
    // legacy fields (pre-dual-score build, still present until next CI run)
    score_trend?: number;
    score_volume?: number;
    score_value?: number;
    score_offplan?: number;
  };

  const scores = rawScores as Record<string, ScoreEntry>;
  let entry = $derived(scores[district] ?? null);

  function scoreColor(score: number) {
    if (score >= 75) return { text: 'text-emerald-600', ring: 'border-emerald-200 bg-emerald-50' };
    if (score >= 50) return { text: 'text-amber-600',   ring: 'border-amber-200 bg-amber-50' };
    return              { text: 'text-red-600',          ring: 'border-red-200 bg-red-50' };
  }

  function barColor(score: number) {
    if (score >= 75) return '#16a34a';
    if (score >= 50) return '#d97706';
    return '#dc2626';
  }

  function fmtPct(n: number | null | undefined, prefix = '') {
    if (n == null) return '—';
    return `${prefix}${n > 0 ? '+' : ''}${n}%`;
  }

  function fmtRatio(n: number | null | undefined) {
    if (n == null) return '—';
    return `${n.toFixed(2)}×`;
  }

  // Legacy fallback — JSON produced before the dual-score rewrite
  let isLegacy = $derived(entry != null && !entry.score_type);
</script>

{#if entry}
  {@const c = scoreColor(entry.score)}
  <div class="rounded-xl border {c.ring} px-5 py-4 mb-6">

    <!-- Header row -->
    <div class="flex items-start justify-between gap-3 mb-3">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-500 mb-1">Investment Score</p>
        <div class="flex items-end gap-3">
          <span class="text-4xl font-extrabold leading-none {c.text}">{entry.score}</span>
          <span class="text-sm text-gray-400 font-medium pb-1">/ 100</span>
        </div>
      </div>

      {#if !isLegacy}
        {#if entry.score_type === 'yield_stability'}
          <span class="mt-1 inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-bold text-emerald-800 uppercase tracking-wider flex-shrink-0">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block"></span>
            Yield &amp; Stability
          </span>
        {:else if entry.score_type === 'growth_early_cycle'}
          <span class="mt-1 inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-1 text-[10px] font-bold text-blue-800 uppercase tracking-wider flex-shrink-0">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-600 inline-block"></span>
            Growth &amp; Early-Cycle
          </span>
        {:else}
          <span class="mt-1 inline-flex items-center gap-1 rounded-full bg-violet-100 px-2.5 py-1 text-[10px] font-bold text-violet-800 uppercase tracking-wider flex-shrink-0">
            <span class="w-1.5 h-1.5 rounded-full bg-violet-600 inline-block"></span>
            Dual market
          </span>
        {/if}
      {/if}
    </div>

    <!-- Progress bar -->
    <div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden mb-4">
      <div class="h-full rounded-full" style="width:{entry.score}%; background:{barColor(entry.score)}"></div>
    </div>

    {#if isLegacy}
      <!-- ── Legacy sub-scores (pre-dual-score JSON) ── -->
      <div class="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
        <div class="flex items-center justify-between">
          <span class="text-gray-500">Price trend</span>
          <span class="font-semibold text-gray-700">{entry.score_trend ?? '—'}/25</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-500">Volume</span>
          <span class="font-semibold text-gray-700">{entry.score_volume ?? '—'}/25</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-500">Value vs AD</span>
          <span class="font-semibold text-gray-700">{entry.score_value ?? '—'}/25</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-500">Off-plan</span>
          <span class="font-semibold text-gray-700">{entry.score_offplan ?? '—'}/25</span>
        </div>
      </div>

    {:else if entry.score_type === 'yield_stability' && entry.ys}
      <!-- ── Yield & Stability breakdown ── -->
      <div class="space-y-2 text-xs">
        {#each [
          { label: 'Price momentum (ready)', score: entry.ys.momentum.score, max: 30,
            detail: entry.ys.momentum.pct_change != null ? fmtPct(entry.ys.momentum.pct_change) + ' YoY (ready)' : 'Insufficient ready data' },
          { label: 'Gross rental yield',     score: entry.ys.yield.score,    max: 25,
            detail: entry.ys.yield.gross_yield_pct != null ? entry.ys.yield.gross_yield_pct + '% gross yield' : 'No rental registrations' },
          { label: 'Liquidity',              score: entry.ys.liquidity.score, max: 20,
            detail: entry.ys.liquidity.recency_ratio != null ? fmtRatio(entry.ys.liquidity.recency_ratio) + ' recency ratio' : '—' },
          { label: 'Price stability',        score: entry.ys.stability.score, max: 15,
            detail: entry.ys.stability.cov != null ? 'CoV ' + entry.ys.stability.cov : 'Limited history' },
          { label: 'Appreciation signal',    score: entry.ys.appreciation.score, max: 10,
            detail: entry.ys.appreciation.ratio != null ? fmtRatio(entry.ys.appreciation.ratio) + ' ready/off-plan' : 'One sale type only' },
        ] as row}
          <div class="flex items-center gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex justify-between mb-0.5">
                <span class="text-gray-600 truncate">{row.label}</span>
                <span class="font-semibold text-gray-800 flex-shrink-0 ms-2">{row.score}/{row.max}</span>
              </div>
              <div class="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-emerald-400 rounded-full" style="width:{row.score/row.max*100}%"></div>
              </div>
              <p class="text-[10px] text-gray-400 mt-0.5">{row.detail}</p>
            </div>
          </div>
        {/each}
      </div>

    {:else if entry.score_type === 'growth_early_cycle' && entry.gec}
      <!-- ── Growth & Early-Cycle breakdown ── -->
      <div class="space-y-2 text-xs">
        {#each [
          { label: 'Off-plan velocity',     score: entry.gec.velocity.score,    max: 30,
            detail: entry.gec.velocity.velocity_ratio != null ? fmtRatio(entry.gec.velocity.velocity_ratio) + ' last 6m vs prior 6m' : 'Insufficient data' },
          { label: 'Off-plan momentum',     score: entry.gec.momentum.score,    max: 25,
            detail: entry.gec.momentum.pct_change != null ? fmtPct(entry.gec.momentum.pct_change) + ' off-plan PSF YoY' : 'Insufficient data' },
          { label: 'Appreciation signal',   score: entry.gec.appreciation.score, max: 20,
            detail: entry.gec.appreciation.ratio != null ? fmtRatio(entry.gec.appreciation.ratio) + ' ready/off-plan' : 'No completions yet' },
          { label: 'Developer activity',    score: entry.gec.developer.score,   max: 15,
            detail: entry.gec.developer.project_growth_ratio != null ? fmtRatio(entry.gec.developer.project_growth_ratio) + ' project growth' : '—' },
          { label: 'Market entry momentum', score: entry.gec.entry.score,       max: 10,
            detail: entry.gec.entry.entry_ratio != null ? fmtRatio(entry.gec.entry.entry_ratio) + ' entry ratio' : '—' },
        ] as row}
          <div class="flex-1 min-w-0">
            <div class="flex justify-between mb-0.5">
              <span class="text-gray-600 truncate">{row.label}</span>
              <span class="font-semibold text-gray-800 flex-shrink-0 ms-2">{row.score}/{row.max}</span>
            </div>
            <div class="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-blue-400 rounded-full" style="width:{row.score/row.max*100}%"></div>
            </div>
            <p class="text-[10px] text-gray-400 mt-0.5">{row.detail}</p>
          </div>
        {/each}
      </div>

    {:else if entry.score_type === 'both' && entry.ys && entry.gec}
      <!-- ── Dual: show both totals + top-level bars ── -->
      <div class="grid grid-cols-2 gap-3 text-xs mb-2">
        <div class="rounded-lg bg-white border border-emerald-100 px-3 py-2">
          <p class="text-[9px] font-bold uppercase tracking-widest text-emerald-600 mb-1">Yield &amp; Stability</p>
          <p class="text-2xl font-extrabold text-emerald-600 leading-none">{entry.ys.total}</p>
          <div class="mt-1.5 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-emerald-400 rounded-full" style="width:{entry.ys.total}%"></div>
          </div>
        </div>
        <div class="rounded-lg bg-white border border-blue-100 px-3 py-2">
          <p class="text-[9px] font-bold uppercase tracking-widest text-blue-600 mb-1">Growth &amp; Early-Cycle</p>
          <p class="text-2xl font-extrabold text-blue-600 leading-none">{entry.gec.total}</p>
          <div class="mt-1.5 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-blue-400 rounded-full" style="width:{entry.gec.total}%"></div>
          </div>
        </div>
      </div>
      <p class="text-[10px] text-gray-400 mb-2">
        This district has an active secondary market and ongoing off-plan activity — both scores apply.
        Click "How is this scored?" below to understand each framework.
      </p>
    {/if}

    <!-- Footer -->
    <p class="mt-3 text-[10px] text-gray-400">
      Based on {entry.tx_count_12m.toLocaleString('en-AE')} transactions · last 12 months · ADREC data
      {#if !isLegacy}· {entry.ready_pct_alltime}% ready all-time{/if}
    </p>

    <!-- Methodology (compact / expandable) -->
    <ScoreMethodology compact={true} />
  </div>
{/if}
