<script lang="ts">
  import { metadata, dbReady } from '$lib/stores/db';
  import { query } from '$lib/db/duckdb';
  import PropertyUpload, { type ExtractionData } from '$lib/components/investors/PropertyUpload.svelte';
  import { base } from '$app/paths';
  import { buildDealUrl, type OffplanDealSnapshot } from '$lib/utils/dealShare';
  import { m } from '$lib/paraglide/messages.js';

  // ── Helpers ─────────────────────────────────────────────────────────────────
  function fmtAed(v: number): string {
    if (!isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number, dp = 1): string {
    if (!isFinite(v)) return '—';
    return v.toFixed(dp) + '%';
  }

  // ── Constants ────────────────────────────────────────────────────────────────
  const LAYOUT_ORDER = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds', '5+ beds', '6+ beds'];
  const LAYOUT_DISPLAY: Record<string, string> = { studio: 'Studio' };
  const PINNED_DISTRICTS = [
    'Al Reem Island', 'Yas Island', 'Al Saadiyat Island', 'Al Rahah',
    'Khalifa City', 'Al Reef', 'Fahid Island', 'Al Hidayriyyat',
  ];

  // ── Derived: districts + layouts ─────────────────────────────────────────────
  let pinnedCount = $derived.by(() =>
    PINNED_DISTRICTS.filter(p => ($metadata?.districts ?? []).some((d: string) => d.toLowerCase() === p.toLowerCase())).length
  );
  let districts = $derived.by(() => {
    const all: string[] = $metadata?.districts ?? [];
    const pinnedFound = PINNED_DISTRICTS.filter(p => all.some(d => d.toLowerCase() === p.toLowerCase()));
    const pinnedSet   = new Set(pinnedFound.map(p => p.toLowerCase()));
    const rest        = all.filter(d => !pinnedSet.has(d.toLowerCase())).sort();
    return [...pinnedFound, ...rest];
  });
  let layouts = $derived(
    ($metadata?.layouts ?? [])
      .filter((l: string) => LAYOUT_ORDER.includes(l.toLowerCase()))
      .sort((a: string, b: string) => LAYOUT_ORDER.indexOf(a.toLowerCase()) - LAYOUT_ORDER.indexOf(b.toLowerCase()))
  );

  // ── Shared class strings ─────────────────────────────────────────────────────
  const inp       = 'w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30';
  const sel       = 'w-full bg-[#141414] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 appearance-none cursor-pointer';
  // White background = field requires manual input (not auto-populated from ADREC or filter dropdowns)
  const inpManual = 'w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-900 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-400/30';
  const selManual = 'w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-900 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-400/30 appearance-none cursor-pointer';

  // ── Unit inputs ──────────────────────────────────────────────────────────────
  let district = $state('');
  let layout   = $state('');
  let cost     = $state(1_000_000);
  let size     = $state(945);

  const handoverAdminFee = 5_000;

  // ── Rental inputs (defaults 0 as requested) ──────────────────────────────────
  let comparableRent    = $state(50_000);
  let yearsTillHandover = $state(2);
  let rentalAppPct      = $state(15);
  let furnishingType    = $state<'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality'>('none');
  let furnishingPct     = $derived(furnishingType === 'basic_airbnb' ? 10 : furnishingType === 'highend_airbnb' ? 20 : furnishingType === 'branded_hospitality' ? 25 : 0);
  let maidsRoom         = $state<'no' | 'yes'>('no');
  let maidsPct          = $derived.by(() => {
    if (maidsRoom !== 'yes') return 0;
    const l = layout.toLowerCase();
    if (l === '2 beds') return 10;
    if (l === '3 beds') return 15;
    return 0;
  });
  let mgmtFeePct        = $state(0);
  let utilitiesMonthly  = $state(0);
  let serviceChargePsf  = $state(15);

  // ── Capital gains inputs ─────────────────────────────────────────────────────
  let yearsToResale   = $state(5);
  let annualAppPct    = $state(12);
  let otherFactorType = $state<'no' | 'yes'>('no');
  let otherAppPct     = $derived(otherFactorType === 'yes' ? 10 : 0);
  let resaleBrokerPct = $state(2);

  // Auto-sync capital gains "furnished/branded" toggle with furnishing selection
  $effect(() => {
    otherFactorType = (furnishingType === 'highend_airbnb' || furnishingType === 'branded_hospitality')
      ? 'yes'
      : 'no';
  });

  // ── AI Property Scanner ──────────────────────────────────────────────────────
  let scannedFields = $state<Set<string>>(new Set());
  let scannedMeta   = $state<{ projectName: string | null; developer: string | null } | null>(null);

  function handleExtraction(data: ExtractionData) {
    const filled = new Set<string>();

    // District — case-insensitive match against available districts
    if (data.district) {
      const lc    = data.district.toLowerCase();
      const match = (districts as string[]).find(d => d.toLowerCase() === lc)
        ?? (districts as string[]).find(d => d.toLowerCase().includes(lc) || lc.includes(d.toLowerCase()));
      if (match) { district = match; filled.add('district'); }
    }

    // Layout — normalise and match
    if (data.layout) {
      const lc    = data.layout.toLowerCase().trim();
      const match = (layouts as string[]).find(l => l.toLowerCase() === lc)
        ?? (layouts as string[]).find(l => l.toLowerCase().includes(lc) || lc.includes(l.toLowerCase()));
      if (match) { layout = match; filled.add('layout'); }
    }

    if (data.cost   && data.cost   > 0) { cost              = data.cost;                                     filled.add('cost'); }
    if (data.size   && data.size   > 0) { size              = Math.round(data.size);                         filled.add('size'); }
    if (data.yearsTillHandover != null) { yearsTillHandover = Math.max(0, Math.round(data.yearsTillHandover * 2) / 2); filled.add('yearsTillHandover'); }
    if (data.serviceChargePsf  > 0)    { serviceChargePsf  = data.serviceChargePsf;                         filled.add('serviceChargePsf'); }

    scannedMeta   = { projectName: data.projectName, developer: data.developer };
    scannedFields = filled;
  }

  // Fields that the scanner couldn't fill — shown as a prompt to the user
  const ALL_SCANNER_FIELDS: [string, string][] = [
    ['district',         m.calc_field_district()],
    ['layout',           m.calc_field_layout()],
    ['cost',             m.calc_field_price()],
    ['size',             m.calc_field_size()],
    ['yearsTillHandover',m.calc_years_till_handover_label()],
  ];

  let missingAfterScan = $derived.by(() => {
    if (scannedFields.size === 0) return [];
    return ALL_SCANNER_FIELDS.filter(([key]) => !scannedFields.has(key)).map(([, label]) => label);
  });

  // ── Derived: unit ────────────────────────────────────────────────────────────
  let pricePerSqft       = $derived(size > 0 ? cost / size : 0);
  let registrationFee    = $derived(cost * 0.02 + 1_000);
  let devRegistrationFee = $derived(cost < 500_000 ? 2_000 : 4_000);
  let totalPurchaseCost  = $derived(cost + registrationFee + devRegistrationFee + handoverAdminFee);

  // ── Derived: rental ──────────────────────────────────────────────────────────
  let baseRentalAfterGrowth = $derived(comparableRent * Math.pow(1 + rentalAppPct / 100, yearsTillHandover));
  let afterFurnishing       = $derived(baseRentalAfterGrowth * (1 + furnishingPct / 100));
  let grossRental           = $derived(afterFurnishing * (1 + maidsPct / 100));
  let mgmtFee       = $derived(grossRental * mgmtFeePct / 100);
  let utilities     = $derived(utilitiesMonthly * 12);
  let serviceCharge = $derived(size * serviceChargePsf * 1.05);
  let netRental     = $derived(grossRental - mgmtFee - utilities - serviceCharge);

  let grossYield      = $derived(cost > 0 ? (grossRental / cost) * 100 : 0);
  let netYield        = $derived(totalPurchaseCost > 0 ? (netRental / totalPurchaseCost) * 100 : 0);
  let paybackYears    = $derived(netYield > 0 ? 100 / netYield : 0);
  let rentalObjective = $derived(netYield >= 7);

  // ── Derived: capital gains ────────────────────────────────────────────────────
  let sellingPrice     = $derived(cost * Math.pow(1 + annualAppPct / 100, yearsToResale) * (1 + otherAppPct / 100));
  let resaleBrokerFee  = $derived(sellingPrice * resaleBrokerPct / 100);
  let totalAllInCost   = $derived(totalPurchaseCost + resaleBrokerFee);
  let netProfit        = $derived(sellingPrice - totalAllInCost);
  let netProfitPct     = $derived(totalAllInCost > 0 ? (netProfit / totalAllInCost) * 100 : 0);
  let netProfitPerYear = $derived(
    yearsToResale > 0 && totalAllInCost > 0
      ? (Math.pow(sellingPrice / totalAllInCost, 1 / yearsToResale) - 1) * 100
      : 0
  );
  let capitalObjective = $derived(netProfitPerYear >= 7);
  let totalRoiPa       = $derived(netYield + netProfitPerYear);

  // ── Auto-populate: comparable rent (2025 median, district + layout) ───────────
  let rentLoading = $state(false);
  let rentSource  = $state('');

  $effect(() => {
    if (!$dbReady) return;
    const d = district;
    const l = layout;
    const rentalLayout = l ? l : 'all beds';
    const layoutFilter = `LOWER(layout) = '${rentalLayout.replace(/'/g, "''").toLowerCase()}'`;
    const baseWhere    = `year = 2025 AND ${layoutFilter} AND typology = 'All property types' AND rent_type = 'All types' AND median_rent > 0`;
    const distClause   = d ? `AND district = '${d.replace(/'/g, "''")}'` : '';
    rentLoading = true;
    query<{ median_rent: number }>(`
      SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent
      FROM rental WHERE ${baseWhere} ${distClause}
    `).then(rows => {
      const val = rows[0]?.median_rent;
      if (val && val > 0) {
        comparableRent = Math.round(val);
        rentSource = [d, l].filter(Boolean).join(' · ') || 'Abu Dhabi · all';
      }
      rentLoading = false;
    }).catch(() => { rentLoading = false; });
  });

  // ── Auto-populate: rental YoY appreciation (2024→2025 median, 50% haircut) ───
  let rentalYoyLoading = $state(false);
  let rentalYoySource  = $state('');

  $effect(() => {
    if (!$dbReady) return;
    const d = district;
    const l = layout;
    const rentalLayout = l ? l : 'all beds';
    const layoutFilter = `LOWER(layout) = '${rentalLayout.replace(/'/g, "''").toLowerCase()}'`;
    const baseWhere    = `typology = 'All property types' AND rent_type = 'All types' AND median_rent > 0 AND ${layoutFilter}`;
    const distClause   = d ? `AND district = '${d.replace(/'/g, "''")}'` : '';
    rentalYoyLoading = true;
    Promise.all([
      query<{ median_rent: number }>(`SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent FROM rental WHERE ${baseWhere} AND year = 2025 ${distClause}`),
      query<{ median_rent: number }>(`SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent FROM rental WHERE ${baseWhere} AND year = 2024 ${distClause}`),
    ]).then(([curr, prev]) => {
      const c = curr[0]?.median_rent;
      const p = prev[0]?.median_rent;
      if (c && p && p > 0) {
        rentalAppPct    = Math.min(10, Math.max(0, parseFloat(((c - p) / p * 100 * 0.5).toFixed(1))));
        rentalYoySource = [d, l].filter(Boolean).join(' · ') || 'Abu Dhabi · all';
      }
      rentalYoyLoading = false;
    }).catch(() => { rentalYoyLoading = false; });
  });

  // ── Share link ───────────────────────────────────────────────────────────────
  let shareCopied = $state(false);

  function shareAnalysis() {
    const snapshot: OffplanDealSnapshot = {
      v: 1,
      type: 'offplan',
      projectName:        scannedMeta?.projectName  ?? undefined,
      developer:          scannedMeta?.developer     ?? undefined,
      district,
      layout,
      cost,
      size,
      comparableRent,
      yearsTillHandover,
      rentalAppPct,
      furnishingType,
      maidsRoom,
      mgmtFeePct,
      utilitiesMonthly,
      serviceChargePsf,
      yearsToResale,
      annualAppPct,
      otherFactorType,
      resaleBrokerPct,
      // pre-computed outputs
      pricePerSqft,
      registrationFee,
      devRegistrationFee,
      totalPurchaseCost,
      grossRental,
      netRental,
      grossYield,
      netYield,
      sellingPrice,
      netProfit,
      netProfitPct,
      netProfitPerYear,
      totalRoiPa,
    };
    const url = buildDealUrl(snapshot, window.location.origin, base);
    navigator.clipboard.writeText(url).then(() => {
      shareCopied = true;
      setTimeout(() => { shareCopied = false; }, 2500);
    });
  }

  // ── Auto-populate: capital gains YoY (off-plan PSF, last 12 vs prior 12, 50% haircut) ──
  let capYoyLoading = $state(false);
  let capYoySource  = $state('');

  $effect(() => {
    if (!$dbReady) return;
    const d = district;
    const l = layout;
    const parts: string[] = [];
    if (d) parts.push(`district = '${d.replace(/'/g, "''")}'`);
    if (l) parts.push(`LOWER(TRIM(layout)) = '${l.replace(/'/g, "''").toLowerCase()}'`);
    const filterClause = parts.length ? 'AND ' + parts.join(' AND ') : '';
    const source       = [d, l].filter(Boolean).join(' · ') || 'Abu Dhabi · all off-plan';
    const baseWhere    = `LOWER(TRIM(sale_type)) = 'off-plan' AND rate_per_sqft > 0`;
    capYoyLoading = true;
    Promise.all([
      query<{ median_psf: number }>(`SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf FROM transactions WHERE ${baseWhere} AND sale_date >= (CURRENT_DATE - INTERVAL '12 months') ${filterClause}`),
      query<{ median_psf: number }>(`SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf FROM transactions WHERE ${baseWhere} AND sale_date >= (CURRENT_DATE - INTERVAL '24 months') AND sale_date < (CURRENT_DATE - INTERVAL '12 months') ${filterClause}`),
    ]).then(([currRows, prevRows]) => {
      const curr = currRows[0]?.median_psf;
      const prev = prevRows[0]?.median_psf;
      if (curr && prev && prev > 0) {
        annualAppPct = Math.min(10, Math.max(0, parseFloat(((curr - prev) / prev * 100 * 0.5).toFixed(1))));
        capYoySource = source;
      }
      capYoyLoading = false;
    }).catch(() => { capYoyLoading = false; });
  });
</script>

{#snippet scannedBadge(field: string)}
  {#if scannedFields.has(field)}
    <span class="ml-1 inline-flex items-center gap-0.5 text-[9px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/25 rounded px-1.5 py-0.5 leading-none">
      ✓ AI
    </span>
  {/if}
{/snippet}

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="rounded-2xl border border-white/10 bg-[#1e1e1e] overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-white/8 flex items-center gap-3">
    <div class="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center flex-shrink-0">
      <svg class="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" />
      </svg>
    </div>
    <div>
      <h4 class="text-sm font-bold text-white">{m.calc_offplan_title()}</h4>
      <p class="text-xs text-white/40 mt-0.5">{m.calc_offplan_subtitle()}</p>
    </div>
  </div>

  <!-- ── AI Property Scanner ──────────────────────────────────────────────── -->
  <div class="px-5 py-4 border-b border-white/8 space-y-2">
    <PropertyUpload onExtracted={handleExtraction} />

    <!-- Project info extracted -->
    {#if scannedMeta?.projectName || scannedMeta?.developer}
      <div class="flex items-center gap-1.5 text-xs flex-wrap">
        {#if scannedMeta.projectName}
          <span class="font-semibold text-amber-400/80">{scannedMeta.projectName}</span>
        {/if}
        {#if scannedMeta.developer}
          <span class="text-white/30">{m.calc_by()}</span>
          <span class="text-white/50">{scannedMeta.developer}</span>
        {/if}
      </div>
    {/if}

    <!-- Missing fields prompt -->
    {#if missingAfterScan.length > 0}
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-white/30">{m.calc_still_needs_manual()}</span>
        {#each missingAfterScan as field}
          <span class="text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-400/70 rounded px-1.5 py-0.5 leading-none">{field}</span>
        {/each}
      </div>
    {/if}
  </div>

  <div class="p-5 grid grid-cols-1 xl:grid-cols-2 gap-6">

    <!-- ── LEFT: Inputs ──────────────────────────────────────────────────────── -->
    <div class="space-y-5">

      <!-- Unit Details -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-amber-400/80 uppercase tracking-widest">{m.calc_unit_details_title()}</legend>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_field_district()}</span>
              {@render scannedBadge('district')}
            </div>
            <div class="relative">
              <select bind:value={district} class={sel}>
                <option value="">{m.calc_district_all()}</option>
                {#if districts.length > 0}
                  <optgroup label={m.calc_optgroup_popular()}>
                    {#each districts.slice(0, pinnedCount) as d}
                      <option value={d}>{d}</option>
                    {/each}
                  </optgroup>
                  <optgroup label={m.calc_optgroup_all_districts()}>
                    {#each districts.slice(pinnedCount) as d}
                      <option value={d}>{d}</option>
                    {/each}
                  </optgroup>
                {/if}
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
          <div class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_field_layout()}</span>
              {@render scannedBadge('layout')}
            </div>
            <div class="relative">
              <select bind:value={layout} class={sel}>
                <option value="">{m.calc_layout_select()}</option>
                {#each layouts as l}
                  <option value={l}>{LAYOUT_DISPLAY[l.toLowerCase()] ?? l}</option>
                {/each}
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_field_price()}</span>
              {@render scannedBadge('cost')}
            </div>
            <input type="number" bind:value={cost} min="0" step="10000" class={scannedFields.has('cost') ? inp : inpManual} />
          </label>
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_field_size()}</span>
              {@render scannedBadge('size')}
            </div>
            <input type="number" bind:value={size} min="0" step="10" class={scannedFields.has('size') ? inp : inpManual} />
          </label>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="rounded-lg bg-amber-500/8 border border-amber-500/20 px-3 py-2.5">
            <p class="text-[10px] text-amber-400/70 uppercase tracking-wider">{m.calc_price_per_sqft_label()}</p>
            <p class="text-base font-black text-amber-400 tabular-nums mt-0.5">
              {size > 0 ? Math.round(pricePerSqft).toLocaleString('en-AE') : '—'} <span class="text-xs font-semibold text-amber-400/60">AED/sqft</span>
            </p>
          </div>
          <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5">
            <p class="text-[10px] text-white/35 uppercase tracking-wider">{m.calc_total_acquisition_cost_label()}</p>
            <p class="text-sm font-bold text-white/70 tabular-nums mt-0.5">{fmtAed(totalPurchaseCost)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">{m.calc_total_acquisition_breakdown({ devFee: cost < 500_000 ? '2,000' : '4,000' })}</p>
          </div>
        </div>
      </fieldset>

      <!-- Rental Analysis -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-emerald-400/80 uppercase tracking-widest">{m.calc_rental_analysis_title()}</legend>

        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_comparable_rent_label()}</span>
            <input type="number" bind:value={comparableRent} min="0" step="1000" class={inp} />
            {#if rentLoading}
              <p class="text-[10px] text-white/30 pl-0.5">{m.calc_loading_median_rent()}</p>
            {:else if rentSource}
              <p class="text-[10px] text-emerald-400/60 pl-0.5">{m.calc_median_rent_source({ source: rentSource })}</p>
            {/if}
          </label>
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_years_till_handover_label()}</span>
              {@render scannedBadge('yearsTillHandover')}
            </div>
            <input type="number" bind:value={yearsTillHandover} min="0" max="10" step="0.5" class={scannedFields.has('yearsTillHandover') ? inp : inpManual} />
          </label>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_rental_appreciation_label()}</span>
            <input type="number" bind:value={rentalAppPct} min="0" max="10" step="0.5" class={inp} />
            {#if rentalYoyLoading}
              <p class="text-[10px] text-white/30 pl-0.5">{m.calc_loading_rental_yoy()}</p>
            {:else if rentalYoySource}
              <p class="text-[10px] text-amber-400/60 pl-0.5">{m.calc_rental_yoy_source({ source: rentalYoySource })}</p>
            {/if}
          </label>
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_furnishing_label()}</span>
            <div class="relative">
              <select bind:value={furnishingType} class={selManual}>
                <option value="none">{m.calc_furnishing_none()}</option>
                <option value="basic_airbnb">{m.calc_furnishing_basic()}</option>
                <option value="highend_airbnb">{m.calc_furnishing_highend()}</option>
                <option value="branded_hospitality">{m.calc_furnishing_branded()}</option>
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_maids_room_label()}</span>
            <div class="relative">
              <select bind:value={maidsRoom} class={selManual}>
                <option value="no">{m.calc_maids_no()}</option>
                <option value="yes">{maidsPct > 0 ? m.calc_maids_yes_pct({ pct: String(maidsPct) }) : m.calc_maids_yes_plain()}</option>
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
            {#if maidsRoom === 'yes' && maidsPct === 0}
              <p class="text-[10px] text-white/30 pl-0.5">{m.calc_maids_hint()}</p>
            {/if}
          </div>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 items-end">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_mgmt_fee_label()}</span>
            <input type="number" bind:value={mgmtFeePct} min="0" max="30" step="0.5" class={inpManual} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_utilities_label()}</span>
            <input type="number" bind:value={utilitiesMonthly} min="0" step="100" class={inpManual} />
          </label>
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_service_charge_label()}</span>
              {@render scannedBadge('serviceChargePsf')}
            </div>
            <input type="number" bind:value={serviceChargePsf} min="0" step="0.5" class={scannedFields.has('serviceChargePsf') ? inp : inpManual} />
          </label>
        </div>
        <p class="text-[11px] text-white/30 pl-0.5">
          {m.calc_service_charge_formula({ size: size.toLocaleString('en-AE'), rate: String(serviceChargePsf) })} <span class="text-amber-400/70">{fmtAed(serviceCharge)}/yr</span>
        </p>
      </fieldset>

      <!-- Capital Gains -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-blue-400/80 uppercase tracking-widest">{m.calc_capital_gains_title()}</legend>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_resale_time_offplan_label()}</span>
            <input type="number" bind:value={yearsToResale} min="0" max="5" step="1" class={inpManual} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_annual_appreciation_label()}</span>
            <input type="number" bind:value={annualAppPct} min="0" max="10" step="0.5" class={inp} />
            {#if capYoyLoading}
              <p class="text-[10px] text-white/30 pl-0.5">{m.calc_loading_offplan_yoy()}</p>
            {:else if capYoySource}
              <p class="text-[10px] text-amber-400/60 pl-0.5">{m.calc_offplan_yoy_source({ source: capYoySource })}</p>
            {/if}
          </label>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_furnishing_label()}</span>
            <div class="relative">
              <select bind:value={otherFactorType} class={selManual}>
                <option value="no">{m.calc_maids_no()}</option>
                <option value="yes">{m.calc_finish_branding_yes()}</option>
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_resale_broker_fee_label()}</span>
            <input type="number" bind:value={resaleBrokerPct} min="0" max="5" step="0.25" class={inpManual} />
          </label>
        </div>

        <p class="text-[11px] text-white/30 pl-0.5">
          {m.calc_selling_price_formula_offplan({ cost: fmtAed(cost), pct: String(annualAppPct), years: String(yearsToResale), extra: otherAppPct > 0 ? ` × (1 + ${otherAppPct}%)` : '' })} <span class="text-amber-400/70">{fmtAed(sellingPrice)}</span>
        </p>
      </fieldset>

    </div><!-- end left -->

    <!-- ── RIGHT: Results ────────────────────────────────────────────────────── -->
    <div class="rounded-xl border border-amber-300/60 bg-white overflow-hidden shadow-lg shadow-amber-900/10">

      <!-- Results header bar -->
      <div class="px-4 py-3 border-b border-amber-200 flex items-center justify-between bg-gradient-to-r from-amber-50 to-amber-100/60">
        <div class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
          </svg>
          <span class="text-[10px] font-bold text-gray-900 uppercase tracking-widest">{m.calc_estimated_returns()}</span>
        </div>
        <div class="flex gap-1.5">
          <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide border {rentalObjective ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-600 border-red-200'}">
            {rentalObjective ? m.calc_yield_pass() : m.calc_yield_fail()}
          </span>
          <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide border {capitalObjective ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-600 border-red-200'}">
            {capitalObjective ? m.calc_cagr_pass() : m.calc_cagr_fail()}
          </span>
        </div>
      </div>

      <div class="p-4 space-y-4 bg-gradient-to-b from-white to-amber-50/40">

        <!-- KPI hero strip -->
        <div class="grid grid-cols-3 divide-x divide-amber-200 rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white overflow-hidden shadow-sm">
          <div class="px-3 py-4 text-center">
            <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_net_rental_yield_pa()}</p>
            <p class="text-xl sm:text-3xl font-black tabular-nums mt-1.5 leading-none {netYield >= 7 ? 'text-emerald-600' : netYield >= 5 ? 'text-amber-600' : 'text-red-600'}">{fmtPct(netYield)}</p>
            <p class="text-[9px] text-gray-500 mt-1">{m.calc_on_total_cost()}</p>
          </div>
          <div class="px-3 py-4 text-center">
            <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_capital_gain_pa()}</p>
            <p class="text-xl sm:text-3xl font-black tabular-nums mt-1.5 leading-none {netProfitPerYear >= 7 ? 'text-emerald-600' : netProfitPerYear >= 5 ? 'text-amber-600' : 'text-red-600'}">{fmtPct(netProfitPerYear)}</p>
            <p class="text-[9px] text-gray-500 mt-1">{m.calc_yr_horizon({ years: String(yearsToResale) })}</p>
          </div>
          <div class="px-3 py-4 text-center">
            <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_total_roi_pa()}</p>
            <p class="text-xl sm:text-3xl font-black tabular-nums mt-1.5 leading-none {totalRoiPa >= 14 ? 'text-emerald-600' : totalRoiPa >= 7 ? 'text-amber-600' : 'text-red-600'}">{fmtPct(totalRoiPa)}</p>
            <p class="text-[9px] text-gray-500 mt-1">{m.calc_yield_plus_capital()}</p>
          </div>
        </div>

        <!-- Rental breakdown -->
        <div class="rounded-xl border border-amber-200 bg-white overflow-hidden shadow-sm">
          <div class="px-3.5 py-2.5 border-b border-amber-100 bg-amber-50">
            <h5 class="text-[10px] font-bold text-gray-900 uppercase tracking-widest">{m.calc_rental_income_at_handover_title()}</h5>
          </div>
          <div class="px-3.5 py-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-gray-500">
              <span>Comparable rent × (1 + {rentalAppPct}%)^{yearsTillHandover}yr</span>
              <span class="tabular-nums text-gray-700 font-medium">{fmtAed(baseRentalAfterGrowth)}</span>
            </div>
            {#if furnishingPct > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_furnishing_premium({ pct: String(furnishingPct) })}</span>
                <span class="tabular-nums text-emerald-600">+ {fmtAed(baseRentalAfterGrowth * furnishingPct / 100)}</span>
              </div>
            {/if}
            {#if maidsPct > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_maids_premium({ pct: String(maidsPct) })}</span>
                <span class="tabular-nums text-emerald-600">+ {fmtAed(afterFurnishing * maidsPct / 100)}</span>
              </div>
            {/if}
            <div class="flex justify-between font-semibold text-gray-800 border-t border-amber-100 pt-1.5">
              <span>{m.calc_gross_rental_revenue()}</span>
              <span class="tabular-nums">{fmtAed(grossRental)}</span>
            </div>
            {#if mgmtFee > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_mgmt_fee_line({ pct: String(mgmtFeePct) })}</span>
                <span class="tabular-nums text-red-500">− {fmtAed(mgmtFee)}</span>
              </div>
            {/if}
            {#if utilities > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_utilities_line()}</span>
                <span class="tabular-nums text-red-500">− {fmtAed(utilities)}</span>
              </div>
            {/if}
            <div class="flex justify-between text-gray-500">
              <span>{m.calc_service_charge_vat_line()}</span>
              <span class="tabular-nums text-red-500">− {fmtAed(serviceCharge)}</span>
            </div>
            <div class="flex justify-between font-bold text-gray-800 border-t border-amber-100 pt-1.5">
              <span>{m.calc_net_annual_revenue()}</span>
              <span class="tabular-nums {netRental >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(netRental)}</span>
            </div>
          </div>
          <!-- Monthly cashflow callout -->
          <div class="mx-3.5 mb-3.5 rounded-lg border px-3.5 py-2.5 flex items-center justify-between {netRental >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}">
            <span class="text-xs font-semibold {netRental >= 0 ? 'text-emerald-700' : 'text-red-700'}">{m.calc_monthly_net_cashflow()}</span>
            <span class="text-xl font-black tabular-nums {netRental >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(netRental / 12)}</span>
          </div>
        </div>

        <!-- Capital Gains breakdown -->
        <div class="rounded-xl border border-amber-200 bg-white overflow-hidden shadow-sm">
          <div class="px-3.5 py-2.5 border-b border-amber-100 bg-amber-50">
            <h5 class="text-[10px] font-bold text-gray-900 uppercase tracking-widest">{m.calc_capital_gains_horizon_title({ years: String(yearsToResale) })}</h5>
          </div>
          <div class="px-3.5 py-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-gray-500">
              <span>Potential selling price (@ {annualAppPct}%/yr{otherAppPct > 0 ? ` + ${otherAppPct}% finish` : ''})</span>
              <span class="tabular-nums text-gray-700 font-medium">{fmtAed(sellingPrice)}</span>
            </div>
            <div class="flex justify-between gap-2 text-gray-500">
              <span class="min-w-0">{m.calc_total_purchase_cost()}</span>
              <span class="tabular-nums text-red-500 flex-shrink-0">− {fmtAed(cost + registrationFee + devRegistrationFee + handoverAdminFee)}</span>
            </div>
            <div class="flex justify-between gap-2 text-gray-500">
              <span class="min-w-0">{m.calc_resale_broker_fee_line()} ({resaleBrokerPct}%)</span>
              <span class="tabular-nums text-red-500 flex-shrink-0">− {fmtAed(resaleBrokerFee)}</span>
            </div>
            <div class="flex justify-between font-bold text-gray-800 border-t border-amber-100 pt-1.5">
              <span>{m.calc_net_profit()}</span>
              <span class="tabular-nums {netProfit >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(netProfit)}</span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2 mx-3.5 mb-3.5">
            <div class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2.5 text-center">
              <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_total_return()}</p>
              <p class="text-xl font-black tabular-nums mt-1 {netProfitPct >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtPct(netProfitPct)}</p>
              <p class="text-[9px] text-gray-500 mt-0.5">{m.calc_on_all_in_cost()}</p>
            </div>
            <div class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2.5 text-center">
              <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_net_profit()}</p>
              <p class="text-xl font-black tabular-nums mt-1 {netProfit >= 0 ? 'text-emerald-600' : 'text-red-600'}">
                {netProfit >= 0 ? '+' : ''}{Math.abs(netProfit) >= 1_000_000 ? (netProfit / 1_000_000).toFixed(2) + 'M' : Math.round(Math.abs(netProfit) / 1000) + 'K'}
              </p>
              <p class="text-[9px] text-gray-500 mt-0.5">{m.calc_aed()}</p>
            </div>
          </div>
        </div>

        <!-- Share button -->
        <button
          type="button"
          onclick={shareAnalysis}
          class="w-full flex items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-xs font-semibold text-gray-700 hover:border-amber-400 hover:text-amber-700 transition-colors"
        >
          {#if shareCopied}
            <svg class="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            <span class="text-emerald-600">{m.calc_share_link_copied()}</span>
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 1 1.242 7.244" />
            </svg>
            {m.calc_share_button()}
          {/if}
        </button>

        <!-- Disclaimer -->
        <p class="text-[10px] text-gray-400 leading-relaxed px-0.5">
          {m.calc_disclaimer_offplan({ pct: String(annualAppPct), extra: otherAppPct > 0 ? ` + ${otherAppPct}% finish premium applied at resale` : '' })}
        </p>

      </div><!-- end inner padding -->
    </div><!-- end right -->

  </div><!-- end grid -->
</div>
