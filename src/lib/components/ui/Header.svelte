<script lang="ts">
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
</script>

<header class="bg-navy border-b border-navy-light/30">
  <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
    <!-- Brand -->
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2.5">
        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600/20 border border-brand-500/30">
          <svg class="h-4.5 w-4.5 text-brand-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <div>
          <h1 class="text-base font-bold text-brand-300 leading-none tracking-wide">ADInteract</h1>
          <p class="text-[10px] text-white/40 font-medium tracking-widest uppercase mt-0.5">Abu Dhabi Property Transactions</p>
        </div>
      </div>
    </div>

    <!-- Meta -->
    {#if lastUpdated}
      <div class="flex items-center gap-2 text-white/30 text-xs">
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Updated {formatUpdated(lastUpdated)}</span>
      </div>
    {/if}
  </div>
</header>
