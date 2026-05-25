<script lang="ts">
  let { lastUpdated = '' } = $props();
</script>

<header class="flex items-center justify-between bg-white border-b border-gray-200 px-6 py-3">
  <div class="flex items-center gap-3">
    <div class="flex items-center gap-2">
      <svg class="h-7 w-7 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <h1 class="text-xl font-bold text-brand-700 tracking-tight">ADInteract</h1>
    </div>
    <span class="hidden sm:inline text-sm text-gray-400">|</span>
    <span class="hidden sm:inline text-sm text-gray-500">Abu Dhabi Property Transactions</span>
  </div>
  {#if lastUpdated}
    <div class="text-xs text-gray-400 whitespace-nowrap">
      Last updated: {lastUpdated}
    </div>
  {/if}
</header>
