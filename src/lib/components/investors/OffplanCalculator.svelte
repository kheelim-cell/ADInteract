<script lang="ts">
  // ── Helpers ─────────────────────────────────────────────────────────────────
  function fmtAed(v: number): string {
    if (!isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number, dp = 1): string {
    if (!isFinite(v)) return '—';
    return v.toFixed(dp) + '%';
  }
  function fmtNum(v: number): string {
    if (!isFinite(v)) return '—';
    return Math.round(v).toLocaleString('en-AE');
  }

  // ── Inputs ──────────────────────────────────────────────────────────────────
  let cost              = $state(1_000_000);   // purchase price AED
  let internalArea      = $state(900);          // sqft
  let balconyArea       = $state(45);           // sqft
  let adminFee          = $state(4_000);        // developer admin AED

  // Rental inputs
  let comparableRent    = $state(50_000);       // AED/year
  let yearsTillHandover = $state(2);
  let rentalAppPct      = $state(15);           // % appreciation over construction
  let furnishedPremium  = $state(10_000);       // AED annual premium
  let mgmtFeePct        = $state(8);            // % of gross rental
  let utilitiesMonthly  = $state(0);            // AED/month
  let serviceChargePsf  = $state(15);           // AED/sqft/year
  let furnitureCost     = $state(0);            // one-time AED

  // Capital gains inputs
  let readyUnitPsf      = $state(1_137);        // AED/sqft comparable ready unit
  let yearsToResale     = $state(5);
  let annualAppPct      = $state(12);           // % annual price appreciation
  let otherAppPct       = $state(0);            // % additional appreciation
  let resaleBrokerPct   = $state(2);            // %

  // ── Derived: purchase costs ─────────────────────────────────────────────────
  let totalArea = $derived(internalArea + balconyArea);
  let dldFee    = $derived(cost * 0.04 + 580);
  let totalPurchaseCost = $derived(cost + dldFee + adminFee);

  // ── Derived: rental ─────────────────────────────────────────────────────────
  let grossRental = $derived(
    comparableRent * Math.pow(1 + rentalAppPct / 100, yearsTillHandover) + furnishedPremium
  );
  let mgmtFee       = $derived(grossRental * mgmtFeePct / 100);
  let utilities     = $derived(utilitiesMonthly * 12);
  let serviceCharge = $derived((internalArea + balconyArea * 0.25) * serviceChargePsf * 1.05);
  let netRental     = $derived(grossRental - mgmtFee - utilities - serviceCharge);

  let grossYield    = $derived(cost > 0 ? (grossRental / cost) * 100 : 0);
  let netYield      = $derived(totalPurchaseCost > 0 ? (netRental / totalPurchaseCost) * 100 : 0);
  let paybackYears  = $derived(netYield > 0 ? (100 / netYield) : 0);
  let rentalObjective = $derived(netYield >= 7);

  // ── Derived: capital gains ───────────────────────────────────────────────────
  let totalAppRate    = $derived((annualAppPct + otherAppPct) / 100);
  let sellingPrice    = $derived(cost * Math.pow(1 + totalAppRate, yearsToResale));
  let resaleBrokerFee = $derived(sellingPrice * resaleBrokerPct / 100);
  let totalAllInCost  = $derived(totalPurchaseCost + resaleBrokerFee);
  let netProfit       = $derived(sellingPrice - totalAllInCost);
  let netProfitPct    = $derived(totalAllInCost > 0 ? (netProfit / totalAllInCost) * 100 : 0);
  let netProfitPerYear = $derived(
    yearsToResale > 0 && totalAllInCost > 0
      ? (Math.pow(sellingPrice / totalAllInCost, 1 / yearsToResale) - 1) * 100
      : 0
  );
  let capitalObjective = $derived(netProfitPerYear >= 7);
</script>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="rounded-2xl border border-white/8 bg-[#0e1e15] overflow-hidden">

  <!-- Header -->
  <div class="px-5 py-4 border-b border-white/8 flex items-center gap-3">
    <div class="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center flex-shrink-0">
      <svg class="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" />
      </svg>
    </div>
    <div>
      <h4 class="text-sm font-bold text-white">Offplan Investment Calculator</h4>
      <p class="text-xs text-white/40 mt-0.5">Capital gains · Rental yield · Net ROI</p>
    </div>
  </div>

  <div class="p-5 grid grid-cols-1 xl:grid-cols-2 gap-6">

    <!-- ── LEFT: Inputs ──────────────────────────────────────────────────────── -->
    <div class="space-y-5">

      <!-- Unit details -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-amber-400/80 uppercase tracking-widest">Unit Details</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Purchase Price (AED)</span>
            <input type="number" bind:value={cost} min="0" step="10000"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Developer Admin Fee (AED)</span>
            <input type="number" bind:value={adminFee} min="0" step="500"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Internal Area (sqft)</span>
            <input type="number" bind:value={internalArea} min="0" step="10"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Balcony (sqft)</span>
            <input type="number" bind:value={balconyArea} min="0" step="5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <div class="space-y-1">
            <span class="text-[11px] text-white/50">Total Area</span>
            <div class="w-full bg-white/3 border border-white/6 rounded-lg px-3 py-2 text-sm text-white/60 tabular-nums">{totalArea.toLocaleString('en-AE')} sqft</div>
          </div>
        </div>
        <!-- DLD info line -->
        <p class="text-[11px] text-white/30 pl-0.5">DLD fee (4% + AED 580) = <span class="text-amber-400/70">{fmtAed(dldFee)}</span> · Total acquisition cost = <span class="text-amber-400/70">{fmtAed(totalPurchaseCost)}</span></p>
      </fieldset>

      <!-- Rental inputs -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-emerald-400/80 uppercase tracking-widest">Rental Analysis (at Handover)</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Comparable Rent today (AED/yr)</span>
            <input type="number" bind:value={comparableRent} min="0" step="1000"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Years till Handover</span>
            <input type="number" bind:value={yearsTillHandover} min="0" max="10" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Rental Appreciation over Build (%)</span>
            <input type="number" bind:value={rentalAppPct} min="0" max="100" step="1"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Furnished Premium (AED/yr)</span>
            <input type="number" bind:value={furnishedPremium} min="0" step="1000"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Management Fee (%)</span>
            <input type="number" bind:value={mgmtFeePct} min="0" max="30" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Utilities (AED/mth)</span>
            <input type="number" bind:value={utilitiesMonthly} min="0" step="100"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Service Charge (AED/sqft)</span>
            <input type="number" bind:value={serviceChargePsf} min="0" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <p class="text-[11px] text-white/30 pl-0.5">
          Service charge = (internal + 25% balcony) × {serviceChargePsf} psf + 5% VAT = <span class="text-amber-400/70">{fmtAed(serviceCharge)}/yr</span>
        </p>
      </fieldset>

      <!-- Capital gains inputs -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-blue-400/80 uppercase tracking-widest">Capital Gains Estimation</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Time of Resale (years from today)</span>
            <input type="number" bind:value={yearsToResale} min="0" max="30" step="1"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Expected Annual Appreciation (%)</span>
            <input type="number" bind:value={annualAppPct} min="0" max="50" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Other Appreciation Factors (%)</span>
            <input type="number" bind:value={otherAppPct} min="0" max="20" step="0.5"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Resale Broker Fee (%)</span>
            <input type="number" bind:value={resaleBrokerPct} min="0" max="5" step="0.25"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30" />
          </label>
        </div>
      </fieldset>

    </div><!-- end left -->

    <!-- ── RIGHT: Results ────────────────────────────────────────────────────── -->
    <div class="space-y-4">

      <!-- Rental Yield Card -->
      <div class="rounded-xl border border-emerald-500/20 bg-emerald-950/30 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h5 class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Rental Yield at Handover</h5>
          <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide {rentalObjective ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/15 text-red-400'}">
            {rentalObjective ? '✓ 7%+ Target Met' : '✗ Below 7% Target'}
          </span>
        </div>

        <!-- Revenue build-up -->
        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Comparable rent × (1 + {rentalAppPct}%)^{yearsTillHandover}yr</span>
            <span class="tabular-nums text-white/80">{fmtAed(comparableRent * Math.pow(1 + rentalAppPct/100, yearsTillHandover))}</span>
          </div>
          {#if furnishedPremium > 0}
          <div class="flex justify-between text-white/60">
            <span>Furnished premium</span>
            <span class="tabular-nums text-white/80">+ {fmtAed(furnishedPremium)}</span>
          </div>
          {/if}
          <div class="flex justify-between font-semibold text-white border-t border-white/10 pt-1.5">
            <span>Gross Rental Revenue</span>
            <span class="tabular-nums">{fmtAed(grossRental)}</span>
          </div>
        </div>

        <!-- Deductions -->
        <div class="space-y-1.5 text-xs border-t border-white/8 pt-2">
          {#if mgmtFee > 0}
          <div class="flex justify-between text-white/55">
            <span>Management fee ({mgmtFeePct}%)</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(mgmtFee)}</span>
          </div>
          {/if}
          {#if utilities > 0}
          <div class="flex justify-between text-white/55">
            <span>Utilities</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(utilities)}</span>
          </div>
          {/if}
          <div class="flex justify-between text-white/55">
            <span>Service charge + VAT</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(serviceCharge)}</span>
          </div>
          <div class="flex justify-between font-bold text-white border-t border-white/10 pt-1.5">
            <span>Net Rental Revenue</span>
            <span class="tabular-nums {netRental >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtAed(netRental)}</span>
          </div>
        </div>

        <!-- Yield metrics -->
        <div class="grid grid-cols-3 gap-2 pt-1">
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Gross Yield</p>
            <p class="text-lg font-black tabular-nums {grossYield >= 7 ? 'text-emerald-400' : 'text-amber-400'}">{fmtPct(grossYield)}</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Net Yield</p>
            <p class="text-lg font-black tabular-nums {netYield >= 7 ? 'text-emerald-400' : netYield >= 5 ? 'text-amber-400' : 'text-red-400'}">{fmtPct(netYield)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">on total cost</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Payback</p>
            <p class="text-lg font-black tabular-nums text-white/80">{netYield > 0 ? paybackYears.toFixed(1) : '∞'} yrs</p>
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

        <!-- Selling price -->
        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Potential selling price (after {yearsToResale}yr @ {annualAppPct + otherAppPct}%/yr)</span>
            <span class="tabular-nums text-white/80 font-semibold">{fmtAed(sellingPrice)}</span>
          </div>
        </div>

        <!-- Cost deductions -->
        <div class="space-y-1.5 text-xs border-t border-white/8 pt-2">
          <div class="flex justify-between text-white/55">
            <span>Original purchase price</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(cost)}</span>
          </div>
          <div class="flex justify-between text-white/55">
            <span>DLD + admin fees at purchase</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(dldFee + adminFee)}</span>
          </div>
          <div class="flex justify-between text-white/55">
            <span>Resale broker fee ({resaleBrokerPct}%)</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(resaleBrokerFee)}</span>
          </div>
          <div class="flex justify-between font-bold text-white border-t border-white/10 pt-1.5">
            <span>Net Profit</span>
            <span class="tabular-nums {netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtAed(netProfit)}</span>
          </div>
        </div>

        <!-- Return metrics -->
        <div class="grid grid-cols-3 gap-2 pt-1">
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Total Return</p>
            <p class="text-lg font-black tabular-nums {netProfitPct >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtPct(netProfitPct)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">on all-in cost</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Per Year (CAGR)</p>
            <p class="text-lg font-black tabular-nums {netProfitPerYear >= 7 ? 'text-emerald-400' : netProfitPerYear >= 5 ? 'text-amber-400' : 'text-red-400'}">{fmtPct(netProfitPerYear)}</p>
          </div>
          <div class="rounded-lg bg-white/5 px-3 py-2.5 text-center">
            <p class="text-[10px] text-white/40 uppercase tracking-wide">Net Profit</p>
            <p class="text-base font-black tabular-nums {netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'} leading-tight">
              {netProfit >= 0 ? '+' : ''}{Math.abs(netProfit) >= 1_000_000 ? (netProfit/1_000_000).toFixed(2) + 'M' : Math.round(netProfit/1000) + 'K'}
            </p>
            <p class="text-[9px] text-white/25 mt-0.5">AED</p>
          </div>
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-[10px] text-white/20 leading-relaxed px-0.5">
        Indicative estimates only. Assumes {annualAppPct + otherAppPct}%/yr compound appreciation on purchase price, DLD 4% + AED 580 registration, and service charge at 105% of {serviceChargePsf} AED/sqft on (internal + 25% balcony). Cross-verify rental comparables on ADInteract · Sales and rental data.
      </p>

    </div><!-- end right -->

  </div><!-- end grid -->
</div>
