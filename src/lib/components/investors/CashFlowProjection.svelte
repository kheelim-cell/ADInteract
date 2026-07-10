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
      const yr     = i + 1;
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
      backgroundColor: 'transparent',
      grid: { left: 64, right: 64, top: 24, bottom: 48 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        borderWidth: 1,
        textStyle: { color: '#f1f5f9', fontSize: 12 },
        formatter: (params: any[]) => {
          const label = params[0].axisValue;
          let html = `<div style="font-weight:600;margin-bottom:6px;color:#94a3b8">${label}</div>`;
          for (const p of params) {
            const isRoi = p.seriesName === 'Cumulative ROI %';
            const val = isRoi ? p.value.toFixed(1) + '%' : 'AED ' + Math.round(p.value).toLocaleString('en-AE');
            html += `<div style="display:flex;align-items:center;gap:8px;margin-top:4px">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color}"></span>
              <span style="color:#cbd5e1;flex:1">${p.seriesName}</span>
              <span style="font-weight:700;color:#f1f5f9">${val}</span>
            </div>`;
          }
          return html;
        }
      },
      legend: { show: false },
      xAxis: {
        type: 'category',
        data: rows.map(r => `Yr ${r.year}`),
        axisLabel: { fontSize: 11, color: '#94a3b8' },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: 'AED',
          nameTextStyle: { color: '#94a3b8', fontSize: 10 },
          axisLabel: {
            fontSize: 10,
            color: '#94a3b8',
            formatter: (v: number) => v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? (v / 1e3).toFixed(0) + 'K' : String(v),
          },
          splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        {
          type: 'value',
          position: 'right',
          axisLabel: {
            fontSize: 10,
            color: '#f59e0b',
            formatter: (v: number) => v.toFixed(0) + '%',
          },
          splitLine: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
        },
      ],
      series: [
        {
          name: 'Net Cash Flow',
          type: 'bar',
          barMaxWidth: 40,
          barCategoryGap: '40%',
          data: rows.map(r => Math.round(r.net)),
          itemStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#34d399' }, { offset: 1, color: '#059669' }] },
            borderRadius: [4, 4, 0, 0],
          },
          z: 2,
        },
        {
          name: 'Cumulative ROI %',
          type: 'line',
          yAxisIndex: 1,
          data: rows.map(r => +r.cumulativeRoi.toFixed(1)),
          smooth: true,
          lineStyle: { width: 2.5, color: '#f59e0b' },
          itemStyle: { color: '#f59e0b', borderWidth: 2, borderColor: '#fff' },
          symbol: 'circle',
          symbolSize: 7,
          areaStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(245,158,11,0.18)' }, { offset: 1, color: 'rgba(245,158,11,0)' }] }
          },
          z: 3,
        },
      ],
    });
  }

  $effect(() => {
    rows;
    renderChart();
  });

  onMount(() => {
    renderChart();
    return () => { chartInstance?.dispose(); };
  });
</script>

{#if purchasePrice > 0}
  <div class="mt-8 rounded-2xl border border-gray-200 overflow-hidden shadow-sm">

    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100">
      <div>
        <h3 class="text-sm font-semibold text-gray-900">{m.cashflow_section_title()}</h3>
        <p class="text-[11px] text-gray-400 mt-0.5">Compound growth · {annualAppPct}% annual appreciation</p>
      </div>
      <div class="flex rounded-lg border border-gray-200 overflow-hidden text-xs font-semibold">
        <button
          type="button"
          onclick={() => { years = 5; }}
          class="px-4 py-1.5 transition-colors {years === 5 ? 'bg-emerald-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}"
        >{m.cashflow_toggle_5yr()}</button>
        <button
          type="button"
          onclick={() => { years = 10; }}
          class="px-4 py-1.5 transition-colors border-l border-gray-200 {years === 10 ? 'bg-emerald-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}"
        >{m.cashflow_toggle_10yr()}</button>
      </div>
    </div>

    <!-- Chart -->
    <div class="px-6 pt-5 pb-3 bg-white">
      <div bind:this={chartContainer} class="w-full h-64"></div>
    </div>

    <!-- Colour legend strip -->
    <div class="flex items-center gap-5 px-6 pb-4 bg-white text-[11px] text-gray-500">
      <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-sm bg-emerald-500"></span> Net Cash Flow (AED)</span>
      <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-full bg-amber-400"></span> Cumulative ROI %</span>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border-t border-gray-100">
      <table class="w-full text-xs">
        <thead>
          <tr class="bg-gray-50">
            <th class="px-6 py-3 text-start text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{m.cashflow_col_year()}</th>
            <th class="px-4 py-3 text-end text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{m.cashflow_col_rental()}</th>
            <th class="px-4 py-3 text-end text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{m.cashflow_col_costs()}</th>
            <th class="px-4 py-3 text-end text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">{m.cashflow_col_net()}</th>
            <th class="px-4 py-3 text-end text-[10px] font-semibold text-blue-600 uppercase tracking-wider">{m.cashflow_col_value()}</th>
            <th class="px-6 py-3 text-end text-[10px] font-semibold text-amber-600 uppercase tracking-wider">{m.cashflow_col_roi()}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          {#each rows as r}
            <tr class="hover:bg-gray-50/70 transition-colors">
              <td class="px-6 py-3 font-semibold text-gray-700">Yr {r.year}</td>
              <td class="px-4 py-3 text-end text-gray-600 tabular-nums">{fmt(r.rental)}</td>
              <td class="px-4 py-3 text-end text-gray-400 tabular-nums">{fmt(r.costs)}</td>
              <td class="px-4 py-3 text-end font-semibold tabular-nums {r.net >= 0 ? 'text-emerald-600' : 'text-red-500'}">{fmt(r.net)}</td>
              <td class="px-4 py-3 text-end font-semibold text-blue-600 tabular-nums">{fmt(r.value)}</td>
              <td class="px-6 py-3 text-end font-bold tabular-nums {r.cumulativeRoi >= 0 ? 'text-amber-600' : 'text-red-500'}">{fmtPct(r.cumulativeRoi)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

  </div>
{/if}
