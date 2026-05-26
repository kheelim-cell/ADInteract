<script lang="ts">
  import RentalStatCard from './RentalStatCard.svelte';
  import type { RentalStatsResult } from '$lib/db/rental_types';

  let { stats }: { stats: RentalStatsResult } = $props();

  function fmt(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n).toLocaleString('en-US')}`;
    return `AED ${n.toLocaleString('en-US')}`;
  }

  let compLabel = $derived(`vs. ${stats.prevYear}`);
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
  <RentalStatCard
    label="Projects Tracked"
    value={stats.projectCount.toLocaleString('en-US')}
    sub="in selected filters"
  />
  <RentalStatCard
    label="Lower Band (25th %ile)"
    value={fmt(stats.lowerRent)}
    currentRaw={stats.lowerRent}
    previousRaw={stats.prevLowerRent ?? 0}
    comparisonLabel={compLabel}
  />
  <RentalStatCard
    label="Median Annual Rent"
    value={fmt(stats.medianRent)}
    currentRaw={stats.medianRent}
    previousRaw={stats.prevMedianRent ?? 0}
    comparisonLabel={compLabel}
  />
  <RentalStatCard
    label="Upper Band (75th %ile)"
    value={fmt(stats.upperRent)}
    currentRaw={stats.upperRent}
    previousRaw={stats.prevUpperRent ?? 0}
    comparisonLabel={compLabel}
  />
</div>
