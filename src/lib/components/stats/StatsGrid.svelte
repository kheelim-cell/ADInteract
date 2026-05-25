<script lang="ts">
  import type { StatsResult } from '$lib/db/types';
  import { formatCurrency, formatNumber, formatRate, formatCurrencyShort } from '$lib/utils/format';
  import StatCard from './StatCard.svelte';

  let { stats }: { stats: StatsResult } = $props();
</script>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  <StatCard
    label="Transaction Volume"
    value={formatNumber(stats.totalVolume)}
    currentRaw={stats.totalVolume}
    previousRaw={stats.prevTotalVolume}
    previousValue={stats.prevTotalVolume}
  />
  <StatCard
    label="Median Price"
    value={formatCurrency(stats.medianPrice)}
    currentRaw={stats.medianPrice}
    previousRaw={stats.prevMedianPrice}
    previousValue={stats.prevMedianPrice}
  />
  <StatCard
    label="Median Rate"
    value={formatRate(stats.medianRatePerSqft)}
    currentRaw={stats.medianRatePerSqft}
    previousRaw={stats.prevMedianRatePerSqft}
    previousValue={stats.prevMedianRatePerSqft}
  />
  <StatCard
    label="Total Value"
    value={formatCurrencyShort(stats.totalValue) + ' AED'}
    currentRaw={stats.totalValue}
    previousRaw={stats.prevTotalValue}
    previousValue={stats.prevTotalValue}
  />
</div>
