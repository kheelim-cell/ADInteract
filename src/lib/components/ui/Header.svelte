<script lang="ts">
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { metadata, rentalMetadata } from '$lib/stores/db';

  let { lastUpdated = '' } = $props();

  let isRentalPage = $derived($page.url.pathname.includes('/rental'));
  let hasRental    = $derived($rentalMetadata !== null);

  function formatUpdated(ts: string): string {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Dubai'
      }) + ' GST';
    } catch {
      return ts;
    }
  }

  function dataRange(min: string, max: string): string {
    const fmt = (d: string) => new Date(d).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
    return `${fmt(min)} – ${fmt(max)}`;
  }
</script>

<!-- Gold accent line at very top -->
<div class="h-0.5 w-full bg-gradient-to-r from-transparent via-brand-500 to-transparent"></div>

<header class="bg-gradient-to-b from-[#1e4d3a] to-navy border-b border-white/5">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3 sm:gap-6">

    <!-- Left: Logo + brand -->
    <div class="flex items-center gap-2 sm:gap-4 min-w-0">

      <!-- Skyline silhouette icon -->
      <div class="flex-shrink-0 flex items-center justify-center w-9 h-8 sm:w-12 sm:h-11 rounded-xl bg-white/8 border border-brand-500/30 shadow-inner">
        <svg class="w-7 h-5 sm:w-10 sm:h-8 text-brand-400" viewBox="0 0 80 40" fill="currentColor">
          <path d="
            M 0,38
            L 0,30 L 5,30 L 5,26 L 10,26 L 10,30
            L 11,30 L 11,25 Q 15.5,18 20,25 L 20,30
            L 21,30 L 21,21
            L 23,21 L 23,13 L 25,3 L 27,13 L 27,21
            L 29,21 L 29,17
            L 31,17 L 31,7 L 32,7 L 32,2 L 32.5,0 L 33,2 L 33,7 L 34,7 L 34,17
            L 35,17 L 35,21
            L 37,21 L 37,13 L 39.5,7 L 42,13 L 42,21
            L 44,21 L 44,16 L 47,13 L 50,16 L 50,21
            L 52,21 L 52,27 L 57,27 L 57,23 L 64,23 L 64,27 L 72,27 L 72,31 L 80,31
            L 80,38
            Z
          "/>
        </svg>
      </div>

      <!-- Text logo: AD bold + INTERACT light italic -->
      <div class="min-w-0">
        <div class="flex items-center gap-2.5">
          <h1 class="leading-none">
            <span class="text-[26px] font-extrabold text-brand-400 tracking-tight">AD</span><span class="text-[26px] font-light italic text-brand-400 tracking-tight">INTERACT</span>
          </h1>
          <!-- Data source badge — unofficial independent platform -->
          <span class="hidden sm:inline-flex items-center gap-1 rounded-full bg-white/8 border border-white/15 px-2 py-0.5 text-[10px] font-semibold text-white/40 tracking-wide">
            Data: ADREC
          </span>
        </div>
        <p class="text-[10px] text-white/35 font-semibold tracking-widest uppercase mt-1">
          Abu Dhabi Property Transactions
        </p>
      </div>
    </div>

    <!-- Centre: Sales / Rental nav tabs (always visible when rental data available) -->
    {#if hasRental}
      <nav class="flex items-center rounded-full bg-white/10 border border-white/25 p-0.5 sm:p-1 gap-0.5 sm:gap-1">
        <a
          href="{base}/"
          class="rounded-full px-3 sm:px-7 py-1.5 sm:py-2 text-xs sm:text-sm font-semibold sm:font-bold transition-colors whitespace-nowrap sm:tracking-wide
                 {!isRentalPage
                   ? 'bg-brand-500 text-white shadow-sm sm:shadow-md'
                   : 'text-white/60 hover:text-white hover:bg-white/10'}"
        >
          Sales
        </a>
        <a
          href="{base}/rental"
          class="rounded-full px-3 sm:px-7 py-1.5 sm:py-2 text-xs sm:text-sm font-semibold sm:font-bold transition-colors whitespace-nowrap sm:tracking-wide
                 {isRentalPage
                   ? 'bg-brand-500 text-white shadow-sm sm:shadow-md'
                   : 'text-white/60 hover:text-white hover:bg-white/10'}"
        >
          Rental
        </a>
      </nav>
    {/if}

    <!-- Right: dataset stats + last updated -->
    <div class="hidden md:flex flex-col items-end gap-1 flex-shrink-0">
      {#if $metadata}
        <div class="flex items-center gap-1.5 text-[11px] font-semibold text-white/60">
          <svg class="h-3.5 w-3.5 text-brand-500/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
          </svg>
          <span class="text-white/80">{$metadata.rowCount.toLocaleString()}</span> transactions
          {#if $metadata.dateRange?.min && $metadata.dateRange?.max}
            <span class="text-white/30">·</span>
            <span>{dataRange($metadata.dateRange.min, $metadata.dateRange.max)}</span>
          {/if}
        </div>
      {/if}
      {#if lastUpdated}
        <div class="flex items-center gap-1.5 text-white/30 text-[10px] font-medium">
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Updated {formatUpdated(lastUpdated)}
        </div>
      {/if}
    </div>

  </div>
</header>
