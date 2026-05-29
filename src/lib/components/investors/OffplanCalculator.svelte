<script lang="ts">
  import { metadata } from '$lib/stores/db';

  // ── Helpers ─────────────────────────────────────────────────────────────────
  function fmtAed(v: number): string {
    if (!isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number, dp = 1): string {
    if (!isFinite(v)) return '—';
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

  // ── Unit inputs ──────────────────────────────────────────────────────────────
  let district = $state('');
  let layout   = $state('');
  let cost     = $state(1_000_000);   // purchase price AED
  let size     = $state(945);         // total sqft

  const adminFee = 4_000;             // hardcoded

  // ── Rental inputs ────────────────────────────────────────────────────────────
  let comparableRent    = $state(50_000);
  let yearsTillHandover = $state(2);
  let rentalAppPct      = $state(15);
  let furnishedPremium  = $state(10_000);
  let mgmtFeePct        = $state(8);
  let utilitiesMonthly  = $state(0);
  let serviceChargePsf  = $state(15);

  // ── Capital gains inputs ─────────────────────────────────────────────────────
  let yearsToResale   = $state(5);
  let annualAppPct    = $state(12);
  let otherAppPct     = $state(0);
  let resaleBrokerPct = $state(2);

  // ── Derived: unit ────────────────────────────────────────────────────────────
  let pricePerSqft     = $derived(size > 0 ? cost / size : 0);
  let registrationFee   = $derived(cost * 0.02 + 1_000); // Abu Dhabi: 2% DARI/DMT + AED 1,000 title deed
  let totalPurchaseCost = $derived(cost + registrationFee + adminFee);

  // ── Derived: rental ──────────────────────────────────────────────────────────
  let grossRental   = $derived(
    comparableRent * Math.pow(1 + rentalAppPct / 100, yearsTillHandover) + furnishedPremium
  );
  let mgmtFee       = $derived(grossRental * mgmtFeePct / 100);
  let utilities     = $derived(utilitiesMonthly * 12);
  let serviceCharge = $derived(size * serviceChargePsf * 1.05);
  let netRental     = $derived(grossRental - mgmtFee - utilities - serviceCharge);

  let grossYield      = $derived(cost > 0 ? (grossRental / cost) * 100 : 0);
  let netYield        = $derived(totalPurchaseCost > 0 ? (netRental / totalPurchaseCost) * 100 : 0);
  let paybackYears    = $derived(netYield > 0 ? 100 / netYield : 0);
  let rentalObjective = $derived(netYield >= 7);

  // ── Derived: capital gains ────────────────────────────────────────────────────
  let totalAppRate     = $derived((annualAppPct + otherAppPct) / 100);
  let sellingPrice     = $derived(cost * Math.pow(1 + totalAppRate, yearsToResale));
  let resaleBrokerFee  = $derived(sellingPrice * resaleBrokerPct / 100);
  let totalAllInCost   = $derived(totalPurchaseCost + resaleBrokerFee); // totalPurchaseCost already includes registrationFee + adminFee
  let netProfit        = $derived(sellingPrice - totalAllInCost);
  let netProfitPct     = $derived(totalAllInCost > 0 ? (netProfit / totalAllInCost) * 100 : 0);
  let netProfitPerYear = $derived(
    yearsToResale > 0 && totalAllInCost > 0
      ? (Math.pow(sellingPrice / totalAllInCost, 1 / yearsToResale) - 1) * 100
      : 0
  );
  let capitalObjective = $derived(netProfitPerYear >= 7);

  // ── Shared input class ───────────────────────────────────────────────────────
  const inp = 'w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30';
  const sel = 'w-full bg-[#0a1a10] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 appearance-none cursor-pointer';
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

      <!-- ── Unit Details ───────────────────────────────────────────────────── -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-amber-400/80 uppercase tracking-widest">Unit Details</legend>

        <!-- District + Layout dropdowns (header row) -->
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

        <!-- Price + Size -->
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Price (AED)</span>
            <input type="number" bind:value={cost} min="0" step="10000" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Size (sqft)</span>
            <input type="number" bind:value={size} min="0" step="10" class={inp} />
          </label>
        </div>

        <!-- AED/sqft + acquisition cost info row -->
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-lg bg-amber-500/8 border border-amber-500/20 px-3 py-2.5">
            <p class="text-[10px] text-amber-400/70 uppercase tracking-wider">Price per sqft</p>
            <p class="text-base font-black text-amber-400 tabular-nums mt-0.5">
              {size > 0 ? Math.round(pricePerSqft).toLocaleString('en-AE') : '—'} <span class="text-xs font-semibold text-amber-400/60">AED/sqft</span>
            </p>
          </div>
          <div class="rounded-lg bg-white/3 border border-white/8 px-3 py-2.5">
            <p class="text-[10px] text-white/35 uppercase tracking-wider">Total Acquisition Cost</p>
            <p class="text-sm font-bold text-white/70 tabular-nums mt-0.5">{fmtAed(totalPurchaseCost)}</p>
            <p class="text-[9px] text-white/25 mt-0.5">Price + DARI/DMT (2% + 1,000) + Admin (4,000)</p>
          </div>
        </div>
      </fieldset>

      <!-- ── Rental Analysis ────────────────────────────────────────────────── -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-emerald-400/80 uppercase tracking-widest">Rental Analysis (at Handover)</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Comparable Rent today (AED/yr)</span>
            <input type="number" bind:value={comparableRent} min="0" step="1000" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Years till Handover</span>
            <input type="number" bind:value={yearsTillHandover} min="0" max="10" step="0.5" class={inp} />
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Rental Appreciation over Build (%)</span>
            <input type="number" bind:value={rentalAppPct} min="0" max="100" step="1" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Furnished Premium (AED/yr)</span>
            <input type="number" bind:value={furnishedPremium} min="0" step="1000" class={inp} />
          </label>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Management Fee (%)</span>
            <input type="number" bind:value={mgmtFeePct} min="0" max="30" step="0.5" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Utilities (AED/mth)</span>
            <input type="number" bind:value={utilitiesMonthly} min="0" step="100" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Service Charge (AED/sqft)</span>
            <input type="number" bind:value={serviceChargePsf} min="0" step="0.5" class={inp} />
          </label>
        </div>
        <p class="text-[11px] text-white/30 pl-0.5">
          Service charge = {size.toLocaleString('en-AE')} sqft × AED {serviceChargePsf} + 5% VAT = <span class="text-amber-400/70">{fmtAed(serviceCharge)}/yr</span>
        </p>
      </fieldset>

      <!-- ── Capital Gains ──────────────────────────────────────────────────── -->
      <fieldset class="space-y-3">
        <legend class="text-[10px] font-bold text-blue-400/80 uppercase tracking-widest">Capital Gains Estimation</legend>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Time of Resale (years from today)</span>
            <input type="number" bind:value={yearsToResale} min="0" max="30" step="1" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Expected Annual Appreciation (%)</span>
            <input type="number" bind:value={annualAppPct} min="0" max="50" step="0.5" class={inp} />
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Other Appreciation Factors (%)</span>
            <input type="number" bind:value={otherAppPct} min="0" max="20" step="0.5" class={inp} />
          </label>
          <label class="space-y-1">
            <span class="text-[11px] text-white/50">Resale Broker Fee (%)</span>
            <input type="number" bind:value={resaleBrokerPct} min="0" max="5" step="0.25" class={inp} />
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

        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Comparable rent × (1 + {rentalAppPct}%)^{yearsTillHandover}yr</span>
            <span class="tabular-nums text-white/80">{fmtAed(comparableRent * Math.pow(1 + rentalAppPct / 100, yearsTillHandover))}</span>
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

        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-white/60">
            <span>Potential selling price (after {yearsToResale}yr @ {annualAppPct + otherAppPct}%/yr)</span>
            <span class="tabular-nums text-white/80 font-semibold">{fmtAed(sellingPrice)}</span>
          </div>
        </div>

        <div class="space-y-1.5 text-xs border-t border-white/8 pt-2">
          <div class="flex justify-between text-white/55">
            <span>Original purchase price</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(cost)}</span>
          </div>
          <div class="flex justify-between text-white/55">
            <span>DARI/DMT reg. + admin fees at purchase</span>
            <span class="tabular-nums text-red-400/80">− {fmtAed(registrationFee + adminFee)}</span>
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
              {netProfit >= 0 ? '+' : ''}{Math.abs(netProfit) >= 1_000_000 ? (netProfit / 1_000_000).toFixed(2) + 'M' : Math.round(netProfit / 1000) + 'K'}
            </p>
            <p class="text-[9px] text-white/25 mt-0.5">AED</p>
          </div>
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-[10px] text-white/20 leading-relaxed px-0.5">
        Indicative estimates only. Abu Dhabi registration fee: 2% DARI/DMT + AED 1,000 title deed. Off-plan registration via DARI/Tamleek (Oqood equivalent). Admin AED 4,000. Assumes {annualAppPct + otherAppPct}%/yr compound appreciation. Service charge on full unit size + 5% VAT. Cross-verify rental comparables on ADInteract Sales and Rental data.
      </p>

    </div><!-- end right -->

  </div><!-- end grid -->
</div>
