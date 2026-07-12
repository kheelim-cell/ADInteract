<script lang="ts">
  import { metadata, dbReady } from '$lib/stores/db';
  import { query } from '$lib/db/duckdb';
  import { base } from '$app/paths';
  import { onMount } from 'svelte';
  import ReadyPropertyUpload, { type ReadyExtractionData } from '$lib/components/investors/ReadyPropertyUpload.svelte';
  import { buildDealUrl, buildAgentDealUrl, type ReadyDealSnapshot } from '$lib/utils/dealShare';
  import { isAuthenticated, user } from '$lib/stores/auth';
  import MortgageSection from '$lib/components/investors/MortgageSection.svelte';
  import CashFlowProjection from '$lib/components/investors/CashFlowProjection.svelte';

  let mortgageMonthlyPaymentCf = $state(0);
  import { m } from '$lib/paraglide/messages.js';

  // ── Helpers ─────────────────────────────────────────────────────────────────
  function fmtAed(v: number): string {
    if (!isFinite(v) || isNaN(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number, dp = 1): string {
    if (!isFinite(v) || isNaN(v)) return '—';
    return v.toFixed(dp) + '%';
  }
  function toTitleCase(str: string): string {
    return str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }

  // ── Constants ─────────────────────────────────────────────────────────────────
  const LAYOUT_ORDER = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds', '5+ beds', '6+ beds'];
  const LAYOUT_DISPLAY: Record<string, string> = { studio: 'Studio' };
  const PINNED_DISTRICTS = [
    'Al Reem Island', 'Yas Island', 'Al Saadiyat Island', 'Al Rahah',
    'Khalifa City', 'Al Reef', 'Fahid Island', 'Al Hidayriyyat',
  ];

  // ── Loaded data ───────────────────────────────────────────────────────────────
  interface ProjectInfo { project_name: string; district: string; sc_avg: number | null; }
  let readyDistricts   = $state<string[]>([]);
  let allProjects      = $state<ProjectInfo[]>([]);
  let scLookup         = $state<Record<string, number>>({});  // normalised name → sc_avg
  let loadingDistricts = $state(true);

  // ── Derived: layouts ─────────────────────────────────────────────────────────
  let layouts = $derived(
    ($metadata?.layouts ?? [])
      .filter((l: string) => LAYOUT_ORDER.includes(l.toLowerCase()))
      .sort((a: string, b: string) => LAYOUT_ORDER.indexOf(a.toLowerCase()) - LAYOUT_ORDER.indexOf(b.toLowerCase()))
  );

  // ── Derived: ready districts (pinned first) ──────────────────────────────────
  let pinnedCount = $derived.by(() =>
    PINNED_DISTRICTS.filter(p => readyDistricts.some(d => d.toLowerCase() === p.toLowerCase())).length
  );
  let districts = $derived.by(() => {
    const pinnedFound = PINNED_DISTRICTS.filter(p => readyDistricts.some(d => d.toLowerCase() === p.toLowerCase()));
    const pinnedSet   = new Set(pinnedFound.map(p => p.toLowerCase()));
    const rest        = readyDistricts.filter(d => !pinnedSet.has(d.toLowerCase())).sort();
    return [...pinnedFound, ...rest];
  });

  // ── Derived: projects filtered by selected district ───────────────────────────
  let filteredProjects = $derived.by(() => {
    const list = district
      ? allProjects.filter(p => p.district.toLowerCase() === district.toLowerCase())
      : allProjects;
    return [...list].sort((a, b) => a.project_name.localeCompare(b.project_name));
  });

  // ── Shared class strings ─────────────────────────────────────────────────────
  const inp       = 'w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30';
  const sel       = 'w-full bg-[#0a1a10] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 appearance-none cursor-pointer';
  // White background = field requires manual input (not auto-populated from ADREC or filter dropdowns)
  const inpManual = 'w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-900 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-400/30';
  const selManual = 'w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-900 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-400/30 appearance-none cursor-pointer';

  // ── Mortgage LTV matrix ──────────────────────────────────────────────────────
  const LTV_MATRIX: Record<string, [number, number]> = {
    'none|uae_national': [0, 0], 'none|uae_resident': [0, 0], 'none|non_resident': [0, 0],
    '1st|uae_national':  [0.85, 0.75], '1st|uae_resident': [0.80, 0.70], '1st|non_resident': [0.50, 0.50],
    '2nd|uae_national':  [0.65, 0.65], '2nd|uae_resident': [0.60, 0.60], '2nd|non_resident': [0.50, 0.50],
  };

  // ── Inputs ────────────────────────────────────────────────────────────────────
  let district         = $state('');
  let layout           = $state('');
  let project          = $state('');
  let tenancyStatus    = $state<'tenanted' | 'vacant'>('vacant');
  let price            = $state(600_000);
  let livingArea       = $state(413);
  let balconyArea      = $state(45);
  let serviceChargePsf = $state(16);
  let annualRent       = $state(50_000);

  let mortgageType = $state<'none' | '1st' | '2nd'>('1st');
  let residency    = $state<'uae_national' | 'uae_resident' | 'non_resident'>('uae_resident');
  let interestRate = $state(4.35);
  let termYears    = $state(25);

  let comparablePsf   = $state(1_250);
  let yearsToResale   = $state(5);
  let annualAppPct    = $state(4);
  let otherFactorType = $state<'no' | 'yes'>('no');
  let otherAppPct     = $derived(otherFactorType === 'yes' ? 10 : 0);
  let furnishingType  = $state<'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality'>('none');
  let furnishingPct   = $derived(furnishingType === 'basic_airbnb' ? 10 : furnishingType === 'highend_airbnb' ? 20 : furnishingType === 'branded_hospitality' ? 25 : 0);

  // Auto-sync capital gains "furnished/branded" toggle with furnishing selection
  $effect(() => {
    otherFactorType = (furnishingType === 'highend_airbnb' || furnishingType === 'branded_hospitality')
      ? 'yes'
      : 'no';
  });
  let maidsRoom       = $state<'no' | 'yes'>('no');
  let maidsPct        = $derived.by(() => {
    if (maidsRoom !== 'yes') return 0;
    const l = layout.toLowerCase();
    if (l === '2 beds') return 10;
    if (l === '3 beds') return 15;
    return 0;
  });
  let additionalCapex = $state(0);

  // ── Derived: unit ─────────────────────────────────────────────────────────────
  let totalArea     = $derived(livingArea + balconyArea);
  let pricePerSqft  = $derived(totalArea > 0 ? price / totalArea : 0);
  // effectiveRent applies furnishing then maid's room premium on top of base annual rent
  let afterFurnishing = $derived(annualRent * (1 + furnishingPct / 100));
  let effectiveRent   = $derived(afterFurnishing * (1 + maidsPct / 100));

  // ── Derived: LTV & mortgage ──────────────────────────────────────────────────
  let ltvKey               = $derived(`${mortgageType}|${residency}`);
  let ltvRates             = $derived(LTV_MATRIX[ltvKey] ?? [0, 0]);
  let ltv                  = $derived(price >= 5_000_000 ? ltvRates[1] : ltvRates[0]);
  let mortgageAmount       = $derived(price * ltv);
  let downpayment          = $derived(price - mortgageAmount);
  let registrationFee      = $derived(price * 0.02 + 1_000);
  let agencyFee            = $derived(price * 0.02 * 1.05);
  let purchasingFees       = $derived(registrationFee + agencyFee);
  let mortgageAdminFee     = $derived(mortgageType !== 'none' ? 9_400 : 0);
  let equityInjection      = $derived(downpayment + purchasingFees + mortgageAdminFee);
  let monthlyRate          = $derived(interestRate / 100 / 12);
  let nPayments            = $derived(termYears * 12);
  let emi = $derived(
    mortgageType !== 'none' && mortgageAmount > 0 && monthlyRate > 0
      ? mortgageAmount * monthlyRate / (1 - Math.pow(1 + monthlyRate, -nPayments))
      : 0
  );
  let lifeInsurance        = $derived(mortgageAmount * 0.000171);
  let propertyInsurance    = $derived(price * 0.0001);
  let totalMonthlyMortgage = $derived(emi + lifeInsurance + propertyInsurance);
  let annualMortgage       = $derived(totalMonthlyMortgage * 12);
  let mortgageEligible     = $derived(mortgageType === 'none' || mortgageAmount >= 250_000);

  // ── Derived: rental (uses effectiveRent) ─────────────────────────────────────
  let serviceCharge      = $derived((livingArea + balconyArea * 0.25) * serviceChargePsf * 1.05);
  let netAnnualRental    = $derived(effectiveRent - serviceCharge - annualMortgage);
  let monthlyNetCashflow = $derived(netAnnualRental / 12);
  let netYield           = $derived(equityInjection > 0 ? (netAnnualRental / equityInjection) * 100 : 0);
  let rentalObjective    = $derived(netYield >= 7);

  // ── Derived: capital gains ───────────────────────────────────────────────────
  let sellingPrice    = $derived(comparablePsf * livingArea * Math.pow(1 + annualAppPct / 100, yearsToResale) * (1 + otherAppPct / 100));
  let resaleBrokerFee = $derived(sellingPrice * 0.02);
  let netProfit = $derived(
    sellingPrice - price - purchasingFees - mortgageAdminFee - resaleBrokerFee - additionalCapex
  );
  let totalEquityBase  = $derived(equityInjection + additionalCapex);
  let netProfitPct     = $derived(totalEquityBase > 0 ? (netProfit / totalEquityBase) * 100 : 0);
  let netProfitPerYear = $derived(
    yearsToResale > 0 && totalEquityBase > 0
      ? (Math.pow(1 + netProfitPct / 100, 1 / yearsToResale) - 1) * 100
      : 0
  );
  let capitalObjective = $derived(netProfitPerYear >= 7);
  let totalRoiPa      = $derived(netYield + netProfitPerYear);

  // ── Load service_charges.json (static) ───────────────────────────────────────
  onMount(async () => {
    try {
      const res = await fetch(`${base}/data/service_charges.json`);
      if (res.ok) {
        const json = await res.json();
        const scProjects: ProjectInfo[] = (json.projects ?? []).map(
          (p: { project_name: string; district: string; sc_avg: number | null }) => ({
            project_name: p.project_name,
            district:     p.district ?? '',
            sc_avg:       p.sc_avg ?? null,
          })
        );
        const lookup: Record<string, number> = {};
        for (const p of scProjects) {
          if (p.sc_avg != null) lookup[p.project_name.toLowerCase().trim()] = p.sc_avg;
        }
        scLookup    = lookup;
        allProjects = scProjects;
      }
    } catch { /* ignore */ }
  });

  // ── Query ready districts + rental projects once DB is ready ──────────────────
  $effect(() => {
    if (!$dbReady) return;

    query<{ district: string }>(`
      SELECT DISTINCT district FROM transactions
      WHERE LOWER(TRIM(sale_type)) = 'ready'
        AND district IS NOT NULL AND district != ''
      ORDER BY district
    `).then(rows => {
      readyDistricts   = rows.map(r => r.district);
      loadingDistricts = false;
    }).catch(() => { loadingDistricts = false; });

    query<{ project_name: string; district: string }>(`
      SELECT project_name, ANY_VALUE(district) AS district
      FROM rental
      WHERE project_name IS NOT NULL AND TRIM(project_name) != ''
        AND LOWER(project_name) != 'private'
      GROUP BY project_name
      ORDER BY project_name
    `).then(rows => {
      const existingKeys = new Set(allProjects.map(p => p.project_name.toLowerCase().trim()));
      const extra = rows
        .filter(r => !existingKeys.has(r.project_name.toLowerCase().trim()))
        .map(r => ({ project_name: r.project_name, district: r.district ?? '', sc_avg: null as number | null }));
      if (extra.length) allProjects = [...allProjects, ...extra];
    }).catch(() => {});
  });

  // ── Auto-populate service charge when project is selected ─────────────────────
  $effect(() => {
    if (!project || project === 'other') return;
    const sc = scLookup[project.toLowerCase().trim()];
    if (sc != null) serviceChargePsf = sc;
  });

  // ── Reset project when district changes ───────────────────────────────────────
  $effect(() => {
    void district;
    project = '';
  });

  // ── Auto-populate median market rent when Vacant + project/district/layout changes ─────
  let medianRentLoading = $state(false);
  let rentSource = $state<'project' | 'district'>('district');

  $effect(() => {
    if (tenancyStatus !== 'vacant') return;
    if (!$dbReady) return;

    const d  = district;
    const l  = layout;
    const p  = project && project !== 'other' ? project : '';
    const rentalLayout   = l ? l : 'all beds';
    const layoutFilter   = `LOWER(layout) = '${rentalLayout.replace(/'/g, "''").toLowerCase()}'`;
    const baseWhere      = `year = 2025 AND ${layoutFilter} AND typology = 'All property types' AND rent_type = 'All types' AND median_rent > 0`;
    const districtClause = d ? `AND district = '${d.replace(/'/g, "''")}'` : '';

    medianRentLoading = true;

    // Try project-level first (only if a real project is selected)
    const tryProject = p
      ? query<{ median_rent: number }>(`
          SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent
          FROM rental
          WHERE ${baseWhere}
            AND LOWER(TRIM(project_name)) = '${p.replace(/'/g, "''").toLowerCase().trim()}'
        `)
      : Promise.resolve<{ median_rent: number }[]>([]);

    // District/layout fallback
    const tryDistrict = query<{ median_rent: number }>(`
      SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent
      FROM rental
      WHERE ${baseWhere}
        ${districtClause}
    `);

    Promise.all([tryProject, tryDistrict])
      .then(([projRows, distRows]) => {
        const projVal = projRows[0]?.median_rent;
        const distVal = distRows[0]?.median_rent;
        if (projVal && projVal > 0) {
          annualRent = Math.round(projVal);
          rentSource = 'project';
        } else if (distVal && distVal > 0) {
          annualRent = Math.round(distVal);
          rentSource = 'district';
        }
        medianRentLoading = false;
      })
      .catch(() => { medianRentLoading = false; });
  });

  // ── Auto-populate comparable PSF (last 6 months, ready only) ─────────────────
  let psf6mLoading = $state(false);
  let psf6mSource  = $state('');

  $effect(() => {
    if (!$dbReady) return;
    const d = district;
    const l = layout;
    const p = project && project !== 'other' ? project : '';

    let filterClause: string;
    let source: string;
    if (p) {
      filterClause = `AND LOWER(TRIM(project_name)) = '${p.replace(/'/g, "''").toLowerCase().trim()}'`;
      source = toTitleCase(p);
    } else {
      const parts: string[] = [];
      if (d) parts.push(`district = '${d.replace(/'/g, "''")}'`);
      if (l) parts.push(`LOWER(TRIM(layout)) = '${l.replace(/'/g, "''").toLowerCase()}'`);
      filterClause = parts.length ? 'AND ' + parts.join(' AND ') : '';
      source = [d, l].filter(Boolean).join(' · ') || 'Abu Dhabi · all ready';
    }

    psf6mLoading = true;
    query<{ median_psf: number }>(`
      SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf
      FROM transactions
      WHERE LOWER(TRIM(sale_type)) = 'ready'
        AND rate_per_sqft > 0
        AND sale_date >= (CURRENT_DATE - INTERVAL '6 months')
        ${filterClause}
    `).then(rows => {
      const val = rows[0]?.median_psf;
      if (val && val > 0) { comparablePsf = Math.round(val); psf6mSource = source; }
      psf6mLoading = false;
    }).catch(() => { psf6mLoading = false; });
  });

  // ── AI Listing Scanner ────────────────────────────────────────────────────────
  let scannedFields = $state<Set<string>>(new Set());

  function handleReadyExtraction(data: ReadyExtractionData) {
    const filled = new Set<string>();

    // District — case-insensitive match
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

    // Project — fuzzy match against loaded project list
    if (data.project) {
      const lc    = data.project.toLowerCase().trim();
      const match = allProjects.find(p => p.project_name.toLowerCase().trim() === lc)
        ?? allProjects.find(p => p.project_name.toLowerCase().includes(lc) || lc.includes(p.project_name.toLowerCase().trim()));
      if (match) { project = match.project_name; filled.add('project'); }
    }

    if (data.price        && data.price        > 0) { price            = data.price;                        filled.add('price'); }
    if (data.livingArea   && data.livingArea   > 0) { livingArea       = Math.round(data.livingArea);       filled.add('livingArea'); }
    if (data.balconyArea  != null && data.balconyArea >= 0) { balconyArea = Math.round(data.balconyArea);   filled.add('balconyArea'); }
    if (data.serviceChargePsf && data.serviceChargePsf > 0) { serviceChargePsf = data.serviceChargePsf;    filled.add('serviceChargePsf'); }
    if (data.annualRent   && data.annualRent   > 0) {
      annualRent    = data.annualRent;
      tenancyStatus = 'tenanted';
      filled.add('annualRent');
    }

    scannedFields = filled;
  }

  const ALL_SCANNER_FIELDS: [string, string][] = [
    ['district',         m.calc_field_district()],
    ['layout',           m.calc_field_layout()],
    ['project',          m.calc_project_label()],
    ['price',            m.calc_field_price()],
    ['livingArea',       m.calc_living_area_label()],
    ['balconyArea',      m.calc_balcony_label()],
    ['serviceChargePsf', m.calc_scanner_field_service_charge_short()],
  ];

  let missingAfterScan = $derived.by(() => {
    if (scannedFields.size === 0) return [];
    return ALL_SCANNER_FIELDS.filter(([key]) => !scannedFields.has(key)).map(([, label]) => label);
  });

  // ── Share link ───────────────────────────────────────────────────────────────
  let shareCopied = $state(false);
  let shareProfileCopied = $state(false);

  function buildSnapshot(): ReadyDealSnapshot {
    return {
      v: 1,
      type: 'ready',
      district,
      layout,
      project,
      tenancyStatus,
      price,
      livingArea,
      balconyArea,
      serviceChargePsf,
      annualRent,
      mortgageType,
      residency,
      interestRate,
      termYears,
      comparablePsf,
      yearsToResale,
      annualAppPct,
      otherFactorType,
      furnishingType,
      maidsRoom,
      additionalCapex,
      pricePerSqft,
      equityInjection,
      mortgageAmount,
      emi,
      totalMonthlyMortgage,
      serviceCharge,
      netAnnualRental,
      netYield,
      sellingPrice,
      netProfit,
      netProfitPct,
      netProfitPerYear,
      totalRoiPa,
    };
  }

  function shareAnalysis() {
    const url = buildDealUrl(buildSnapshot(), window.location.origin, base);
    navigator.clipboard.writeText(url).then(() => {
      shareCopied = true;
      setTimeout(() => { shareCopied = false; }, 2500);
    });
  }

  function shareWithProfileFn() {
    const u = $user;
    if (!u) { shareAnalysis(); return; }
    const agentCard = {
      name: u.user_metadata?.full_name ?? u.email ?? 'Agent',
      avatar: u.user_metadata?.avatar_url ?? null,
      identity: u.email ?? '',
      whatsapp: u.user_metadata?.phone ?? null,
    };
    const url = buildAgentDealUrl(buildSnapshot(), window.location.origin, base, agentCard);
    navigator.clipboard.writeText(url).then(() => {
      shareProfileCopied = true;
      setTimeout(() => { shareProfileCopied = false; }, 2500);
    });
  }

  // ── Auto-populate YoY appreciation (last 12 vs prior 12 months, ready only) ──
  let yoyLoading = $state(false);
  let yoySource  = $state('');

  $effect(() => {
    if (!$dbReady) return;
    const d = district;
    const l = layout;
    const p = project && project !== 'other' ? project : '';

    let filterClause: string;
    let source: string;
    if (p) {
      filterClause = `AND LOWER(TRIM(project_name)) = '${p.replace(/'/g, "''").toLowerCase().trim()}'`;
      source = toTitleCase(p);
    } else {
      const parts: string[] = [];
      if (d) parts.push(`district = '${d.replace(/'/g, "''")}'`);
      if (l) parts.push(`LOWER(TRIM(layout)) = '${l.replace(/'/g, "''").toLowerCase()}'`);
      filterClause = parts.length ? 'AND ' + parts.join(' AND ') : '';
      source = [d, l].filter(Boolean).join(' · ') || 'Abu Dhabi · all ready';
    }

    const baseWhere = `LOWER(TRIM(sale_type)) = 'ready' AND rate_per_sqft > 0`;

    yoyLoading = true;
    Promise.all([
      query<{ median_psf: number }>(`
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf
        FROM transactions
        WHERE ${baseWhere}
          AND sale_date >= (CURRENT_DATE - INTERVAL '12 months')
          ${filterClause}
      `),
      query<{ median_psf: number }>(`
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf
        FROM transactions
        WHERE ${baseWhere}
          AND sale_date >= (CURRENT_DATE - INTERVAL '24 months')
          AND sale_date <  (CURRENT_DATE - INTERVAL '12 months')
          ${filterClause}
      `),
    ]).then(([currRows, prevRows]) => {
      const curr = currRows[0]?.median_psf;
      const prev = prevRows[0]?.median_psf;
      if (curr && prev && prev > 0) {
        const rawYoy = ((curr - prev) / prev) * 100;
        annualAppPct = Math.min(10, Math.max(0, parseFloat((rawYoy * 0.5).toFixed(1))));
        yoySource    = source;
      }
      yoyLoading = false;
    }).catch(() => { yoyLoading = false; });
  });
</script>

{#snippet scannedBadge(field: string)}
  {#if scannedFields.has(field)}
    <span class="ms-1 inline-flex items-center gap-0.5 text-[9px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/25 rounded px-1.5 py-0.5 leading-none">
      ✓ AI
    </span>
  {/if}
{/snippet}

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="rounded-2xl border border-white/8 bg-[#0e1e15] overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-white/8 flex items-center gap-3">
    <div class="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center flex-shrink-0">
      <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    </div>
    <div>
      <h4 class="text-sm font-bold text-white">{m.calc_ready_title()}</h4>
      <p class="text-xs text-white/40 mt-0.5">{m.calc_ready_subtitle()}</p>
    </div>
  </div>

  <!-- ── AI Listing Scanner ─────────────────────────────────────────────────── -->
  <div class="px-5 py-4 border-b border-white/8 space-y-2">
    <ReadyPropertyUpload onExtracted={handleReadyExtraction} />

    {#if missingAfterScan.length > 0}
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-white/30">{m.calc_still_needs_manual()}</span>
        {#each missingAfterScan as field}
          <span class="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400/70 rounded px-1.5 py-0.5 leading-none">{field}</span>
        {/each}
      </div>
    {/if}
  </div>

  <div class="p-5 grid grid-cols-1 xl:grid-cols-2 gap-6">

    <!-- ── LEFT: Inputs ──────────────────────────────────────────────────────── -->
    <div class="space-y-5">

      <!-- Unit details -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-amber-400/80 uppercase tracking-widest">{m.calc_unit_details_title()}</legend>

        <!-- District + Layout -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_field_district()}</span>
              {@render scannedBadge('district')}
            </div>
            <div class="relative">
              <select bind:value={district} class={sel}>
                <option value="">{loadingDistricts ? m.calc_district_loading() : m.calc_district_all()}</option>
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
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
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
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Project + Tenancy Status (same row) -->
        <div class="flex items-end gap-3">

          <!-- Project (takes most width) -->
          <div class="flex-1 min-w-0 space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_project_label()}</span>
              {@render scannedBadge('project')}
            </div>
            <div class="relative">
              <select bind:value={project} class={sel}>
                <option value="">{m.calc_select_project()}</option>
                {#if filteredProjects.some(p => p.sc_avg != null)}
                  <optgroup label={m.calc_optgroup_sc_available()}>
                    {#each filteredProjects.filter(p => p.sc_avg != null) as p}
                      <option value={p.project_name}>{toTitleCase(p.project_name)}</option>
                    {/each}
                  </optgroup>
                {/if}
                {#if filteredProjects.some(p => p.sc_avg == null)}
                  <optgroup label={m.calc_optgroup_rental_only()}>
                    {#each filteredProjects.filter(p => p.sc_avg == null) as p}
                      <option value={p.project_name}>{toTitleCase(p.project_name)}</option>
                    {/each}
                  </optgroup>
                {/if}
                <option value="other">{m.calc_other_not_listed()}</option>
              </select>
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
            {#if project && project !== 'other' && scLookup[project.toLowerCase().trim()] != null}
              <p class="text-[10px] text-emerald-400/60 ps-0.5">{m.calc_sc_auto_populated()}</p>
            {/if}
          </div>

          <!-- Tenancy Status (shrink-0, aligned to bottom of project) -->
          <div class="shrink-0 space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_tenancy_label()}</span>
            <div class="flex gap-2">
              {#each ([['tenanted', m.calc_tenanted()], ['vacant', m.calc_vacant()]] as const) as [val, label]}
                <button
                  type="button"
                  onclick={() => { tenancyStatus = val; }}
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all {tenancyStatus === val ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20'}"
                >{label}</button>
              {/each}
            </div>
          </div>

        </div>

        <!-- Listing Price + Annual Rent (same row) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="space-y-1 block">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_listing_price_label()}</span>
              {@render scannedBadge('price')}
            </div>
            <input type="number" bind:value={price} min="0" step="10000" class={scannedFields.has('price') ? inp : inpManual} />
          </label>
          <label class="space-y-1 block">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">
                {tenancyStatus === 'tenanted' ? m.calc_annual_rent_label() : m.calc_est_annual_rent_label()}
              </span>
              {@render scannedBadge('annualRent')}
            </div>
            <input type="number" bind:value={annualRent} min="0" step="1000"
              class={scannedFields.has('annualRent') ? inp : tenancyStatus === 'tenanted' ? inpManual : inp} />
            {#if tenancyStatus === 'vacant'}
              {#if medianRentLoading}
                <p class="text-[10px] text-white/30 ps-0.5">{m.calc_loading_median_rent()}</p>
              {:else if rentSource === 'project' && project && project !== 'other'}
                <p class="text-[10px] text-emerald-400/60 ps-0.5">{m.calc_median_rent_project_source({ project: toTitleCase(project), layout: layout || 'all' })}</p>
              {:else}
                <p class="text-[10px] text-amber-400/60 ps-0.5">{m.calc_median_rent_district_source({ district: district || 'Abu Dhabi', layout: layout || 'all' })}</p>
              {/if}
            {/if}
          </label>
        </div>

        <!-- Furnishing + Maid's Room -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_furnishing_label()}</span>
            <div class="relative">
              <select bind:value={furnishingType} class={selManual}>
                <option value="none">{m.calc_furnishing_none()}</option>
                <option value="basic_airbnb">{m.calc_furnishing_basic()}</option>
                <option value="highend_airbnb">{m.calc_furnishing_highend()}</option>
                <option value="branded_hospitality">{m.calc_furnishing_branded()}</option>
              </select>
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
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
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
            {#if maidsRoom === 'yes' && maidsPct === 0}
              <p class="text-[10px] text-white/30 ps-0.5">{m.calc_maids_hint()}</p>
            {/if}
          </div>
        </div>

        <!-- Size inputs -->
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_living_area_label()}</span>
              {@render scannedBadge('livingArea')}
            </div>
            <input type="number" bind:value={livingArea} min="0" step="10" class={scannedFields.has('livingArea') ? inp : inpManual} />
          </label>
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_balcony_label()}</span>
              {@render scannedBadge('balconyArea')}
            </div>
            <input type="number" bind:value={balconyArea} min="0" step="5" class={scannedFields.has('balconyArea') ? inp : inpManual} />
          </label>
          <label class="space-y-1">
            <div class="flex items-center gap-1">
              <span class="text-[11px] text-white/50">{m.calc_service_charge_label()}</span>
              {@render scannedBadge('serviceChargePsf')}
            </div>
            <input type="number" bind:value={serviceChargePsf} min="0" step="0.5" class={scannedFields.has('serviceChargePsf') ? inp : inpManual} />
          </label>
        </div>

        <!-- AED/sqft + Total Acquisition Cost -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="rounded-lg bg-amber-500/8 border border-amber-500/20 px-3 py-2.5">
            <p class="text-[10px] text-amber-400/70 uppercase tracking-wider">{m.calc_price_per_sqft_label()}</p>
            <p class="text-base font-black text-amber-400 tabular-nums mt-0.5">
              {livingArea > 0 ? Math.round(pricePerSqft).toLocaleString('en-AE') : '—'} <span class="text-xs font-semibold text-amber-400/60">AED/sqft</span>
            </p>
          </div>
          <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5">
            <p class="text-[10px] text-white/35 uppercase tracking-wider">{m.calc_total_acquisition_cost_label()}</p>
            <p class="text-sm font-bold text-white/70 tabular-nums mt-0.5">{fmtAed(equityInjection)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">{m.calc_total_acquisition_breakdown_ready({ mortgageExtra: mortgageType !== 'none' ? m.calc_mortgage_admin_extra() : '' })}</p>
          </div>
        </div>
      </fieldset>

      <!-- Mortgage settings -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-indigo-400/80 uppercase tracking-widest">{m.calc_mortgage_title()}</legend>

        <!-- Mortgage type toggle -->
        <div class="flex gap-2 flex-wrap">
          {#each [['none', m.calc_no_mortgage()], ['1st', m.calc_1st_mortgage()], ['2nd', m.calc_2nd_mortgage()]] as [val, label]}
            <button
              type="button"
              onclick={() => { mortgageType = val as 'none' | '1st' | '2nd'; }}
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all {mortgageType === val ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20'}"
            >{label}</button>
          {/each}
        </div>

        {#if mortgageType !== 'none'}
        <!-- Residency -->
        <div class="flex gap-2 flex-wrap">
          {#each [['uae_national', m.calc_uae_national()], ['uae_resident', m.calc_uae_resident()], ['non_resident', m.calc_non_uae_resident()]] as [val, label]}
            <button
              type="button"
              onclick={() => { residency = val as 'uae_national' | 'uae_resident' | 'non_resident'; }}
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all {residency === val ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20'}"
            >{label}</button>
          {/each}
        </div>

        <!-- LTV display + mortgage params -->
        <div class="rounded-lg bg-indigo-950/40 border border-indigo-500/15 px-3 py-2.5 flex items-center justify-between text-xs">
          <span class="text-white/50">{m.calc_ltv_label()}</span>
          <span class="font-bold text-indigo-300">{m.calc_ltv_value({ ltv: (ltv * 100).toFixed(0), mortgage: fmtAed(mortgageAmount), down: fmtAed(downpayment) })}</span>
        </div>

        {#if !mortgageEligible}
        <p class="text-[11px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
          {m.calc_mortgage_min_warning()}
        </p>
        {/if}

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_interest_rate_label()}</span>
            <input type="number" bind:value={interestRate} min="0" max="20" step="0.05" class={inpManual} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_term_length_label()}</span>
            <input type="number" bind:value={termYears} min="5" max="25" step="1" class={inpManual} />
          </label>
        </div>

        <!-- EMI breakdown -->
        <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5 space-y-1 text-xs text-white/50">
          <div class="flex justify-between"><span>{m.calc_monthly_emi()}</span><span class="tabular-nums text-white/70">{fmtAed(emi)}/mth</span></div>
          <div class="flex justify-between"><span>{m.calc_life_insurance()}</span><span class="tabular-nums text-white/70">{fmtAed(lifeInsurance)}/mth</span></div>
          <div class="flex justify-between"><span>{m.calc_property_insurance()}</span><span class="tabular-nums text-white/70">{fmtAed(propertyInsurance)}/mth</span></div>
          <div class="flex justify-between font-semibold text-white/80 border-t border-white/8 pt-1"><span>{m.calc_total_mortgage_month()}</span><span class="tabular-nums">{fmtAed(totalMonthlyMortgage)}</span></div>
          <div class="flex justify-between text-white/60"><span>{m.calc_total_mortgage_year()}</span><span class="tabular-nums">{fmtAed(annualMortgage)}</span></div>
        </div>
        {/if}

        <!-- Equity injection summary -->
        <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5 space-y-1 text-xs">
          <div class="flex justify-between text-white/50"><span>{m.calc_downpayment_label({ pct: (100 - ltv * 100).toFixed(0) })}</span><span class="tabular-nums">{fmtAed(downpayment)}</span></div>
          <div class="flex justify-between text-white/50"><span>{m.calc_dari_agency_fees()}</span><span class="tabular-nums">{fmtAed(purchasingFees)}</span></div>
          {#if mortgageType !== 'none'}
          <div class="flex justify-between text-white/50"><span>{m.calc_mortgage_admin_fees()}</span><span class="tabular-nums">{fmtAed(mortgageAdminFee)}</span></div>
          {/if}
          <div class="flex justify-between font-semibold text-white/80 border-t border-white/8 pt-1"><span>{m.calc_total_equity_purchase()}</span><span class="tabular-nums">{fmtAed(equityInjection)}</span></div>
        </div>
      </fieldset>

      <!-- Capital gains inputs -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-blue-400/80 uppercase tracking-widest">{m.calc_capital_gains_title()}</legend>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_comparable_psf_label()}</span>
            <input type="number" bind:value={comparablePsf} min="0" step="50" class={inp} />
            {#if psf6mLoading}
              <p class="text-[10px] text-white/30 ps-0.5">{m.calc_loading_median_psf()}</p>
            {:else if psf6mSource}
              <p class="text-[10px] text-amber-400/60 ps-0.5">{m.calc_median_psf_source({ source: psf6mSource })}</p>
            {/if}
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_resale_time_ready_label()}</span>
            <input type="number" bind:value={yearsToResale} min="0" max="5" step="1" class={inpManual} />
          </label>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_annual_appreciation_label()}</span>
            <input type="number" bind:value={annualAppPct} min="0" max="10" step="0.5" class={inp} />
            {#if yoyLoading}
              <p class="text-[10px] text-white/30 ps-0.5">{m.calc_loading_yoy()}</p>
            {:else if yoySource}
              <p class="text-[10px] text-amber-400/60 ps-0.5">{m.calc_yoy_ready_source({ source: yoySource })}</p>
            {/if}
          </label>
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_furnishing_label()}</span>
            <div class="relative">
              <select bind:value={otherFactorType} class={selManual}>
                <option value="no">{m.calc_maids_no()}</option>
                <option value="yes">{m.calc_finish_branding_yes()}</option>
              </select>
              <svg class="pointer-events-none absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">{m.calc_refurb_capex_label()}</span>
            <input type="number" bind:value={additionalCapex} min="0" step="5000" class={inpManual} />
          </label>
        </div>
        <p class="text-[11px] text-white/30 ps-0.5">
          {m.calc_selling_price_based_on({ psf: comparablePsf.toLocaleString('en-AE'), area: String(livingArea), pct: String(annualAppPct), years: String(yearsToResale), extra: otherAppPct > 0 ? ` × (1 + ${otherAppPct}%)` : '' })} <span class="text-amber-400/70">{fmtAed(sellingPrice)}</span>
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
            <p class="text-[9px] text-gray-500 mt-1">{m.calc_on_equity_injected()}</p>
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

        <!-- Rental ROI breakdown -->
        <div class="rounded-xl border border-amber-200 bg-white overflow-hidden shadow-sm">
          <div class="px-3.5 py-2.5 border-b border-amber-100 bg-amber-50">
            <h5 class="text-[10px] font-bold text-gray-900 uppercase tracking-widest">{m.calc_rental_income_title()}</h5>
          </div>
          <div class="px-3.5 py-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-gray-500">
              <span>{tenancyStatus === 'tenanted' ? m.calc_tenanted_annual_rent() : m.calc_vacant_est_market_rent()}</span>
              <span class="tabular-nums text-gray-700 font-medium">{fmtAed(annualRent)}</span>
            </div>
            {#if furnishingPct > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_furnishing_premium({ pct: String(furnishingPct) })}</span>
                <span class="tabular-nums text-emerald-600">+ {fmtAed(annualRent * furnishingPct / 100)}</span>
              </div>
            {/if}
            {#if maidsPct > 0}
              <div class="flex justify-between text-gray-500">
                <span>{m.calc_maids_premium({ pct: String(maidsPct) })}</span>
                <span class="tabular-nums text-emerald-600">+ {fmtAed(afterFurnishing * maidsPct / 100)}</span>
              </div>
            {/if}
            <div class="flex justify-between text-gray-500">
              <span>{m.calc_service_charge_vat_line()}</span>
              <span class="tabular-nums text-red-500">− {fmtAed(serviceCharge)}</span>
            </div>
            {#if mortgageType !== 'none'}
            <div class="flex justify-between text-gray-500">
              <span>{m.calc_total_mortgage_year()}</span>
              <span class="tabular-nums text-red-500">− {fmtAed(annualMortgage)}</span>
            </div>
            {/if}
            <div class="flex justify-between font-bold text-gray-800 border-t border-amber-100 pt-1.5">
              <span>{m.calc_net_annual_revenue()}</span>
              <span class="tabular-nums {netAnnualRental >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(netAnnualRental)}</span>
            </div>
          </div>
          <!-- Monthly cashflow callout -->
          <div class="mx-3.5 mb-3.5 rounded-lg border px-3.5 py-2.5 flex items-center justify-between {monthlyNetCashflow >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}">
            <span class="text-xs font-semibold {monthlyNetCashflow >= 0 ? 'text-emerald-700' : 'text-red-700'}">{m.calc_monthly_net_cashflow()}</span>
            <span class="text-xl font-black tabular-nums {monthlyNetCashflow >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(monthlyNetCashflow)}</span>
          </div>
        </div>

        <!-- Capital Gains breakdown -->
        <div class="rounded-xl border border-amber-200 bg-white overflow-hidden shadow-sm">
          <div class="px-3.5 py-2.5 border-b border-amber-100 bg-amber-50">
            <h5 class="text-[10px] font-bold text-gray-900 uppercase tracking-widest">{m.calc_capital_gains_horizon_title({ years: String(yearsToResale) })}</h5>
          </div>
          <div class="px-3.5 py-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-gray-500">
              <span>{m.calc_potential_selling_price()}</span>
              <span class="tabular-nums text-gray-700 font-medium">{fmtAed(sellingPrice)}</span>
            </div>
            <div class="flex justify-between gap-2 text-gray-500">
              <span class="min-w-0">{m.calc_total_purchase_cost()}</span>
              <span class="tabular-nums text-red-500 flex-shrink-0">− {fmtAed(price + purchasingFees + mortgageAdminFee)}</span>
            </div>
            <div class="flex justify-between gap-2 text-gray-500">
              <span class="min-w-0">{m.calc_resale_broker_fee_2pct()}</span>
              <span class="tabular-nums text-red-500 flex-shrink-0">− {fmtAed(resaleBrokerFee)}</span>
            </div>
            {#if additionalCapex > 0}
            <div class="flex justify-between text-gray-500">
              <span>{m.calc_additional_capex_line()}</span>
              <span class="tabular-nums text-red-500">− {fmtAed(additionalCapex)}</span>
            </div>
            {/if}
            <div class="flex justify-between font-bold text-gray-800 border-t border-amber-100 pt-1.5">
              <span>{m.calc_net_profit()}</span>
              <span class="tabular-nums {netProfit >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtAed(netProfit)}</span>
            </div>
          </div>
          <!-- Total return + net profit callout row -->
          <div class="grid grid-cols-2 gap-2 mx-3.5 mb-3.5">
            <div class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2.5 text-center">
              <p class="text-[10px] font-bold text-gray-800 uppercase tracking-wider">{m.calc_total_return()}</p>
              <p class="text-xl font-black tabular-nums mt-1 {netProfitPct >= 0 ? 'text-emerald-600' : 'text-red-600'}">{fmtPct(netProfitPct)}</p>
              <p class="text-[9px] text-gray-500 mt-0.5">{m.calc_on_equity_capex()}</p>
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

        <!-- Share button(s) -->
        {#if $isAuthenticated}
          <div class="flex gap-2">
            <button
              type="button"
              onclick={shareWithProfileFn}
              class="flex-1 flex items-center justify-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-xs font-semibold text-emerald-800 hover:border-emerald-400 hover:bg-emerald-100 transition-colors"
            >
              {#if shareProfileCopied}
                <svg class="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span>{m.share_copied()}</span>
              {:else}
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
                </svg>
                {m.agent_share_with_profile()}
              {/if}
            </button>
            <button
              type="button"
              onclick={shareAnalysis}
              class="flex-1 flex items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-xs font-semibold text-gray-700 hover:border-amber-400 hover:text-amber-700 transition-colors"
            >
              {#if shareCopied}
                <svg class="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span class="text-emerald-600">{m.share_copied()}</span>
              {:else}
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 1 1.242 7.244" />
                </svg>
                {m.agent_share_anonymous()}
              {/if}
            </button>
          </div>
        {:else}
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
        {/if}

        <!-- Disclaimer -->
        <p class="text-[10px] text-gray-400 leading-relaxed px-0.5">
          {m.calc_disclaimer_ready()}
        </p>

      </div><!-- end inner padding -->
    </div><!-- end right -->

  </div><!-- end grid -->

  <!-- Mortgage + Cash Flow -->
  <div class="mt-6 px-5 pb-5">
    <MortgageSection
      purchasePrice={price}
      netAnnualRental={netAnnualRental}
      onchange={(d) => { mortgageMonthlyPaymentCf = d.monthlyPayment; }}
    />
    <CashFlowProjection
      purchasePrice={price}
      grossRental={effectiveRent}
      rentalAppPct={0}
      {serviceCharge}
      mgmtFeePct={0}
      utilities={0}
      {annualAppPct}
      monthlyMortgagePayment={mortgageMonthlyPaymentCf}
    />
  </div>
</div>
