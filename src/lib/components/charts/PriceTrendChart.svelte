<script lang="ts">
  import { onMount } from 'svelte';
  import * as echarts from 'echarts';
  import type { ChartDataPoint } from '$lib/db/types';
  import { formatCurrencyShort } from '$lib/utils/format';

  let { data = [] as ChartDataPoint[] } = $props();
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
      const months = data.map((d) => d.month);
      const prices = data.map((d) => d.medianPrice);
      const rates = data.map((d) => d.medianRate);

      chart.setOption({
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#fff',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#374151', fontSize: 12 },
          formatter(params: any) {
            const month = params[0].axisValue;
            let html = `<div class="font-medium mb-1">${month}</div>`;
            for (const p of params) {
              const color = p.color;
              const name = p.seriesName;
              const val =
                name === 'Median Price'
                  ? formatCurrencyShort(p.value) + ' AED'
                  : formatCurrencyShort(p.value) + ' AED/sqft';
              html += `<div class="flex items-center gap-2"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color}"></span>${name}: <b>${val}</b></div>`;
            }
            return html;
          }
        },
        legend: {
          top: 0,
          right: 0,
          textStyle: { fontSize: 12, color: '#6b7280' }
        },
        grid: { left: 60, right: 60, top: 50, bottom: 30 },
        xAxis: {
          type: 'category',
          data: months,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#9ca3af', fontSize: 11, rotate: months.length > 18 ? 45 : 0 }
        },
        yAxis: [
          {
            type: 'value',
            name: 'Price (AED)',
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
          {
            type: 'value',
            name: 'AED/sqft',
            nameTextStyle: { color: '#9ca3af', fontSize: 11 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: {
              color: '#9ca3af',
              fontSize: 11,
              formatter: (v: number) => formatCurrencyShort(v)
            }
          }
        ],
        series: [
          {
            name: 'Median Price',
            type: 'line',
            data: prices,
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
            lineStyle: { width: 2.5, color: '#0c93e9' },
            itemStyle: { color: '#0c93e9' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(12,147,233,0.15)' },
                { offset: 1, color: 'rgba(12,147,233,0.01)' }
              ])
            }
          },
          {
            name: 'Median Rate/sqft',
            type: 'line',
            data: rates,
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
            lineStyle: { width: 2, color: '#f59e0b', type: 'dashed' },
            itemStyle: { color: '#f59e0b' }
          }
        ]
      });
    }
  });
</script>

<div bind:this={chartEl} class="w-full h-72"></div>
