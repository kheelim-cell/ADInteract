<script lang="ts">
  import { rentalFilters, updateRentalFilter, resetRentalFilters } from '$lib/stores/rental_filters';
  import { rentalMetadata } from '$lib/stores/db';
  import { DEFAULT_RENTAL_FILTERS } from '$lib/db/rental_types';
  import { browser } from '$app/environment';

  // District autocomplete
  let districtQuery = $state('');
  let districtOpen  = $state(false);
  let districtEl    = $state<HTMLDivElement>();

  // Project autocomplete
  let projectQuery = $state('');
  let projectOpen  = $state(false);
  let projectEl    = $state<HTMLDivElement>();

  // Share
  let copied        = $state(false);
  let shareMenuOpen = $state(false);
  let shareEl       = $state<HTMLDivElement>();

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
    if (districtEl && !districtEl.contains(e.target as Node)) districtOpen  = false;
    if (projectEl  && !projectEl.contains(e.target as Node))  projectOpen   = false;
    if (shareEl    && !shareEl.contains(e.target as Node))    shareMenuOpen = false;
  }

  $effect(() => {
    if (districtOpen || projectOpen || shareMenuOpen) {
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

  function currentUrl(): string {
    return typeof window !== 'undefined' ? window.location.href : '';
  }

  async function copyLink() {
    await navigator.clipboard.writeText(currentUrl());
    copied = true;
    shareMenuOpen = false;
    setTimeout(() => (copied = false), 2000);
  }

  function shareWhatsApp() {
    const msg = encodeURIComponent('Check out this Abu Dhabi rental data view: ' + currentUrl());
    window.open(`https://wa.me/?text=${msg}`, '_blank');
    shareMenuOpen = false;
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

      <!-- Share button — far right -->
      <div class="relative ml-auto" bind:this={shareEl}>
        <button
          type="button"
          onclick={() => (shareMenuOpen = !shareMenuOpen)}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-colors
                 {copied
                   ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                   : 'border-gray-200 bg-white text-gray-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50'}"
        >
          {#if copied}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Copied!
          {:else}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
            </svg>
            Share
          {/if}
        </button>

        {#if shareMenuOpen}
          <div class="absolute right-0 z-30 mt-1.5 w-52 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
            <button
              type="button"
              onclick={copyLink}
              class="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <svg class="h-4 w-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
              </svg>
              Copy link
            </button>
            <button
              type="button"
              onclick={shareWhatsApp}
              class="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors border-t border-gray-100"
            >
              <svg class="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="#25D366">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              Share on WhatsApp
            </button>
          </div>
        {/if}
      </div>

    </div>

    <!-- Row 2: year pills left-aligned + Clear all far right -->
    {#if years.length > 0}
      <div class="flex items-center gap-1 mt-2">
        {#each years as yr}
          <button
            type="button"
            onclick={() => updateRentalFilter({ year: yr })}
            class="rounded-full px-3 py-1 text-xs font-semibold border transition-all whitespace-nowrap
                   {resolvedYear === yr
                     ? 'bg-brand-600 border-brand-600 text-white shadow-sm'
                     : 'border-gray-200 bg-gray-50 text-gray-900 hover:bg-white'}"
          >
            {yr}
          </button>
        {/each}

        {#if hasActiveFilters}
          <button
            type="button"
            onclick={resetRentalFilters}
            class="ml-auto inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors whitespace-nowrap"
          >
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Clear all
          </button>
        {/if}
      </div>
    {/if}

  </div>
</div>
