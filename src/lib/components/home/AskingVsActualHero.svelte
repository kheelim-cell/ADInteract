<script lang="ts">
  import { base } from '$app/paths';
  import { dbReady } from '$lib/stores/db';
  import { query } from '$lib/db/duckdb';
  import rawEstimates from '$lib/data/asking_estimates.json';

  type AskingEstimate = {
    district: string;
    property_type: string;
    bedroom_type: string;
    estimated_asking_psf: number;
    source: string;
    updated_at: string;
  };

  const estimates = rawEstimates as AskingEstimate[];
  // AED is pegged to USD; fetch live rate from config on mount as a nice-to-have
  let usdRate = $state(3.6725);

  const districtOptions = estimates.map((e) => e.district);
  let selectedDistrict = $state(districtOptions[0]);

  let asking = $derived(estimates.find((e) => e.district === selectedDistrict));
  let actualPsf = $state<number | null>(null);
  let txCount = $state<number>(0);
  let loading = $state(false);

  // Fetch exchange rate once on mount (non-blocking)
  $effect(() => {
    fetch(`${base}/data/config.json`)
      .then((r) => r.json())
      .then((cfg) => { if (cfg?.usd_aed_rate) usdRate = cfg.usd_aed_rate; })
      .catch(() => {});
  });

  $effect(() => {
    if (!$dbReady || !asking) return;
    loading = true;
    actualPsf = null;
    const district = asking.district;
    const layout = asking.bedroom_type;
    const cutoff = new Date();
    cutoff.setMonth(cutoff.getMonth() - 12);
    const cutoffStr = cutoff.toISOString().slice(0, 10);

    query<{ median_psf: number | null; cnt: number }>(`
      SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf,
        COUNT(*) AS cnt
      FROM transactions
      WHERE district = '${district.replace(/'/g, "''")}'
        AND layout = '${layout.replace(/'/g, "''")}'
        AND sale_type = 'ready'
        AND rate_per_sqft BETWEEN 50 AND 20000
        AND sale_date >= '${cutoffStr}'
    `).then((rows) => {
      if (rows[0]?.median_psf) {
        actualPsf = Math.round(rows[0].median_psf);
        txCount = Number(rows[0].cnt);
      }
      loading = false;
    }).catch(() => { loading = false; });
  });

  let gapPct = $derived(
    asking && actualPsf
      ? Math.round((asking.estimated_asking_psf - actualPsf) / asking.estimated_asking_psf * 100)
      : null
  );

  function fmt(n: number) { return n.toLocaleString('en-AE'); }
  function fmtUsd(aed: number) { return Math.round(aed / usdRate).toLocaleString('en-US'); }
</script>

<div class="rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50/60 to-white px-5 py-5 mb-6">
  <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
    <p class="text-xs font-bold uppercase tracking-widest text-amber-700">What buyers actually paid vs. asking price</p>
    <select
      bind:value={selectedDistrict}
      class="text-xs font-semibold border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-amber-400"
    >
      {#each districtOptions as d}
        <option value={d}>{d}</option>
      {/each}
    </select>
  </div>

  {#if asking}
    <p class="text-sm font-medium text-gray-600 mb-4">
      {selectedDistrict} · {asking.bedroom_type} apartment · secondary market
    </p>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <!-- Asking price -->
      <div class="rounded-xl bg-white border border-gray-100 px-4 py-3">
        <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">
          Asking <span class="normal-case">(PF / Bayut)</span>
        </p>
        <p class="text-lg font-bold text-gray-400">
          AED {fmt(asking.estimated_asking_psf)}<span class="text-xs font-normal">/sqft</span>
        </p>
        <p class="text-xs text-gray-300 mt-0.5">≈ USD {fmtUsd(asking.estimated_asking_psf)}</p>
      </div>

      <!-- Actual ADREC price -->
      <div class="rounded-xl bg-white border border-amber-200 px-4 py-3">
        <p class="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">
          Actual paid <span class="normal-case">(ADREC)</span>
        </p>
        {#if loading}
          <div class="h-6 w-24 bg-gray-100 rounded animate-pulse mb-1"></div>
        {:else if actualPsf}
          <p class="text-lg font-extrabold text-gray-900">
            AED {fmt(actualPsf)}<span class="text-xs font-normal">/sqft</span>
          </p>
          <p class="text-xs text-gray-400 mt-0.5">≈ USD {fmtUsd(actualPsf)}</p>
        {:else}
          <p class="text-sm text-gray-400 italic">No ready-market data</p>
        {/if}
      </div>
    </div>

    <!-- Gap + CTA -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      {#if gapPct !== null}
        <div class="flex items-center gap-2">
          <span class="text-2xl font-black {gapPct > 0 ? 'text-emerald-600' : 'text-red-500'}">
            {gapPct > 0 ? '−' : '+'}{Math.abs(gapPct)}%
          </span>
          <span class="text-sm text-gray-500">
            {gapPct > 0 ? 'below asking' : 'above asking'}
            {#if txCount > 0}· <span class="text-xs text-gray-400">{fmt(txCount)} sales</span>{/if}
          </span>
        </div>
      {/if}

      <a
        href="{base}/?district={encodeURIComponent(selectedDistrict)}&saleType=ready"
        class="text-xs font-semibold text-amber-700 hover:text-amber-900 underline underline-offset-2"
      >
        Explore {selectedDistrict} data →
      </a>
    </div>

    <p class="mt-3 text-[10px] text-gray-400 leading-relaxed">
      * Asking price estimated from Property Finder / Bayut active listings (updated {asking.updated_at}).
      Transaction price is the ADREC-registered median for ready/secondary sales, last 12 months.
    </p>
  {/if}
</div>
