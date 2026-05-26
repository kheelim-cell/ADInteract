<script lang="ts">
  import RentalStatCard from './RentalStatCard.svelte';
  import type { RentalStatsResult } from '$lib/db/rental_types';

  let { stats }: { stats: RentalStatsResult } = $props();

  function fmt(n: number): string {
    if (n >= 1_000_000) return `AED ${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000)     return `AED ${Math.round(n).toLocaleString('en-US')}`;
    return `AED ${n.toLocaleString('en-US')}`;
  }
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
    sub="25th percentile"
  />
  <RentalStatCard
    label="Median Annual Rent"
    value={fmt(stats.medianRent)}
    sub="50th percentile"
  />
  <RentalStatCard
    label="Upper Band (75th %ile)"
    value={fmt(stats.upperRent)}
    sub="75th percentile"
  />
</div>
