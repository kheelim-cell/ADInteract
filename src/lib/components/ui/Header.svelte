<script lang="ts">
  import { metadata } from '$lib/stores/db';

  let { lastUpdated = '' } = $props();

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
  <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-6">

    <!-- Left: Logo + brand -->
    <div class="flex items-center gap-4 min-w-0">
      <!-- Logo mark: Abu Dhabi emirate outline -->
      <div class="flex-shrink-0 flex items-center justify-center w-11 h-11 rounded-xl bg-white/8 border border-brand-500/30 shadow-inner">
        <svg class="h-7 w-7 text-brand-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" stroke-linecap="round">
          <!--
            Abu Dhabi emirate outline (clockwise from NW coast):
            - NW: where Gulf coast meets western Saudi border
            - N coast sweeps east (Gulf of Arabia)
            - Abu Dhabi city peninsula juts north (centre-north)
            - NE: short diagonal Dubai border
            - E/SE: Oman & Saudi border going south
            - S: long Saudi Arabia border going west
            - W: Saudi border going north back to coast
          -->
          <path d="
            M 1.5,10
            Q 5,7 9,6
            L 10.5,6
            L 12,3.5
            L 13.5,6
            Q 17,6 20,7
            L 22.5,9.5
            L 22,15.5
            L 19.5,21
            L 11.5,22.5
            L 4,20.5
            L 1.5,14
            Z
          "/>
        </svg>
      </div>

      <div class="min-w-0">
        <div class="flex items-center gap-2.5">
          <h1 class="text-[17px] font-extrabold text-brand-300 leading-none tracking-tight">ADInteract</h1>
          <!-- ADREC verified badge -->
          <span class="hidden sm:inline-flex items-center gap-1 rounded-full bg-brand-500/15 border border-brand-500/25 px-2 py-0.5 text-[10px] font-semibold text-brand-400 tracking-wide">
            <svg class="h-2.5 w-2.5" viewBox="0 0 24 24" fill="currentColor">
              <path fill-rule="evenodd" d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.491 4.491 0 01-3.497-1.307 4.491 4.491 0 01-1.307-3.497A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd"/>
            </svg>
            Powered by ADREC
          </span>
        </div>
        <p class="text-[10px] text-white/35 font-semibold tracking-widest uppercase mt-1">
          Abu Dhabi Property Transactions
        </p>
      </div>
    </div>

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
