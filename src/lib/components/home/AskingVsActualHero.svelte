<script lang="ts">
  import { base } from '$app/paths';
  import { dbReady } from '$lib/stores/db';
  import { query } from '$lib/db/duckdb';
  import rawScores from '$lib/data/district_scores.json';

  type ScoreEntry = { slug: string; tx_count_12m: number };
  const scores = rawScores as Record<string, ScoreEntry>;

  // Top districts by transaction volume (already sorted by score in the JSON)
  const districtOptions = Object.keys(scores).slice(0, 12);
  let selectedDistrict = $state(districtOptions[0]);

  type PriceRow = { median_psf: number | null; cnt: number };
  let offplanPsf  = $state<number | null>(null);
  let readyPsf    = $state<number | null>(null);
  let offplanCnt  = $state(0);
  let readyCnt    = $state(0);
  let loading     = $state(false);

  $effect(() => {
    if (!$dbReady) return;
    loading = true;
    offplanPsf = null;
    readyPsf   = null;

    const district = selectedDistrict;
    const cutoff = new Date();
    cutoff.setMonth(cutoff.getMonth() - 12);
    const cutoffStr = cutoff.toISOString().slice(0, 10);
    const d = district.replace(/'/g, "''");

    Promise.all([
      query<PriceRow>(`
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf,
               COUNT(*) AS cnt
        FROM transactions
        WHERE district = '${d}' AND sale_type = 'off-plan'
          AND rate_per_sqft BETWEEN 50 AND 20000
          AND sale_date >= '${cutoffStr}'
      `),
      query<PriceRow>(`
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf,
               COUNT(*) AS cnt
        FROM transactions
        WHERE district = '${d}' AND sale_type = 'ready'
          AND rate_per_sqft BETWEEN 50 AND 20000
          AND sale_date >= '${cutoffStr}'
      `),
    ]).then(([op, rd]) => {
      offplanPsf = op[0]?.median_psf ? Math.round(op[0].median_psf) : null;
      readyPsf   = rd[0]?.median_psf ? Math.round(rd[0].median_psf) : null;
      offplanCnt = Number(op[0]?.cnt ?? 0);
      readyCnt   = Number(rd[0]?.cnt ?? 0);
      loading    = false;
    }).catch(() => { loading = false; });
  });

  // Gap: (ready - offplan) / offplan * 100
  // Positive = ready trades ABOVE off-plan (capital appreciation for off-plan buyers)
  // Negative = ready trades BELOW off-plan (market hasn't caught up yet)
  let gapPct = $derived(
    offplanPsf && readyPsf
      ? Math.round((readyPsf - offplanPsf) / offplanPsf * 100)
      : null
  );

  function fmt(n: number) { return n.toLocaleString('en-AE'); }
</script>

<div class="rounded-2xl border border-brand-100 bg-gradient-to-br from-[#0F2B1F]/5 to-white px-5 py-5 mb-6">
  <div class="flex flex-wrap items-center justify-between gap-3 mb-1">
    <p class="text-xs font-bold uppercase tracking-widest text-brand-700">Off-plan vs ready market · AED/sqft</p>
    <select
      bind:value={selectedDistrict}
      class="text-xs font-semibold border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
    >
      {#each districtOptions as d}
        <option value={d}>{d}</option>
      {/each}
    </select>
  </div>
  <p class="text-xs text-gray-400 mb-4">Last 12 months · ADREC-registered transactions</p>

  <div class="grid grid-cols-2 gap-4 mb-4">
    <!-- Off-plan -->
    <div class="rounded-xl bg-white border border-gray-100 px-4 py-3">
      <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">Off-plan</p>
      {#if loading}
        <div class="h-6 w-24 bg-gray-100 rounded animate-pulse mb-1"></div>
      {:else if offplanPsf}
        <p class="text-lg font-extrabold text-gray-900">AED {fmt(offplanPsf)}<span class="text-xs font-normal">/sqft</span></p>
        <p class="text-[10px] text-gray-400 mt-0.5">{fmt(offplanCnt)} transactions</p>
      {:else}
        <p class="text-sm text-gray-400 italic">No data</p>
      {/if}
    </div>

    <!-- Ready / secondary -->
    <div class="rounded-xl bg-white border border-brand-100 px-4 py-3">
      <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">Ready / resale</p>
      {#if loading}
        <div class="h-6 w-24 bg-gray-100 rounded animate-pulse mb-1"></div>
      {:else if readyPsf}
        <p class="text-lg font-extrabold text-gray-900">AED {fmt(readyPsf)}<span class="text-xs font-normal">/sqft</span></p>
        <p class="text-[10px] text-gray-400 mt-0.5">{fmt(readyCnt)} transactions</p>
      {:else}
        <p class="text-sm text-gray-400 italic">No data</p>
      {/if}
    </div>
  </div>

  <!-- Gap + interpretation -->
  {#if gapPct !== null}
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-2xl font-black {gapPct >= 0 ? 'text-emerald-600' : 'text-red-500'}">
            {gapPct >= 0 ? '+' : ''}{gapPct}%
          </span>
          <span class="text-sm text-gray-500">
            {gapPct >= 0 ? 'ready trades above off-plan' : 'ready trades below off-plan'}
          </span>
        </div>
        <p class="text-[10px] text-gray-400 mt-1 max-w-xs leading-relaxed">
          {#if gapPct >= 10}
            Completed units command a premium — off-plan buyers have seen strong capital appreciation here.
          {:else if gapPct >= 0}
            Ready market is broadly in line with off-plan pricing — typical for a stable, liquid district.
          {:else if gapPct >= -10}
            Off-plan is slightly pricier than resale — developers pricing in future growth.
          {:else}
            Off-plan trades at a significant premium to resale — high developer confidence or new launch effect.
          {/if}
        </p>
      </div>

      <a
        href="{base}/?district={encodeURIComponent(selectedDistrict)}"
        class="text-xs font-semibold text-brand-700 hover:text-brand-900 underline underline-offset-2 flex-shrink-0"
      >
        Explore {selectedDistrict} →
      </a>
    </div>
  {:else if !loading}
    <p class="text-xs text-gray-400">Insufficient data for this district in the last 12 months.</p>
  {/if}

  <p class="mt-3 text-[10px] text-gray-400">Source: ADREC via ADInteract.co · updated daily</p>
</div>
