<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { updateFilter } from '$lib/stores/filters';
  import DashboardContent from '$lib/components/DashboardContent.svelte';
  import ProjectHero from '$lib/components/project/ProjectHero.svelte';

  let projectName = $derived(decodeURIComponent($page.params.name));

  onMount(() => {
    updateFilter({ project: projectName, district: null });
  });
</script>

<svelte:head>
  <title>{projectName} — ADInteract</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6">
  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-4">
    <a href="{base}/" class="hover:text-brand-600 transition-colors">Overview</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="font-medium text-gray-900">{projectName}</span>
  </nav>

  <div class="flex items-start justify-between mb-5">
    <div>
      <h1 class="text-2xl font-bold text-navy">{projectName}</h1>
      <p class="text-sm text-gray-400 mt-0.5">Project analytics</p>
    </div>
    <a
      href="{base}/"
      class="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-brand-600 transition-colors bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-brand-300 shadow-sm"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      Back
    </a>
  </div>

  <!-- Identity strip: location, types, off-plan split, vs district benchmark -->
  <ProjectHero {projectName} />
</div>

<DashboardContent
  topAreasLabel="Top Districts by Volume"
  topAreasClickable={true}
  {projectName}
/>
