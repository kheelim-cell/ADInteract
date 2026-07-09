<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';

  let {
    purchasePrice = 0,
    netAnnualRental = 0,
    onchange
  }: {
    purchasePrice: number;
    netAnnualRental: number;
    onchange?: (data: { monthlyPayment: number; equity: number; enabled: boolean }) => void;
  } = $props();

  let enabled = $state(false);
  let ltv = $state(75);
  let annualRate = $state(4.5);
  let termYears = $state(25);

  const TERMS = [5, 10, 15, 20, 25];

  let loanAmount     = $derived(purchasePrice * (ltv / 100));
  let equity         = $derived(purchasePrice - loanAmount);
  let monthlyRate    = $derived(annualRate / 12 / 100);
  let n              = $derived(termYears * 12);
  let monthlyPayment = $derived(
    monthlyRate > 0 && n > 0 && loanAmount > 0
      ? loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, n)) / (Math.pow(1 + monthlyRate, n) - 1)
      : 0
  );
  let totalInterest = $derived(monthlyPayment * n - loanAmount);
  let cashOnCash    = $derived(
    equity > 0 && netAnnualRental > 0
      ? ((netAnnualRental - monthlyPayment * 12) / equity) * 100
      : null
  );

  $effect(() => {
    onchange?.({ monthlyPayment: enabled ? monthlyPayment : 0, equity: enabled ? equity : purchasePrice, enabled });
  });

  function fmt(n: number) { return Math.round(n).toLocaleString('en-AE'); }
  function fmtPct(n: number | null) { return n == null ? '—' : n.toFixed(1) + '%'; }
</script>

<div class="mt-8 rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
  <!-- Toggle header -->
  <button
    type="button"
    onclick={() => { enabled = !enabled; }}
    class="w-full flex items-center justify-between px-6 py-4 bg-white hover:bg-gray-50 transition-colors text-start"
  >
    <span class="flex items-center gap-3 text-sm font-semibold text-gray-800">
      <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
        </svg>
      </span>
      {m.mortgage_section_toggle()}
    </span>
    <svg class="w-4 h-4 text-gray-400 transition-transform duration-200 {enabled ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  </button>

  {#if enabled}
    <div class="px-6 pb-6 pt-2 space-y-6 bg-white border-t border-gray-100">

      <!-- LTV slider -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">{m.mortgage_ltv_label()}</label>
          <span class="text-sm font-bold text-blue-600 tabular-nums">{ltv}%</span>
        </div>
        <input type="range" min="10" max="90" step="5" bind:value={ltv} class="w-full accent-blue-600 h-1.5" />
        <p class="text-[11px] text-gray-400">{m.mortgage_ltv_hint()}</p>
      </div>

      <!-- Rate + Term -->
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide">{m.mortgage_rate_label()}</label>
          <input
            type="number" min="1" max="15" step="0.1"
            bind:value={annualRate}
            class="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition"
          />
          <p class="text-[11px] text-gray-400">{m.mortgage_rate_hint()}</p>
        </div>
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide">{m.mortgage_term_label()}</label>
          <select bind:value={termYears} class="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition">
            {#each TERMS as t}
              <option value={t}>{t} yrs</option>
            {/each}
          </select>
        </div>
      </div>

      <!-- KPI tiles -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <p class="text-[10px] font-semibold text-blue-500 uppercase tracking-wide mb-1">{m.mortgage_monthly_payment()}</p>
          <p class="text-base font-bold text-blue-700 tabular-nums">AED {fmt(monthlyPayment)}</p>
        </div>
        <div class="rounded-xl border px-4 py-3 {cashOnCash != null && cashOnCash > 0 ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}">
          <p class="text-[10px] font-semibold uppercase tracking-wide mb-1 {cashOnCash != null && cashOnCash > 0 ? 'text-emerald-500' : 'text-red-400'}">{m.mortgage_cash_on_cash()}</p>
          <p class="text-base font-bold tabular-nums {cashOnCash != null && cashOnCash > 0 ? 'text-emerald-700' : 'text-red-600'}">{fmtPct(cashOnCash)}</p>
        </div>
        <div class="rounded-xl bg-red-50 border border-red-100 px-4 py-3">
          <p class="text-[10px] font-semibold text-red-400 uppercase tracking-wide mb-1">{m.mortgage_total_interest()}</p>
          <p class="text-base font-bold text-red-600 tabular-nums">AED {fmt(totalInterest)}</p>
        </div>
        <div class="rounded-xl bg-gray-50 border border-gray-200 px-4 py-3">
          <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">{m.mortgage_equity_required()}</p>
          <p class="text-base font-bold text-gray-800 tabular-nums">AED {fmt(equity)}</p>
        </div>
      </div>

    </div>
  {/if}
</div>
