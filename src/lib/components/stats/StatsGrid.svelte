<script lang="ts">
  import type { StatsResult } from '$lib/db/types';
  import { formatCurrency, formatNumber, formatRate, formatCurrencyShort } from '$lib/utils/format';
  import StatCard from './StatCard.svelte';
  import { m } from '$lib/paraglide/messages.js';

  let { stats }: { stats: StatsResult } = $props();
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
  <StatCard
    label={m.stat_label_volume()}
    value={formatNumber(stats.totalVolume)}
    currentRaw={stats.totalVolume}
    previousRaw={stats.prevTotalVolume}
    previousValue={stats.prevTotalVolume}
  />
  <StatCard
    label={m.stat_label_median_price()}
    value={formatCurrency(stats.medianPrice)}
    currentRaw={stats.medianPrice}
    previousRaw={stats.prevMedianPrice}
    previousValue={stats.prevMedianPrice}
  />
  <StatCard
    label={m.stat_label_median_rate()}
    value={formatRate(stats.medianRatePerSqft)}
    currentRaw={stats.medianRatePerSqft}
    previousRaw={stats.prevMedianRatePerSqft}
    previousValue={stats.prevMedianRatePerSqft}
  />
  <StatCard
    label={m.stat_label_total_value()}
    value={formatCurrencyShort(stats.totalValue) + ' AED'}
    currentRaw={stats.totalValue}
    previousRaw={stats.prevTotalValue}
    previousValue={stats.prevTotalValue}
  />
</div>
