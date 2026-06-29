<script lang="ts">
  import RentalStatCard from './RentalStatCard.svelte';
  import type { RentalStatsResult } from '$lib/db/rental_types';
  import { m } from '$lib/paraglide/messages.js';

  let { stats }: { stats: RentalStatsResult } = $props();

  function fmt(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n).toLocaleString('en-US')}`;
    return `AED ${n.toLocaleString('en-US')}`;
  }

  let compLabel = $derived(m.rental_stat_vs_year({ year: String(stats.prevYear) }));
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
  <RentalStatCard
    label={m.rental_stat_projects_tracked()}
    value={stats.projectCount.toLocaleString('en-US')}
    sub={m.rental_stat_in_selected_filters()}
  />
  <RentalStatCard
    label={m.rental_stat_lower_band()}
    value={fmt(stats.lowerRent)}
    currentRaw={stats.lowerRent}
    previousRaw={stats.prevLowerRent ?? 0}
    comparisonLabel={compLabel}
  />
  <RentalStatCard
    label={m.rental_stat_median_annual_rent()}
    value={fmt(stats.medianRent)}
    currentRaw={stats.medianRent}
    previousRaw={stats.prevMedianRent ?? 0}
    comparisonLabel={compLabel}
  />
  <RentalStatCard
    label={m.rental_stat_upper_band()}
    value={fmt(stats.upperRent)}
    currentRaw={stats.upperRent}
    previousRaw={stats.prevUpperRent ?? 0}
    comparisonLabel={compLabel}
  />
</div>
