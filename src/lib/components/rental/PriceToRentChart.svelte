<script lang="ts">
  import * as echarts from 'echarts';
  import { onMount } from 'svelte';
  import type { PriceToRentRow } from '$lib/db/rental_types';

  let { data }: { data: PriceToRentRow[] } = $props();

  let chartEl = $state<HTMLDivElement>();
  let chart: echarts.ECharts | null = null;

  function fmtM(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n / 1_000)}K`;
    return `AED ${Math.round(n)}`;
  }

  /** Colour ramp: low yield = gray-blue, high yield = brand green */
  function yieldColor(yieldPct: number, maxYield: number): string {
    const ratio = Math.min(yieldPct / Math.max(maxYield, 1), 1);
    // Interpolate from #94a3b8 (gray) → #1B4332 (navy green)
    const r = Math.round(148 + (27  - 148) * ratio);
    const g = Math.round(163 + (67  - 163) * ratio);
    const b = Math.round(184 + (50  - 184) * ratio);
    return `rgb(${r},${g},${b})`;
  }

  onMount(() => {
    if (!chartEl) return;
    chart = echarts.init(chartEl);
    window.addEventListener('resize', () => chart?.resize());
    return () => { chart?.dispose(); chart = null; };
  });

  $effect(() => {
    if (!chart || !data?.length) return;

    // Sort lowest → highest so highest yield is at top
    const sorted   = [...data].sort((a, b) => a.grossYieldPct - b.grossYieldPct);
    const districts = sorted.map((d) => d.district);
    const yields    = sorted.map((d) => d.grossYieldPct);
    const maxYield  = Math.max(...yields);

    chart.setOption({
      animation: true,
      grid: { top: 8, right: 60, bottom: 24, left: 8, containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#fff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
        formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
          const arr = Array.isArray(params) ? params : [params];
          const idx = districts.indexOf(arr[0]?.axisValue as string);
          const row = sorted[idx];
          if (!row) return '';
          return (
            `<b>${row.district}</b><br/>` +
            `Gross yield: <b style="color:#1B4332">${row.grossYieldPct.toFixed(2)}%</b><br/>` +
            `Median sale:  ${fmtM(row.medianSalePrice)}<br/>` +
            `Median rent:  ${fmtM(row.medianAnnualRent)}<br/>` +
            `Payback:      ${row.priceToRentYears.toFixed(1)} yrs`
          );
        }
      },
      xAxis: {
        type: 'value',
        name: 'Gross yield (%)',
        nameTextStyle: { fontSize: 10, color: '#9ca3af' },
        axisLabel: { fontSize: 10, color: '#6b7280', formatter: (v: number) => `${v}%` },
        splitLine: { lineStyle: { color: '#f3f4f6' } }
      },
      yAxis: {
        type: 'category',
        data: districts,
        axisLabel: { fontSize: 11, color: '#374151', width: 160, overflow: 'truncate' },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [{
        type: 'bar',
        data: yields.map((y) => ({
          value: y,
          itemStyle: { color: yieldColor(y, maxYield), borderRadius: [0, 4, 4, 0] }
        })),
        barMaxWidth: 22,
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value: number }) => `${(p.value as number).toFixed(2)}%`,
          fontSize: 10,
          color: '#374151',
          fontWeight: 600
        }
      }]
    });
  });
</script>

{#if data.length === 0}
  <div class="h-64 flex items-center justify-center text-gray-400 text-sm">
    No matching districts found in both sales and rental data.
  </div>
{:else}
  <div bind:this={chartEl} class="w-full" style="height: {Math.max(240, data.length * 38)}px"></div>
{/if}
