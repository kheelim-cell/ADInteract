<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { updateFilter } from '$lib/stores/filters';
  import DashboardContent from '$lib/components/DashboardContent.svelte';

  let districtName = $derived(decodeURIComponent($page.params.district));

  onMount(() => {
    updateFilter({ district: districtName, project: null });
  });
</script>

<svelte:head>
  <title>{districtName} — ADInteract</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6">
  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-4">
    <a href="/" class="hover:text-brand-600 transition-colors">Overview</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="font-medium text-gray-900">{districtName}</span>
  </nav>

  <div class="flex items-start justify-between mb-2">
    <div>
      <h1 class="text-2xl font-bold text-navy">{districtName}</h1>
      <p class="text-sm text-gray-400 mt-0.5">District analytics</p>
    </div>
    <a
      href="/"
      class="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-brand-600 transition-colors bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-brand-300 shadow-sm"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      Back
    </a>
  </div>
</div>

<DashboardContent
  topAreasLabel="Top Projects by Volume"
  topAreasClickable={false}
  useTopProjects={true}
/>
