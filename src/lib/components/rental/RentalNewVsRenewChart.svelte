<script lang="ts">
  import * as echarts from 'echarts';
  import { onMount } from 'svelte';
  import type { NewVsRenewRow } from '$lib/db/rental_types';

  let { data }: { data: NewVsRenewRow[] } = $props();

  let chartEl = $state<HTMLDivElement>();
  let chart: echarts.ECharts | null = null;

  function fmtK(n: number | null): string {
    if (n === null || n === undefined) return '—';
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n / 1_000)}K`;
    return `AED ${Math.round(n)}`;
  }

  onMount(() => {
    if (!chartEl) return;
    chart = echarts.init(chartEl);
    window.addEventListener('resize', () => chart?.resize());
    return () => { chart?.dispose(); chart = null; };
  });

  $effect(() => {
    if (!chart || !data?.length) return;

    const layouts   = data.map((d) => d.layout.charAt(0).toUpperCase() + d.layout.slice(1));
    const newRents  = data.map((d) => Math.round(d.newRent   ?? 0));
    const renRents  = data.map((d) => Math.round(d.renewRent ?? 0));
    const gaps      = data.map((d) => d.gapPct);

    chart.setOption({
      animation: true,
      grid: { top: 8, right: 100, bottom: 8, left: 70, containLabel: false },
      legend: {
        data: ['New contract', 'Renewal'],
        top: 'bottom',
        textStyle: { fontSize: 11, color: '#6b7280' },
        icon: 'roundRect',
        itemWidth: 12, itemHeight: 8
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#fff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
        formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
          const arr  = Array.isArray(params) ? params : [params];
          const label = arr[0]?.axisValue ?? '';
          const idx   = layouts.indexOf(label as string);
          const gap   = gaps[idx];
          const newV  = arr.find((p) => p.seriesName === 'New contract')?.value as number ?? 0;
          const renV  = arr.find((p) => p.seriesName === 'Renewal')?.value as number ?? 0;
          const gapLine = gap !== null
            ? `<br/><span style="color:#059669;font-weight:600">New is ${gap > 0 ? '+' : ''}${gap}% vs Renewal</span>`
            : '';
          return (
            `<b>${label}</b><br/>` +
            `New:     <b>${fmtK(newV)}</b><br/>` +
            `Renewal: <b>${fmtK(renV)}</b>` +
            gapLine
          );
        }
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 10, color: '#6b7280',
          formatter: (v: number) => v >= 1_000_000 ? `${(v/1_000_000).toFixed(1)}M` : `${Math.round(v/1_000)}K`
        },
        splitLine: { lineStyle: { color: '#f3f4f6' } }
      },
      yAxis: {
        type: 'category',
        data: [...layouts].reverse(),
        axisLabel: { fontSize: 11, color: '#374151' },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [
        {
          name: 'New contract',
          type: 'bar',
          data: [...newRents].reverse(),
          barMaxWidth: 18,
          itemStyle: { color: '#1B4332', borderRadius: [0, 4, 4, 0] },
          label: {
            show: true, position: 'right',
            formatter: (p: { value: number }) => fmtK(p.value),
            fontSize: 10, color: '#374151'
          }
        },
        {
          name: 'Renewal',
          type: 'bar',
          data: [...renRents].reverse(),
          barMaxWidth: 18,
          itemStyle: { color: '#C8A951', borderRadius: [0, 4, 4, 0] },
          label: { show: false }
        }
      ]
    });
  });
</script>

{#if data.length === 0}
  <div class="h-56 flex items-center justify-center text-gray-400 text-sm">No data</div>
{:else}
  <div bind:this={chartEl} class="w-full" style="height: {Math.max(200, data.length * 50 + 40)}px"></div>
{/if}
