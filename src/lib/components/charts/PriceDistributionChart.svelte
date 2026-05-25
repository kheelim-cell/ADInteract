<script lang="ts">
  import { onMount } from 'svelte';
  import * as echarts from 'echarts';
  import type { PriceDistributionPoint } from '$lib/db/types';
  import { formatCurrencyShort } from '$lib/utils/format';

  let { data = [] as PriceDistributionPoint[] } = $props();
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
      const layouts = data.map((d) => d.layout);
      // ECharts boxplot data format: [min, Q1, median, Q3, max]
      const boxData = data.map((d) => [d.min, d.q1, d.median, d.q3, d.max]);

      chart.setOption({
        textStyle: { fontFamily: 'Manrope, system-ui, sans-serif' },
        tooltip: {
          trigger: 'item',
          backgroundColor: '#fff',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#374151', fontSize: 12, fontFamily: 'Manrope, system-ui, sans-serif' },
          formatter(params: any) {
            const idx = params.dataIndex;
            const item = data[idx];
            if (!item) return '';
            return `<div class="font-medium mb-1">${item.layout}</div>
                    <div>Max: <b>${formatCurrencyShort(item.max)}</b></div>
                    <div>Q3: <b>${formatCurrencyShort(item.q3)}</b></div>
                    <div>Median: <b>${formatCurrencyShort(item.median)}</b></div>
                    <div>Q1: <b>${formatCurrencyShort(item.q1)}</b></div>
                    <div>Min: <b>${formatCurrencyShort(item.min)}</b></div>
                    <div class="mt-1 text-gray-400">${item.count.toLocaleString()} transactions</div>`;
          }
        },
        grid: { left: 70, right: 30, top: 20, bottom: 40 },
        xAxis: {
          type: 'category',
          data: layouts,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#374151', fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          name: 'AED/sqft',
          nameTextStyle: { color: '#9ca3af', fontSize: 11 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#f3f4f6' } },
          axisLabel: {
            color: '#9ca3af',
            fontSize: 11,
            formatter: (v: number) => formatCurrencyShort(v)
          }
        },
        series: [
          {
            type: 'boxplot',
            data: boxData,
            itemStyle: {
              color: '#f6f3e8',
              borderColor: '#C8A951',
              borderWidth: 1.5
            },
            boxWidth: ['30%', '50%'],
            emphasis: {
              itemStyle: {
                color: '#faf0ca',
                borderColor: '#0A1628',
                borderWidth: 2
              }
            }
          }
        ]
      });
    }
  });
</script>

<div bind:this={chartEl} class="w-full h-72"></div>
