<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';
  import { onMount } from 'svelte';

  let {
    purchasePrice = 0,
    grossRental = 0,
    rentalAppPct = 0,
    serviceCharge = 0,
    mgmtFeePct = 0,
    utilities = 0,
    annualAppPct = 0,
    monthlyMortgagePayment = 0,
  }: {
    purchasePrice: number;
    grossRental: number;
    rentalAppPct: number;
    serviceCharge: number;
    mgmtFeePct: number;
    utilities: number;
    annualAppPct: number;
    monthlyMortgagePayment?: number;
  } = $props();

  let years = $state<5 | 10>(5);
  let chartContainer: HTMLDivElement;
  let chartInstance: any;

  interface YearRow {
    year: number;
    rental: number;
    costs: number;
    net: number;
    value: number;
    cumulativeRoi: number;
  }

  let rows = $derived<YearRow[]>(
    Array.from({ length: years }, (_, i) => {
      const yr = i + 1;
      const rental = grossRental * Math.pow(1 + rentalAppPct / 100, yr);
      const costs  = serviceCharge + (rental * mgmtFeePct / 100) + utilities * 12 + monthlyMortgagePayment * 12;
      const net    = rental - costs;
      const value  = purchasePrice * Math.pow(1 + annualAppPct / 100, yr);
      const cumulativeRoi = purchasePrice > 0 ? ((value - purchasePrice + net * yr) / purchasePrice) * 100 : 0;
      return { year: yr, rental, costs, net, value, cumulativeRoi };
    })
  );

  function fmt(n: number) { return Math.round(n).toLocaleString('en-AE'); }
  function fmtPct(n: number) { return n.toFixed(1) + '%'; }

  async function renderChart() {
    if (!chartContainer || purchasePrice === 0) return;
    const echarts = await import('echarts');
    if (chartInstance) chartInstance.dispose();
    chartInstance = echarts.init(chartContainer, undefined, { renderer: 'canvas' });
    chartInstance.setOption({
      grid: { left: 55, right: 60, top: 20, bottom: 30 },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      xAxis: { type: 'category', data: rows.map(r => `Yr ${r.year}`), axisLabel: { fontSize: 11 } },
      yAxis: [
        { type: 'value', name: 'AED', axisLabel: { fontSize: 10, formatter: (v: number) => (v >= 1e6 ? (v/1e6).toFixed(1)+'M' : (v/1e3).toFixed(0)+'K') } },
        { type: 'value', name: 'ROI %', position: 'right', axisLabel: { fontSize: 10, formatter: (v: number) => v.toFixed(0)+'%' } },
      ],
      series: [
        { name: 'Net Cash Flow', type: 'bar', data: rows.map(r => Math.round(r.net)), itemStyle: { color: '#10b981' } },
        { name: 'Property Value', type: 'bar', data: rows.map(r => Math.round(r.value)), itemStyle: { color: '#3b82f6' }, yAxisIndex: 0 },
        { name: 'Cumulative ROI %', type: 'line', yAxisIndex: 1, data: rows.map(r => +r.cumulativeRoi.toFixed(1)), lineStyle: { width: 2 }, itemStyle: { color: '#f59e0b' }, symbol: 'circle', symbolSize: 6 },
      ],
    });
  }

  $effect(() => {
    rows; // track
    renderChart();
  });

  onMount(() => {
    renderChart();
    return () => { chartInstance?.dispose(); };
  });
</script>

{#if purchasePrice > 0}
  <div class="mt-6 rounded-xl border border-gray-200 overflow-hidden">
    <div class="flex items-center justify-between px-5 py-3.5 bg-gray-50 border-b border-gray-100">
      <h3 class="text-sm font-semibold text-gray-800">{m.cashflow_section_title()}</h3>
      <div class="flex rounded-lg border border-gray-200 overflow-hidden text-xs font-semibold">
        <button type="button" onclick={() => { years = 5; }} class="px-3 py-1.5 transition-colors {years === 5 ? 'bg-emerald-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}">{m.cashflow_toggle_5yr()}</button>
        <button type="button" onclick={() => { years = 10; }} class="px-3 py-1.5 transition-colors {years === 10 ? 'bg-emerald-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}">{m.cashflow_toggle_10yr()}</button>
      </div>
    </div>

    <!-- Chart -->
    <div class="px-4 pt-4 pb-2">
      <div bind:this={chartContainer} class="w-full h-52"></div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="bg-gray-50 text-gray-500 uppercase tracking-wider text-[10px]">
            <th class="px-4 py-2 text-start font-semibold">{m.cashflow_col_year()}</th>
            <th class="px-4 py-2 text-end font-semibold">{m.cashflow_col_rental()}</th>
            <th class="px-4 py-2 text-end font-semibold">{m.cashflow_col_costs()}</th>
            <th class="px-4 py-2 text-end font-semibold">{m.cashflow_col_net()}</th>
            <th class="px-4 py-2 text-end font-semibold">{m.cashflow_col_value()}</th>
            <th class="px-4 py-2 text-end font-semibold">{m.cashflow_col_roi()}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          {#each rows as r}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-2 font-semibold text-gray-700">Yr {r.year}</td>
              <td class="px-4 py-2 text-end text-gray-700">{fmt(r.rental)}</td>
              <td class="px-4 py-2 text-end text-gray-500">{fmt(r.costs)}</td>
              <td class="px-4 py-2 text-end font-semibold {r.net >= 0 ? 'text-emerald-700' : 'text-red-600'}">{fmt(r.net)}</td>
              <td class="px-4 py-2 text-end text-blue-700 font-semibold">{fmt(r.value)}</td>
              <td class="px-4 py-2 text-end font-bold {r.cumulativeRoi >= 0 ? 'text-amber-700' : 'text-red-600'}">{fmtPct(r.cumulativeRoi)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}
