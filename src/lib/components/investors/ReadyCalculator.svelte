<script lang="ts">
  import { metadata } from '$lib/stores/db';

  // ── Helpers ─────────────────────────────────────────────────────────────────
  function fmtAed(v: number): string {
    if (!isFinite(v) || isNaN(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number, dp = 1): string {
    if (!isFinite(v) || isNaN(v)) return '—';
    return v.toFixed(dp) + '%';
  }

  // ── District & Layout options from metadata ──────────────────────────────────
  const LAYOUT_ORDER = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds', '5+ beds', '6+ beds'];
  const LAYOUT_DISPLAY: Record<string, string> = { studio: 'Studio' };

  const PINNED_DISTRICTS = [
    'Al Reem Island',
    'Yas Island',
    'Al Saadiyat Island',
    'Al Rahah',
    'Khalifa City',
    'Al Reef',
    'Fahid Island',
    'Al Hidayriyyat',
  ];

  let districts = $derived(() => {
    const all: string[] = $metadata?.districts ?? [];
    const pinnedFound  = PINNED_DISTRICTS.filter(p => all.some(d => d.toLowerCase() === p.toLowerCase()));
    const pinnedSet    = new Set(pinnedFound.map(p => p.toLowerCase()));
    const rest         = all.filter(d => !pinnedSet.has(d.toLowerCase())).sort();
    return [...pinnedFound, ...rest];
  })();
  let layouts = $derived(
    ($metadata?.layouts ?? [])
      .filter((l: string) => LAYOUT_ORDER.includes(l.toLowerCase()))
      .sort((a: string, b: string) => LAYOUT_ORDER.indexOf(a.toLowerCase()) - LAYOUT_ORDER.indexOf(b.toLowerCase()))
  );

  // ── Shared input / select class ───────────────────────────────────────────
  const inp = 'w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30';
  const sel = 'w-full bg-[#0a1a10] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 appearance-none cursor-pointer';

  // ── Mortgage LTV matrix ──────────────────────────────────────────────────────
  // Key: `${mortgageType}|${residency}` → [ltv_below5m, ltv_above5m]
  const LTV_MATRIX: Record<string, [number, number]> = {
    'none|uae_national':      [0, 0],
    'none|uae_resident':      [0, 0],
    'none|non_resident':      [0, 0],
    '1st|uae_national':       [0.85, 0.75],
    '1st|uae_resident':       [0.80, 0.70],
    '1st|non_resident':       [0.50, 0.50],
    '2nd|uae_national':       [0.65, 0.65],
    '2nd|uae_resident':       [0.60, 0.60],
    '2nd|non_resident':       [0.50, 0.50],
  };

  // ── Inputs ──────────────────────────────────────────────────────────────────
  let district         = $state('');
  let layout           = $state('');
  let price            = $state(600_000);   // property price AED
  let livingArea       = $state(413);       // sqft
  let balconyArea      = $state(45);        // sqft
  let serviceChargePsf = $state(16);        // AED/sqft/year
  let annualRent       = $state(50_000);    // AED/year

  // Mortgage settings
  let mortgageType = $state<'none' | '1st' | '2nd'>('1st');
  let residency    = $state<'uae_national' | 'uae_resident' | 'non_resident'>('uae_resident');
  let interestRate = $state(4.35);          // % annual
  let termYears    = $state(25);

  // Capital gains
  let comparablePsf     = $state(1_250);   // AED/sqft comparable units last 6 months
  let yearsToResale     = $state(5);
  let annualAppPct      = $state(4);        // %
  let otherAppPct       = $state(0);        // %
  let additionalCapex   = $state(0);        // AED refurb/maintenance

  // ── Derived: unit ────────────────────────────────────────────────────────────
  let pricePerSqft = $derived(livingArea > 0 ? price / livingArea : 0);

  // ── Derived: LTV & mortgage ──────────────────────────────────────────────────
  let ltvKey    = $derived(`${mortgageType}|${residency}`);
  let ltvRates  = $derived(LTV_MATRIX[ltvKey] ?? [0, 0]);
  let ltv       = $derived(price >= 5_000_000 ? ltvRates[1] : ltvRates[0]);
  let mortgageAmount = $derived(price * ltv);
  let downpayment    = $derived(price - mortgageAmount);

  // Purchase costs: Abu Dhabi 2% DARI/DMT + AED 1,000 title deed + 2% agency + 5% VAT
  let registrationFee  = $derived(price * 0.02 + 1_000); // DARI/DMT + title deed
  let agencyFee        = $derived(price * 0.02 * 1.05);  // 2% + 5% VAT
  let purchasingFees   = $derived(registrationFee + agencyFee);
  let mortgageAdminFee = $derived(mortgageType !== 'none' ? 9_400 : 0);
  let equityInjection  = $derived(downpayment + purchasingFees + mortgageAdminFee);

  // Mortgage EMI (monthly)
  let monthlyRate = $derived(interestRate / 100 / 12);
  let nPayments   = $derived(termYears * 12);
  let emi = $derived(
    mortgageType !== 'none' && mortgageAmount > 0 && monthlyRate > 0
      ? mortgageAmount * monthlyRate / (1 - Math.pow(1 + monthlyRate, -nPayments))
      : 0
  );
  let lifeInsurance     = $derived(mortgageAmount * 0.000171);  // 0.0171% of loan/mth
  let propertyInsurance = $derived(price * 0.0001);            // 0.01% of price/mth
  let totalMonthlyMortgage = $derived(emi + lifeInsurance + propertyInsurance);
  let annualMortgage = $derived(totalMonthlyMortgage * 12);

  // Mortgage eligibility check (most banks min AED 250k)
  let mortgageEligible = $derived(mortgageType === 'none' || mortgageAmount >= 250_000);

  // ── Derived: rental ─────────────────────────────────────────────────────────
  let serviceCharge = $derived((livingArea + balconyArea * 0.25) * serviceChargePsf * 1.05);
  let netAnnualRental = $derived(annualRent - serviceCharge - annualMortgage);
  let monthlyNetCashflow = $derived(netAnnualRental / 12);
  let netYield = $derived(equityInjection > 0 ? (netAnnualRental / equityInjection) * 100 : 0);
  let rentalObjective = $derived(netYield >= 7);

  // ── Derived: capital gains ───────────────────────────────────────────────────
  let totalAppRate    = $derived((annualAppPct + otherAppPct) / 100);
  let sellingPrice    = $derived(comparablePsf * livingArea * Math.pow(1 + totalAppRate, yearsToResale));
  let resaleBrokerFee = $derived(sellingPrice * 0.02);
  let netProfit = $derived(
    sellingPrice - price - purchasingFees - mortgageAdminFee - resaleBrokerFee - additionalCapex
  );
  let totalEquityBase = $derived(equityInjection + additionalCapex);
  let netProfitPct    = $derived(totalEquityBase > 0 ? (netProfit / totalEquityBase) * 100 : 0);
  let netProfitPerYear = $derived(
    yearsToResale > 0 && totalEquityBase > 0
      ? (Math.pow(1 + netProfitPct / 100, 1 / yearsToResale) - 1) * 100
      : 0
  );
  let capitalObjective = $derived(netProfitPerYear >= 7);
</script>

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
      <h4 class="text-sm font-bold text-white">Ready Property Calculator</h4>
      <p class="text-xs text-white/40 mt-0.5">Rental yield · Mortgage · Capital gains</p>
    </div>
  </div>

  <div class="p-5 grid grid-cols-1 xl:grid-cols-2 gap-6">

    <!-- ── LEFT: Inputs ──────────────────────────────────────────────────────── -->
    <div class="space-y-5">

      <!-- Property details -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-amber-400/80 uppercase tracking-widest">Unit Details</legend>

        <!-- District + Layout dropdowns -->
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">District</span>
            <div class="relative">
              <select bind:value={district} class={sel}>
                <option value="">All Districts</option>
                <optgroup label="── Popular ──">
                  {#each districts.slice(0, PINNED_DISTRICTS.length) as d}
                    <option value={d}>{d}</option>
                  {/each}
                </optgroup>
                <optgroup label="── All Districts ──">
                  {#each districts.slice(PINNED_DISTRICTS.length) as d}
                    <option value={d}>{d}</option>
                  {/each}
                </optgroup>
              </select>
              <svg class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">Layout</span>
            <div class="relative">
              <select bind:value={layout} class={sel}>
                <option value="">Select Layout</option>
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

        <!-- Price + Annual Rent -->
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Listing Price (AED)</span>
            <input type="number" bind:value={price} min="0" step="10000" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Annual Rent (AED/yr)</span>
            <input type="number" bind:value={annualRent} min="0" step="1000" class={inp} />
          </label>
        </div>

        <!-- Size inputs -->
        <div class="grid grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Living Area (sqft)</span>
            <input type="number" bind:value={livingArea} min="0" step="10" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Balcony (sqft)</span>
            <input type="number" bind:value={balconyArea} min="0" step="5" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Service Charge (AED/sqft)</span>
            <input type="number" bind:value={serviceChargePsf} min="0" step="0.5" class={inp} />
          </label>
        </div>

        <!-- AED/sqft + Total Acquisition Cost -->
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-lg bg-amber-500/8 border border-amber-500/20 px-3 py-2.5">
            <p class="text-[10px] text-amber-400/70 uppercase tracking-wider">Price per sqft</p>
            <p class="text-base font-black text-amber-400 tabular-nums mt-0.5">
              {livingArea > 0 ? Math.round(pricePerSqft).toLocaleString('en-AE') : '—'} <span class="text-xs font-semibold text-amber-400/60">AED/sqft</span>
            </p>
          </div>
          <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5">
            <p class="text-[10px] text-white/35 uppercase tracking-wider">Total Acquisition Cost</p>
            <p class="text-sm font-bold text-white/70 tabular-nums mt-0.5">{fmtAed(equityInjection)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">Equity + DARI/DMT (2%+1K) + Agency (2%+VAT){mortgageType !== 'none' ? ' + Mortgage admin' : ''}</p>
          </div>
        </div>
      </fieldset>

      <!-- Mortgage settings -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-indigo-400/80 uppercase tracking-widest">Mortgage</legend>

        <!-- Mortgage type toggle -->
        <div class="flex gap-2 flex-wrap">
          {#each [['none', 'No Mortgage'], ['1st', '1st Mortgage'], ['2nd', '2nd Mortgage']] as [val, label]}
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
          {#each [['uae_national', 'UAE National'], ['uae_resident', 'UAE Resident'], ['non_resident', 'Non-UAE Resident']] as [val, label]}
            <button
              type="button"
              onclick={() => { residency = val as 'uae_national' | 'uae_resident' | 'non_resident'; }}
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all {residency === val ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20'}"
            >{label}</button>
          {/each}
        </div>

        <!-- LTV display + mortgage params -->
        <div class="rounded-lg bg-indigo-950/40 border border-indigo-500/15 px-3 py-2.5 flex items-center justify-between text-xs">
          <span class="text-white/50">LTV (loan-to-value)</span>
          <span class="font-bold text-indigo-300">{(ltv * 100).toFixed(0)}% → Mortgage {fmtAed(mortgageAmount)} · Down {fmtAed(downpayment)}</span>
        </div>

        {#if !mortgageEligible}
        <p class="text-[11px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
          Most banks require a minimum loan of AED 250,000. Consider increasing the property price or switching to no mortgage.
        </p>
        {/if}

        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Annual Interest Rate (%)</span>
            <input type="number" bind:value={interestRate} min="0" max="20" step="0.05"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Term Length (years)</span>
            <input type="number" bind:value={termYears} min="5" max="25" step="1"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>

        <!-- EMI breakdown -->
        <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5 space-y-1 text-xs text-white/50">
          <div class="flex justify-between"><span>Monthly EMI</span><span class="tabular-nums text-white/70">{fmtAed(emi)}/mth</span></div>
          <div class="flex justify-between"><span>Life insurance (0.0171%/mth)</span><span class="tabular-nums text-white/70">{fmtAed(lifeInsurance)}/mth</span></div>
          <div class="flex justify-between"><span>Property insurance (0.01%/mth)</span><span class="tabular-nums text-white/70">{fmtAed(propertyInsurance)}/mth</span></div>
          <div class="flex justify-between font-semibold text-white/80 border-t border-white/8 pt-1"><span>Total mortgage / month</span><span class="tabular-nums">{fmtAed(totalMonthlyMortgage)}</span></div>
          <div class="flex justify-between text-white/60"><span>Total mortgage / year</span><span class="tabular-nums">{fmtAed(annualMortgage)}</span></div>
        </div>
        {/if}

        <!-- Equity injection summary -->
        <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5 space-y-1 text-xs">
          <div class="flex justify-between text-white/50"><span>Downpayment ({(100 - ltv * 100).toFixed(0)}%)</span><span class="tabular-nums">{fmtAed(downpayment)}</span></div>
          <div class="flex justify-between text-white/50"><span>DARI/DMT + agency fees</span><span class="tabular-nums">{fmtAed(purchasingFees)}</span></div>
          {#if mortgageType !== 'none'}
          <div class="flex justify-between text-white/50"><span>Mortgage admin fees (est.)</span><span class="tabular-nums">{fmtAed(mortgageAdminFee)}</span></div>
          {/if}
          <div class="flex justify-between font-semibold text-white/80 border-t border-white/8 pt-1"><span>Total equity at purchase</span><span class="tabular-nums">{fmtAed(equityInjection)}</span></div>
        </div>
      </fieldset>

      <!-- Capital gains inputs -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-blue-400/80 uppercase tracking-widest">Capital Gains Estimation</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Comparable Area PSF (AED, last 6 mths)</span>
            <input type="number" bind:value={comparablePsf} min="0" step="50"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Time of Resale (years)</span>
            <input type="number" bind:value={yearsToResale} min="0" max="30" step="1"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Annual Appreciation (%)</span>
            <input type="number" bind:value={annualAppPct} min="0" max="50" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Other Factors (%)</span>
            <input type="number" bind:value={otherAppPct} min="0" max="20" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Refurb / Capex (AED)</span>
            <input type="number" bind:value={additionalCapex} min="0" step="5000"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <p class="text-[11px] text-white/30 pl-0.5">
          Selling price based on: {comparablePsf.toLocaleString('en-AE')} AED/sqft × {livingArea} sqft living × (1 + {annualAppPct + otherAppPct}%)^{yearsToResale} = <span class="text-amber-400/70">{fmtAed(sellingPrice)}</span>
        </p>
      </fieldset>

    </div><!-- end left -->

    <!-- ── RIGHT: Results ────────────────────────────────────────────────────── -->
    <div class="space-y-4">

      <!-- Rental ROI Card -->
      <div class="rounded-xl border border-emerald-500/20 bg-emerald-950/30 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h5 class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Rental ROI</h5>
          <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide {rentalObjective ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/15 text-red-400'}">
            {rentalObjective ? '✓ 7%+ Target Met' : '✗ Below 7% Target'}
          </span>
        </div>

        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Annual rent</span>
            <span class="tabular-nums text-white/80">{fmtAed(annualRent)}</span>
          </div>
          <div class="flex justify-between text-white/60">
            <span>Service charge + VAT</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(serviceCharge)}</span>
          </div>
          {#if mortgageType !== 'none'}
          <div class="flex justify-between text-white/60">
            <span>Annual mortgage payments</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(annualMortgage)}</span>
          </div>
          {/if}
          <div class="flex justify-between font-bold text-white border-t border-white/10 pt-1.5">
            <span>Net Annual Revenue</span>
            <span class="tabular-nums {netAnnualRental >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtAed(netAnnualRental)}</span>
          </div>
        </div>

        <!-- Metrics grid -->
        <div class="grid grid-cols-3 gap-2 pt-1">
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Gross Yield</p>
            <p class="text-lg font-black tabular-nums {price > 0 && (annualRent/price*100) >= 7 ? 'text-emerald-400' : 'text-amber-400'}">{price > 0 ? fmtPct(annualRent / price * 100) : '—'}</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Net Yield</p>
            <p class="text-lg font-black tabular-nums {netYield >= 7 ? 'text-emerald-400' : netYield >= 5 ? 'text-amber-400' : 'text-red-400'}">{fmtPct(netYield)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">on equity injected</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Mthly Cashflow</p>
            <p class="text-base font-black tabular-nums {monthlyNetCashflow >= 0 ? 'text-emerald-400' : 'text-red-400'} leading-tight">{fmtAed(monthlyNetCashflow)}</p>
          </div>
        </div>
      </div>

      <!-- Capital Gains Card -->
      <div class="rounded-xl border border-blue-500/20 bg-blue-950/20 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h5 class="text-xs font-bold text-blue-300 uppercase tracking-wider">Capital Gains · {yearsToResale}yr Horizon</h5>
          <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide {capitalObjective ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/15 text-red-400'}">
            {capitalObjective ? '✓ 7%/yr Target Met' : '✗ Below 7%/yr Target'}
          </span>
        </div>

        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Potential selling price</span>
            <span class="tabular-nums text-white/80 font-semibold">{fmtAed(sellingPrice)}</span>
          </div>
          <div class="flex justify-between text-white/55">
            <span>Total purchase cost (price + fees)</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(price + purchasingFees + mortgageAdminFee)}</span>
          </div>
          <div class="flex justify-between text-white/55">
            <span>Resale broker fee (2%)</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(resaleBrokerFee)}</span>
          </div>
          {#if additionalCapex > 0}
          <div class="flex justify-between text-white/55">
            <span>Additional capex / refurb</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(additionalCapex)}</span>
          </div>
          {/if}
          <div class="flex justify-between font-bold text-white border-t border-white/10 pt-1.5">
            <span>Net Profit</span>
            <span class="tabular-nums {netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtAed(netProfit)}</span>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2 pt-1">
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Total Return</p>
            <p class="text-lg font-black tabular-nums {netProfitPct >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtPct(netProfitPct)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">on equity + capex</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Per Year (CAGR)</p>
            <p class="text-lg font-black tabular-nums {netProfitPerYear >= 7 ? 'text-emerald-400' : netProfitPerYear >= 5 ? 'text-amber-400' : 'text-red-400'}">{fmtPct(netProfitPerYear)}</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Net Profit</p>
            <p class="text-base font-black tabular-nums {netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'} leading-tight">
              {netProfit >= 0 ? '+' : ''}{Math.abs(netProfit) >= 1_000_000 ? (netProfit / 1_000_000).toFixed(2) + 'M' : (Math.round(Math.abs(netProfit) / 1000)) + 'K' }
            </p>
            <p class="text-[9px] text-white/25 mt-0.5">AED</p>
          </div>
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-[10px] text-white/20 leading-relaxed px-0.5">
        Indicative estimates only. Mortgage rates sourced from current UAE market benchmarks; actual rates vary by bank and applicant profile. LTV ratios per CBUAE guidelines. Abu Dhabi registration fee: 2% DARI/DMT + AED 1,000 title deed. Agency fee: 2% + 5% VAT. Mortgage admin est. AED 9,400. Selling price based on comparable area PSF appreciation — verify with ADInteract Sales data.
      </p>

    </div><!-- end right -->

  </div><!-- end grid -->
</div>
