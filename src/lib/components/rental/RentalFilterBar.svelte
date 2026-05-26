<script lang="ts">
  import { rentalFilters, updateRentalFilter, resetRentalFilters } from '$lib/stores/rental_filters';
  import { rentalMetadata } from '$lib/stores/db';
  import { DEFAULT_RENTAL_FILTERS } from '$lib/db/rental_types';

  // District autocomplete
  let districtQuery = $state('');
  let districtOpen  = $state(false);
  let districtEl    = $state<HTMLDivElement>();

  // Project autocomplete
  let projectQuery = $state('');
  let projectOpen  = $state(false);
  let projectEl    = $state<HTMLDivElement>();

  $effect(() => {
    districtQuery = $rentalFilters.district ?? '';
    projectQuery  = $rentalFilters.project  ?? '';
  });

  let districtMatches = $derived(
    districtQuery.length >= 1
      ? ($rentalMetadata?.districts ?? [])
          .filter((d) => d.toLowerCase().includes(districtQuery.toLowerCase()))
          .slice(0, 8)
      : []
  );

  let projectMatches = $derived(
    projectQuery.length >= 1
      ? ($rentalMetadata?.projects ?? [])
          .filter((p) => p.toLowerCase().includes(projectQuery.toLowerCase()))
          .slice(0, 8)
      : []
  );

  function handleClickOutside(e: MouseEvent) {
    if (districtEl && !districtEl.contains(e.target as Node)) districtOpen = false;
    if (projectEl  && !projectEl.contains(e.target as Node))  projectOpen  = false;
  }

  $effect(() => {
    if (districtOpen || projectOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });

  function selectDistrict(d: string) {
    districtQuery = d;
    districtOpen  = false;
    updateRentalFilter({ district: d, community: null });
  }

  function clearDistrict() {
    districtQuery = '';
    updateRentalFilter({ district: null, community: null });
  }

  function selectProject(p: string) {
    projectQuery = p;
    projectOpen  = false;
    updateRentalFilter({ project: p });
  }

  function clearProject() {
    projectQuery = '';
    updateRentalFilter({ project: null });
  }

  let hasActiveFilters = $derived(
    $rentalFilters.district !== null ||
    $rentalFilters.project  !== null ||
    $rentalFilters.typology !== null ||
    $rentalFilters.layout   !== null ||
    $rentalFilters.rentType !== DEFAULT_RENTAL_FILTERS.rentType
  );

  const years = $derived($rentalMetadata?.years ?? []);
  const latestYear = $derived($rentalMetadata?.latestYear ?? null);
  const resolvedYear = $derived($rentalFilters.year ?? latestYear);

  const typologies = $derived(
    ($rentalMetadata?.typologies ?? []).filter(
      (t) => t !== 'All property types'
    )
  );

  const layouts = $derived(
    ($rentalMetadata?.layouts ?? []).filter((l) => l !== 'all beds')
  );

  function capLayout(l: string): string {
    return l.charAt(0).toUpperCase() + l.slice(1);
  }
</script>

<div class="sticky top-0 z-10 bg-white/98 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
  <div class="px-4 sm:px-6 py-3">

    <!-- Row 1: searches + year selector + typology + layout + rent type -->
    <div class="flex flex-wrap items-center gap-2">

      <!-- District search -->
      <div class="relative" bind:this={districtEl}>
        <div class="flex items-center rounded-xl border border-gray-200 bg-white px-3 py-2 gap-2 text-sm w-44 sm:w-52">
          <svg class="h-3.5 w-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z" />
          </svg>
          <input
            type="text"
            placeholder="District"
            bind:value={districtQuery}
            oninput={() => { districtOpen = districtQuery.length >= 1; }}
            onfocus={() => { if (districtQuery.length >= 1) districtOpen = true; }}
            class="flex-1 min-w-0 bg-transparent text-xs font-medium text-gray-700 placeholder-gray-400 outline-none"
          />
          {#if $rentalFilters.district}
            <button onclick={clearDistrict} class="text-gray-400 hover:text-gray-600">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          {/if}
        </div>
        {#if districtOpen && districtMatches.length > 0}
          <div class="absolute top-full left-0 z-30 mt-1 w-64 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
            {#each districtMatches as d}
              <button
                type="button"
                onclick={() => selectDistrict(d)}
                class="flex w-full items-center px-4 py-2.5 text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors text-left"
              >
                {d}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Project search -->
      <div class="relative" bind:this={projectEl}>
        <div class="flex items-center rounded-xl border border-gray-200 bg-white px-3 py-2 gap-2 text-sm w-44 sm:w-52">
          <svg class="h-3.5 w-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z" />
          </svg>
          <input
            type="text"
            placeholder="Project"
            bind:value={projectQuery}
            oninput={() => { projectOpen = projectQuery.length >= 1; }}
            onfocus={() => { if (projectQuery.length >= 1) projectOpen = true; }}
            class="flex-1 min-w-0 bg-transparent text-xs font-medium text-gray-700 placeholder-gray-400 outline-none"
          />
          {#if $rentalFilters.project}
            <button onclick={clearProject} class="text-gray-400 hover:text-gray-600">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          {/if}
        </div>
        {#if projectOpen && projectMatches.length > 0}
          <div class="absolute top-full left-0 z-30 mt-1 w-72 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
            {#each projectMatches as p}
              <button
                type="button"
                onclick={() => selectProject(p)}
                class="flex w-full items-center px-4 py-2.5 text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors text-left"
              >
                {p}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <div class="hidden sm:block h-5 w-px bg-gray-200"></div>

      <!-- Year pills -->
      {#if years.length > 0}
        <div class="inline-flex rounded-full border border-gray-200 bg-gray-50 p-0.5">
          {#each years as yr}
            <button
              type="button"
              onclick={() => updateRentalFilter({ year: yr })}
              class="rounded-full px-3 py-1 text-xs font-semibold transition-all whitespace-nowrap
                     {resolvedYear === yr
                       ? 'bg-brand-600 text-white shadow-sm'
                       : 'text-gray-900 hover:bg-white'}"
            >
              {yr}
            </button>
          {/each}
        </div>
      {/if}

      <div class="hidden sm:block h-5 w-px bg-gray-200"></div>

      <!-- Rent type pills -->
      <div class="inline-flex rounded-full border border-gray-200 bg-gray-50 p-0.5">
        {#each ['All types', 'New', 'Renew'] as rt}
          <button
            type="button"
            onclick={() => updateRentalFilter({ rentType: rt })}
            class="rounded-full px-3 py-1 text-xs font-semibold transition-all whitespace-nowrap
                   {$rentalFilters.rentType === rt
                     ? 'bg-brand-600 text-white shadow-sm'
                     : 'text-gray-900 hover:bg-white'}"
          >
            {rt}
          </button>
        {/each}
      </div>

      <!-- Typology selector -->
      {#if typologies.length > 0}
        <select
          value={$rentalFilters.typology ?? ''}
          onchange={(e) => updateRentalFilter({ typology: (e.currentTarget as HTMLSelectElement).value || null })}
          class="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 cursor-pointer"
        >
          <option value="">All types</option>
          {#each typologies as t}
            <option value={t}>{t}</option>
          {/each}
        </select>
      {/if}

      <!-- Layout selector -->
      {#if layouts.length > 0}
        <select
          value={$rentalFilters.layout ?? ''}
          onchange={(e) => updateRentalFilter({ layout: (e.currentTarget as HTMLSelectElement).value || null })}
          class="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 cursor-pointer"
        >
          <option value="">All beds</option>
          {#each layouts as l}
            <option value={l}>{capLayout(l)}</option>
          {/each}
        </select>
      {/if}

      <!-- Clear all -->
      {#if hasActiveFilters}
        <button
          type="button"
          onclick={resetRentalFilters}
          class="ml-auto inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Clear all
        </button>
      {/if}
    </div>

  </div>
</div>
