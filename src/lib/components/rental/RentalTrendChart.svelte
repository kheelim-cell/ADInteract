<script lang="ts">
  import * as echarts from 'echarts';
  import { onMount } from 'svelte';
  import type { RentalTrendPoint } from '$lib/db/rental_types';

  let { data }: { data: RentalTrendPoint[] } = $props();

  let chartEl = $state<HTMLDivElement>();
  let chart: echarts.ECharts | null = null;

  function formatRent(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n).toLocaleString('en-US')}`;
    return `AED ${n}`;
  }

  onMount(() => {
    if (!chartEl) return;
    chart = echarts.init(chartEl);
    window.addEventListener('resize', () => chart?.resize());
    return () => {
      chart?.dispose();
      chart = null;
    };
  });

  $effect(() => {
    if (!chart || !data?.length) return;

    const years     = data.map((d) => d.year);
    const medians   = data.map((d) => Math.round(d.medianRent));

    chart.setOption({
      animation: true,
      textStyle: { fontFamily: 'Montserrat, system-ui, sans-serif' },
      grid: { top: 16, right: 24, bottom: 40, left: 72, containLabel: false },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12, fontFamily: 'Montserrat, system-ui, sans-serif' },
        formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
          const p = Array.isArray(params) ? params[0] : params;
          return `<b>${p.name}</b><br/>Median: <b>${formatRent(p.value as number)}</b>`;
        }
      },
      xAxis: {
        type: 'category',
        data: years,
        axisLabel: { fontSize: 11, color: '#6b7280', fontFamily: 'Montserrat, system-ui, sans-serif' },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 10,
          color: '#6b7280',
          fontFamily: 'Montserrat, system-ui, sans-serif',
          formatter: (v: number) => {
            if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
            if (v >= 1_000)     return `${(v / 1_000).toFixed(0)}K`;
            return String(v);
          }
        },
        splitLine: { lineStyle: { color: '#f3f4f6' } }
      },
      series: [
        {
          type: 'line',
          data: medians,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#C8A951', width: 2.5 },
          itemStyle: { color: '#C8A951', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(200,169,81,0.18)' },
              { offset: 1, color: 'rgba(200,169,81,0)' }
            ])
          }
        }
      ]
    });
  });
</script>

{#if data.length === 0}
  <div class="flex items-center justify-center text-gray-400 text-sm" style="height:280px">No trend data</div>
{:else}
  <div bind:this={chartEl} class="w-full" style="height:280px"></div>
{/if}
