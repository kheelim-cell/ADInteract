<script lang="ts">
  import { onMount } from 'svelte';
  import * as echarts from 'echarts';
  import type { DistrictSummary } from '$lib/db/types';

  let { data = [] as DistrictSummary[] } = $props();
  let chartEl = $state<HTMLDivElement>();
  let chart: echarts.ECharts | undefined;

  onMount(() => {
    if (chartEl) {
      chart = echarts.init(chartEl);
      const handleResize = () => chart?.resize();
      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
        chart?.dispose();
      };
    }
  });

  $effect(() => {
    if (chart && data?.length) {
      const sorted = [...data].sort((a, b) => a.volume - b.volume);
      const districts = sorted.map((d) => d.district);
      const volumes = sorted.map((d) => d.volume);

      const chartHeight = Math.max(280, sorted.length * 32);
      if (chartEl) {
        chartEl.style.height = chartHeight + 'px';
        chart.resize();
      }

      chart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: '#fff',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#374151', fontSize: 12 },
          formatter(params: any) {
            const p = params[0];
            const item = sorted.find((d) => d.district === p.name);
            if (!item) return '';
            return `<div class="font-medium">${p.name}</div>
                    <div>Volume: <b>${item.volume.toLocaleString()}</b></div>
                    <div>Median Price: <b>${item.medianPrice.toLocaleString()} AED</b></div>
                    <div>Median Rate: <b>${item.medianRate.toLocaleString()} AED/sqft</b></div>`;
          }
        },
        grid: { left: 140, right: 40, top: 10, bottom: 10 },
        xAxis: {
          type: 'value',
          name: 'Transactions',
          nameTextStyle: { color: '#9ca3af', fontSize: 11 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#f3f4f6' } },
          axisLabel: { color: '#9ca3af', fontSize: 11 }
        },
        yAxis: {
          type: 'category',
          data: districts,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: {
            color: '#374151',
            fontSize: 11,
            width: 120,
            overflow: 'truncate'
          }
        },
        series: [
          {
            type: 'bar',
            data: volumes,
            barMaxWidth: 22,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#0A1628' },
                { offset: 1, color: '#C5A028' }
              ]),
              borderRadius: [0, 4, 4, 0]
            },
            label: {
              show: true,
              position: 'right',
              color: '#6b7280',
              fontSize: 11,
              formatter: (p: any) => p.value.toLocaleString()
            }
          }
        ]
      });
    }
  });
</script>

<div bind:this={chartEl} class="w-full h-72"></div>
