<script lang="ts">
  import * as echarts from 'echarts';
  import { onMount } from 'svelte';
  import type { RentalLayoutRow } from '$lib/db/rental_types';

  let { data }: { data: RentalLayoutRow[] } = $props();

  let chartEl = $state<HTMLDivElement>();
  let chart: echarts.ECharts | null = null;

  function fmtK(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `${Math.round(n / 1_000)}K`;
    return String(Math.round(n));
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

    // Display labels nicely: "1 bed" → "1 Bed"
    const layouts = data.map((d) =>
      d.layout.charAt(0).toUpperCase() + d.layout.slice(1)
    );
    const lowerRents  = data.map((d) => Math.round(d.lowerRent  ?? 0));
    const medianRents = data.map((d) => Math.round(d.medianRent));
    const upperRents  = data.map((d) => Math.round(d.upperRent  ?? 0));

    chart.setOption({
      animation: true,
      grid: { top: 8, right: 80, bottom: 8, left: 70, containLabel: false },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#fff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
        formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
          const arr = Array.isArray(params) ? params : [params];
          const label = arr[0]?.axisValue;
          const lower  = arr.find((p) => p.seriesName === 'Lower')?.value  as number ?? 0;
          const median = arr.find((p) => p.seriesName === 'Median')?.value as number ?? 0;
          const upper  = arr.find((p) => p.seriesName === 'Upper')?.value  as number ?? 0;
          return (
            `<b>${label}</b><br/>` +
            `Upper: AED ${fmtK(upper)}<br/>` +
            `<b>Median: AED ${fmtK(median)}</b><br/>` +
            `Lower: AED ${fmtK(lower)}`
          );
        }
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 10,
          color: '#6b7280',
          formatter: (v: number) => `${fmtK(v)}`
        },
        splitLine: { lineStyle: { color: '#f3f4f6' } }
      },
      yAxis: {
        type: 'category',
        data: layouts,
        axisLabel: { fontSize: 11, color: '#374151' },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [
        {
          name: 'Lower',
          type: 'bar',
          data: lowerRents,
          barMaxWidth: 16,
          itemStyle: { color: '#dbeafe', borderRadius: [4, 0, 0, 4] },
          label: { show: false }
        },
        {
          name: 'Median',
          type: 'bar',
          data: medianRents,
          barMaxWidth: 16,
          itemStyle: { color: '#C8A951', borderRadius: 0 },
          label: {
            show: true,
            position: 'right',
            formatter: (p: { value: number }) => `AED ${fmtK(p.value)}`,
            fontSize: 10,
            color: '#374151'
          }
        },
        {
          name: 'Upper',
          type: 'bar',
          data: upperRents,
          barMaxWidth: 16,
          itemStyle: { color: '#bbf7d0', borderRadius: [0, 4, 4, 0] },
          label: { show: false }
        }
      ]
    });
  });
</script>

{#if data.length === 0}
  <div class="h-64 flex items-center justify-center text-gray-400 text-sm">No layout data</div>
{:else}
  <div bind:this={chartEl} class="w-full" style="height: {Math.max(160, data.length * 44)}px"></div>
{/if}
