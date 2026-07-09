<script lang="ts">
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { browser } from '$app/environment';
  import { decodeDeal, type DealSnapshot, type OffplanDealSnapshot, type ReadyDealSnapshot } from '$lib/utils/dealShare';

  // ── Decode state from URL param ────────────────────────────────────────────
  let deal = $derived.by((): DealSnapshot | null => {
    if (!browser) return null;
    const s = $page.url.searchParams.get('s');
    if (!s) return null;
    return decodeDeal(s);
  });

  let isOffplan = $derived(deal?.type === 'offplan');
  let op = $derived(isOffplan ? (deal as OffplanDealSnapshot) : null);
  let rd = $derived(!isOffplan && deal ? (deal as ReadyDealSnapshot) : null);
  let agentCard = $derived(deal?.agentCard ?? null);

  // ── Formatters ─────────────────────────────────────────────────────────────
  function fmtAed(v: number | undefined): string {
    if (v == null || !isFinite(v)) return '—';
    return 'AED ' + Math.round(v).toLocaleString('en-AE');
  }
  function fmtNum(v: number | undefined): string {
    if (v == null || !isFinite(v)) return '—';
    return Math.round(v).toLocaleString('en-AE');
  }
  function fmtPct(v: number | undefined, dp = 1): string {
    if (v == null || !isFinite(v)) return '—';
    return v.toFixed(dp) + '%';
  }

  // ── Share this page (copy current URL) ─────────────────────────────────────
  let copyDone = $state(false);
  async function copyLink() {
    if (!browser) return;
    await navigator.clipboard.writeText(window.location.href);
    copyDone = true;
    setTimeout(() => { copyDone = false; }, 2000);
  }

  // ── ROI colour ─────────────────────────────────────────────────────────────
  function roiColour(v: number | undefined): string {
    if (!v) return 'text-gray-600';
    if (v >= 14) return 'text-emerald-600';
    if (v >= 7)  return 'text-amber-600';
    return 'text-red-600';
  }

  // ── Page title (no control flow inside <title> in Svelte 5) ──────────────────
  let pageTitle = $derived(
    deal
      ? `${deal.projectName ?? (isOffplan ? 'Off-Plan' : 'Ready Property')} Deal Analysis | ADInteract`
      : 'Deal Analysis | ADInteract'
  );

  // ── Maid's room pct ────────────────────────────────────────────────────────
  function maidsPctVal(layout: string | undefined, maidsRoom: string | undefined): number {
    if (maidsRoom !== 'yes') return 0;
    const l = (layout ?? '').toLowerCase();
    if (l === '2 beds') return 10;
    if (l === '3 beds') return 15;
    return 0;
  }

  // ── Furnishing label / pct ──────────────────────────────────────────────────
  function furnishingLabel(t: string | undefined): string {
    if (t === 'basic_airbnb')        return 'Basic AirBnB';
    if (t === 'highend_airbnb')      return 'High-end AirBnB';
    if (t === 'branded_hospitality') return 'Branded hospitality';
    return 'None';
  }
  function furnishingPctVal(t: string | undefined): number {
    if (t === 'basic_airbnb')        return 10;
    if (t === 'highend_airbnb')      return 20;
    if (t === 'branded_hospitality') return 25;
    return 0;
  }

  // ── Mortgage type label ─────────────────────────────────────────────────────
  function mtLabel(t: string | undefined): string {
    if (t === '1st') return '1st property';
    if (t === '2nd') return '2nd property';
    return 'No mortgage';
  }
  function residencyLabel(r: string | undefined): string {
    if (r === 'uae_national') return 'UAE National';
    if (r === 'non_resident') return 'Non-Resident';
    return 'UAE Resident';
  }
</script>

<svelte:head>
  <title>{pageTitle}</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<!-- ── Outer wrapper ─────────────────────────────────────────────────────── -->
<div class="min-h-screen bg-gray-50">

  <!-- ── Brand header bar ──────────────────────────────────────────────────── -->
  <div class="bg-[#0a2318] border-b border-white/8">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
      <a href="{base}/" class="flex items-center gap-2 no-underline">
        <span class="text-base font-black text-white tracking-tight">ADInteract</span>
        <span class="hidden sm:inline text-[10px] text-white/30 border-s border-white/15 ps-2 ms-1">Abu Dhabi Property Intelligence</span>
      </a>
      <span class="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 border border-amber-500/25 px-2.5 py-0.5 text-[10px] font-bold text-amber-400 tracking-wider uppercase">
        Deal Analysis
      </span>
    </div>
  </div>

  <!-- ── Content ───────────────────────────────────────────────────────────── -->
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-5">

    <!-- Agent card (shown when deal was shared with a logged-in agent's profile) -->
    {#if agentCard}
      <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 flex items-center gap-4">
        {#if agentCard.avatar}
          <img src={agentCard.avatar} alt={agentCard.name} class="w-12 h-12 rounded-full object-cover flex-shrink-0 border-2 border-emerald-300" />
        {:else}
          <div class="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center text-lg font-bold flex-shrink-0">
            {agentCard.name?.[0]?.toUpperCase() ?? '?'}
          </div>
        {/if}
        <div class="flex-1 min-w-0">
          <p class="font-bold text-emerald-900 text-sm">{agentCard.name}</p>
          {#if agentCard.identity}
            <p class="text-xs text-emerald-600">{agentCard.identity}</p>
          {/if}
        </div>
        {#if agentCard.whatsapp}
          <a
            href="https://wa.me/{agentCard.whatsapp.replace(/\D/g, '')}?text={encodeURIComponent('Hi, I saw your property analysis on ADInteract and wanted to connect.')}"
            target="_blank"
            rel="noopener noreferrer"
            class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-full bg-green-600 text-white px-4 py-2 text-xs font-bold hover:bg-green-700 transition-colors"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
            </svg>
            WhatsApp
          </a>
        {/if}
      </div>
    {/if}

    {#if !deal}
      <!-- Invalid / missing state -->
      <div class="rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-12 text-center">
        <p class="text-sm font-semibold text-gray-600">No deal analysis found</p>
        <p class="text-xs text-gray-400 mt-1">This link may be invalid or has expired.</p>
        <a
          href="{base}/investors/calculator"
          class="mt-5 inline-flex items-center gap-2 rounded-full bg-[#0a2318] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#143524] transition-colors"
        >
          Run your own analysis →
        </a>
      </div>

    {:else}
      <!-- ── Property header ──────────────────────────────────────────────── -->
      <div class="rounded-2xl bg-white border border-gray-100 shadow-sm px-5 py-4">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div>
            {#if deal.projectName}
              <h1 class="text-lg font-bold text-gray-900">{deal.projectName}</h1>
            {/if}
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-sm text-gray-500">
              {#if deal.district}
                <span>{deal.district}</span>
              {/if}
              {#if deal.layout}
                <span class="capitalize">· {deal.layout}</span>
              {/if}
              {#if deal.developer}
                <span class="text-gray-400">· {deal.developer}</span>
              {/if}
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider
                {isOffplan ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}">
                {isOffplan ? 'Off-Plan' : 'Ready Property'}
              </span>
            </div>
          </div>
          <!-- Copy link -->
          <button
            type="button"
            onclick={copyLink}
            class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-600 hover:border-gray-300 hover:text-gray-800 transition-colors"
          >
            {#if copyDone}
              <svg class="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
              Copied!
            {:else}
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
              </svg>
              Copy link
            {/if}
          </button>
        </div>
      </div>

      <!-- ── Total ROI hero ───────────────────────────────────────────────── -->
      <div class="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
        <div class="grid grid-cols-3 divide-x divide-gray-100">
          <div class="px-2 sm:px-4 py-4 sm:py-5 text-center">
            <p class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-tight">Net Yield p.a.</p>
            <p class="text-2xl sm:text-3xl font-black tabular-nums mt-2 {roiColour(deal.netYield)}">
              {fmtPct(deal.netYield)}
            </p>
          </div>
          <div class="px-2 sm:px-4 py-4 sm:py-5 text-center">
            <p class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-tight">Capital Gain p.a.</p>
            <p class="text-2xl sm:text-3xl font-black tabular-nums mt-2
              {isOffplan ? roiColour(op?.netProfitPerYear) : roiColour(rd?.netProfitPerYear)}">
              {fmtPct(isOffplan ? op?.netProfitPerYear : rd?.netProfitPerYear)}
            </p>
          </div>
          <div class="px-2 sm:px-4 py-4 sm:py-5 text-center bg-gray-50/60">
            <p class="text-[9px] sm:text-[10px] font-bold text-gray-500 uppercase tracking-widest leading-tight">Total ROI p.a.</p>
            <p class="text-2xl sm:text-3xl font-black tabular-nums mt-2 {roiColour(deal.totalRoiPa)}">
              {fmtPct(deal.totalRoiPa)}
            </p>
            <p class="text-[9px] text-gray-400 mt-1">yield + capital gain</p>
          </div>
        </div>
      </div>

      <!-- ── Purchase details ─────────────────────────────────────────────── -->
      <div class="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 bg-gray-50/60">
          <h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Purchase Details</h2>
        </div>
        <div class="px-4 py-3 divide-y divide-gray-50 text-sm">
          {#if isOffplan && op}
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Purchase price</span>
              <span class="font-semibold tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtAed(op.cost)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Size</span>
              <span class="font-semibold tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtNum(op.size)} sqft ({fmtNum(op.pricePerSqft)} AED/sqft)</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Registration fee (2% ADM)</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(op.registrationFee)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Developer registration</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(op.devRegistrationFee)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2 font-semibold">
              <span class="text-gray-800 min-w-0">Total all-in cost</span>
              <span class="tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtAed(op.totalPurchaseCost)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2 text-gray-400">
              <span class="min-w-0">Years till handover</span>
              <span class="flex-shrink-0 text-end">{op.yearsTillHandover} yr</span>
            </div>
          {:else if rd}
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Purchase price</span>
              <span class="font-semibold tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtAed(rd.price)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Size (living + balcony)</span>
              <span class="font-semibold tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtNum(rd.livingArea + rd.balconyArea)} sqft ({fmtNum(rd.pricePerSqft)} AED/sqft)</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Mortgage</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{mtLabel(rd.mortgageType)} · {residencyLabel(rd.residency)}</span>
            </div>
            {#if rd.mortgageAmount > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Mortgage amount</span>
                <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(rd.mortgageAmount)}</span>
              </div>
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Monthly payment</span>
                <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(rd.totalMonthlyMortgage)}</span>
              </div>
            {/if}
            <div class="flex justify-between py-2 gap-2 font-semibold">
              <span class="text-gray-800 min-w-0">Equity injection</span>
              <span class="tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtAed(rd.equityInjection)}</span>
            </div>
          {/if}
        </div>
      </div>

      <!-- ── Rental analysis ──────────────────────────────────────────────── -->
      <div class="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 bg-gray-50/60">
          <h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Rental Analysis</h2>
        </div>
        <div class="px-4 py-3 divide-y divide-gray-50 text-sm">
          {#if isOffplan && op}
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Comparable rent (ADREC {op.district || 'Abu Dhabi'} median)</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(op.comparableRent)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Rental appreciation rate</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtPct(op.rentalAppPct)} p.a.</span>
            </div>
            {#if furnishingPctVal(op.furnishingType) > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Furnishing premium · {furnishingLabel(op.furnishingType)}</span>
                <span class="tabular-nums text-emerald-600 flex-shrink-0 text-end">+{fmtPct(furnishingPctVal(op.furnishingType), 0)}</span>
              </div>
            {/if}
            {#if maidsPctVal(op.layout, op.maidsRoom) > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Maid's room premium</span>
                <span class="tabular-nums text-emerald-600 flex-shrink-0 text-end">+{fmtPct(maidsPctVal(op.layout, op.maidsRoom), 0)}</span>
              </div>
            {/if}
            <div class="flex justify-between py-2 gap-2 font-semibold">
              <span class="text-gray-800 min-w-0">Gross rental at handover</span>
              <span class="tabular-nums text-emerald-700 flex-shrink-0 text-end">{fmtAed(op.grossRental)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Service charge ({op.serviceChargePsf} AED/sqft + 5% VAT)</span>
              <span class="tabular-nums text-red-500 flex-shrink-0 text-end">− {fmtAed(op.size * op.serviceChargePsf * 1.05)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2 font-semibold">
              <span class="text-gray-800 min-w-0">Net rental income</span>
              <span class="tabular-nums flex-shrink-0 text-end {op.netRental >= 0 ? 'text-emerald-700' : 'text-red-600'}">{fmtAed(op.netRental)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Gross yield</span>
              <span class="tabular-nums font-semibold text-gray-800 flex-shrink-0 text-end">{fmtPct(op.grossYield)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-600 font-medium min-w-0">Net yield (on total cost)</span>
              <span class="tabular-nums font-bold flex-shrink-0 text-end {roiColour(op.netYield)}">{fmtPct(op.netYield)}</span>
            </div>
          {:else if rd}
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Annual rent</span>
              <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtAed(rd.annualRent)}</span>
            </div>
            {#if furnishingPctVal(rd.furnishingType) > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Furnishing premium · {furnishingLabel(rd.furnishingType)}</span>
                <span class="tabular-nums text-emerald-600 flex-shrink-0 text-end">+{fmtPct(furnishingPctVal(rd.furnishingType), 0)}</span>
              </div>
            {/if}
            {#if maidsPctVal(rd.layout, rd.maidsRoom) > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Maid's room premium</span>
                <span class="tabular-nums text-emerald-600 flex-shrink-0 text-end">+{fmtPct(maidsPctVal(rd.layout, rd.maidsRoom), 0)}</span>
              </div>
            {/if}
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-500 min-w-0">Service charge</span>
              <span class="tabular-nums text-red-500 flex-shrink-0 text-end">− {fmtAed(rd.serviceCharge)}</span>
            </div>
            {#if rd.mortgageAmount > 0}
              <div class="flex justify-between py-2 gap-2">
                <span class="text-gray-500 min-w-0">Annual mortgage payments</span>
                <span class="tabular-nums text-red-500 flex-shrink-0 text-end">− {fmtAed(rd.totalMonthlyMortgage * 12)}</span>
              </div>
            {/if}
            <div class="flex justify-between py-2 gap-2 font-semibold">
              <span class="text-gray-800 min-w-0">Net annual cashflow</span>
              <span class="tabular-nums flex-shrink-0 text-end {rd.netAnnualRental >= 0 ? 'text-emerald-700' : 'text-red-600'}">{fmtAed(rd.netAnnualRental)}</span>
            </div>
            <div class="flex justify-between py-2 gap-2">
              <span class="text-gray-600 font-medium min-w-0">Net yield (on equity)</span>
              <span class="tabular-nums font-bold flex-shrink-0 text-end {roiColour(rd.netYield)}">{fmtPct(rd.netYield)}</span>
            </div>
          {/if}
        </div>
      </div>

      <!-- ── Capital gains ────────────────────────────────────────────────── -->
      <div class="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 bg-gray-50/60">
          <h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Capital Gains — {deal.yearsToResale}yr Horizon</h2>
        </div>
        <div class="px-4 py-3 divide-y divide-gray-50 text-sm">
          <div class="flex justify-between py-2 gap-2">
            <span class="text-gray-500 min-w-0">Appreciation rate</span>
            <span class="tabular-nums text-gray-700 flex-shrink-0 text-end">{fmtPct(deal.annualAppPct)} p.a.{deal.otherFactorType === 'yes' ? ' + furnished/branded (+10%)' : ''}</span>
          </div>
          <div class="flex justify-between py-2 gap-2 font-semibold">
            <span class="text-gray-800 min-w-0">Projected selling price</span>
            <span class="tabular-nums text-gray-900 flex-shrink-0 text-end">{fmtAed(deal.sellingPrice)}</span>
          </div>
          <div class="flex justify-between py-2 gap-2 font-semibold">
            <span class="text-gray-800 min-w-0">Net profit</span>
            <span class="tabular-nums flex-shrink-0 text-end {deal.netProfit >= 0 ? 'text-emerald-700' : 'text-red-600'}">
              {deal.netProfit >= 0 ? '+' : ''}{fmtAed(deal.netProfit)}
            </span>
          </div>
          <div class="flex justify-between py-2 gap-2">
            <span class="text-gray-600 font-medium min-w-0">Capital gain CAGR</span>
            <span class="tabular-nums font-bold flex-shrink-0 text-end {roiColour(deal.netProfitPerYear)}">{fmtPct(deal.netProfitPerYear)}</span>
          </div>
        </div>
      </div>

      <!-- ── Disclaimer ───────────────────────────────────────────────────── -->
      <p class="text-[10px] text-gray-400 leading-relaxed px-1">
        Indicative estimates only. Powered by ADREC registered transaction data via ADInteract. Does not constitute financial or investment advice. Transaction costs (2% ADM fee, agency fees) not fully reflected in ROI. Verify all figures with a qualified advisor before making any investment decision.
      </p>

      <!-- ── CTA ─────────────────────────────────────────────────────────── -->
      <div class="rounded-2xl border border-dashed border-gray-200 bg-white px-5 py-5 text-center">
        <p class="text-sm font-semibold text-gray-700">Run your own Abu Dhabi property analysis</p>
        <p class="text-xs text-gray-400 mt-1">Auto-populated with live ADREC rent and price data</p>
        <a
          href="{base}/investors/calculator"
          class="mt-4 inline-flex items-center gap-2 rounded-full bg-[#0a2318] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#143524] transition-colors"
        >
          Open ROI Calculator →
        </a>
      </div>

    {/if}
  </div>
</div>
