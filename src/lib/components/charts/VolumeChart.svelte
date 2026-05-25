<script lang="ts">
  import { onMount } from 'svelte';
  import * as echarts from 'echarts';
  import type { ChartDataPoint } from '$lib/db/types';

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
      const offPlan = data.map((d) => d.offPlanVolume);
      const ready = data.map((d) => d.readyVolume);

      chart.setOption({
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#fff',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#374151', fontSize: 12 },
          formatter(params: any) {
            const month = params[0].axisValue;
            let total = 0;
            let html = `<div class="font-medium mb-1">${month}</div>`;
            for (const p of params) {
              total += p.value;
              html += `<div class="flex items-center gap-2"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color}"></span>${p.seriesName}: <b>${p.value.toLocaleString()}</b></div>`;
            }
            html += `<div class="mt-1 pt-1 border-t border-gray-200 font-medium">Total: <b>${total.toLocaleString()}</b></div>`;
            return html;
          }
        },
        legend: {
          top: 0,
          right: 0,
          textStyle: { fontSize: 12, color: '#6b7280' }
        },
        grid: { left: 50, right: 20, top: 30, bottom: 30 },
        xAxis: {
          type: 'category',
          data: months,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#9ca3af', fontSize: 11, rotate: months.length > 18 ? 45 : 0 }
        },
        yAxis: {
          type: 'value',
          name: 'Transactions',
          nameTextStyle: { color: '#9ca3af', fontSize: 11 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#f3f4f6' } },
          axisLabel: { color: '#9ca3af', fontSize: 11 }
        },
        series: [
          {
            name: 'Off-plan',
            type: 'bar',
            stack: 'volume',
            data: offPlan,
            barMaxWidth: 28,
            itemStyle: {
              color: '#D4AF37',
              borderRadius: [0, 0, 0, 0]
            }
          },
          {
            name: 'Ready',
            type: 'bar',
            stack: 'volume',
            data: ready,
            barMaxWidth: 28,
            itemStyle: {
              color: '#0A1628',
              borderRadius: [3, 3, 0, 0]
            }
          }
        ]
      });
    }
  });
</script>

<div bind:this={chartEl} class="w-full h-72"></div>
