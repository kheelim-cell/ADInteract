<script lang="ts">
  import * as echarts from 'echarts';
  import { onMount } from 'svelte';
  import type { RentalDistrictRow } from '$lib/db/rental_types';
  import { updateRentalFilter } from '$lib/stores/rental_filters';

  let { data }: { data: RentalDistrictRow[] } = $props();

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

    chart.on('click', (params: echarts.ECElementEvent) => {
      if (params.componentType === 'series') {
        const district = params.name as string;
        updateRentalFilter({ district });
      }
    });

    return () => {
      chart?.dispose();
      chart = null;
    };
  });

  $effect(() => {
    if (!chart || !data?.length) return;

    const districts = data.map((d) => d.district);
    const rents     = data.map((d) => Math.round(d.medianRent));

    chart.setOption({
      animation: true,
      grid: { top: 8, right: 88, bottom: 8, left: 8, containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#fff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
        formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
          const p = Array.isArray(params) ? params[0] : params;
          return `<b>${p.name}</b><br/>Median: AED ${fmtK(p.value as number)}/yr`;
        }
      },
      xAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#6b7280', formatter: (v: number) => `${fmtK(v)}` }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
      yAxis: { type: 'category', data: [...districts].reverse(), axisLabel: { fontSize: 11, color: '#374151' }, axisLine: { show: false }, axisTick: { show: false } },
      series: [{
        type: 'bar',
        data: [...rents].reverse(),
        barMaxWidth: 20,
        itemStyle: { color: '#1B4332', borderRadius: [0, 4, 4, 0] },
        emphasis: { itemStyle: { color: '#C8A951' } },
        cursor: 'pointer',
        label: {
          show: true,
          position: 'right',
          formatter: (p: { value: number }) => `AED ${fmtK(p.value)}`,
          fontSize: 10,
          color: '#374151'
        }
      }]
    });
  });
</script>

{#if data.length === 0}
  <div class="h-64 flex items-center justify-center text-gray-400 text-sm">No district data</div>
{:else}
  <div bind:this={chartEl} class="w-full" style="height: {Math.max(200, data.length * 36)}px"></div>
{/if}
