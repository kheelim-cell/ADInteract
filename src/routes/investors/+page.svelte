<script lang="ts">
  import { dbReady, rentalMetadata } from '$lib/stores/db';
  import InvestorContent from '$lib/components/investors/InvestorContent.svelte';
</script>

<svelte:head>
  <title>Investor Intelligence — ADInteract</title>
  <meta name="description" content="Abu Dhabi property investment insights: top-performing districts and projects by price growth, rental yield rankings, and annual rent benchmarks from ADREC data." />
</svelte:head>

{#if !$dbReady}
  <!-- DB still initialising (handled by layout, but belt-and-braces guard) -->
  <div class="flex flex-col items-center justify-center min-h-[50vh] gap-4">
    <svg class="h-12 w-12 text-emerald-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
    </svg>
    <p class="text-gray-500 text-sm">Loading investor data…</p>
  </div>
{:else}
  <InvestorContent />
{/if}
