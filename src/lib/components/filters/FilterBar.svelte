<script lang="ts">
  import { filters, resetFilters, updateFilter } from '$lib/stores/filters';
  import { metadata } from '$lib/stores/db';
  import DistrictSearch from './DistrictSearch.svelte';
  import DateRangePicker from './DateRangePicker.svelte';
  import SaleTypeToggle from './SaleTypeToggle.svelte';
  import PropertyTypeFilter from './PropertyTypeFilter.svelte';
  import LayoutFilter from './LayoutFilter.svelte';
  import { DEFAULT_FILTERS } from '$lib/db/types';

  let hasActiveFilters = $derived(
    $filters.district !== null ||
    $filters.project !== null ||
    $filters.dateRange !== DEFAULT_FILTERS.dateRange ||
    $filters.saleType !== DEFAULT_FILTERS.saleType ||
    $filters.propertyTypes.length > 0 ||
    $filters.layouts.length > 0
  );

  let activeFilterTags = $derived(() => {
    const tags: { label: string; clear: () => void }[] = [];
    if ($filters.district) {
      tags.push({ label: $filters.district, clear: () => updateFilter({ district: null }) });
    }
    if ($filters.project) {
      tags.push({ label: $filters.project, clear: () => updateFilter({ project: null }) });
    }
    if ($filters.saleType !== 'all') {
      tags.push({
        label: $filters.saleType === 'off-plan' ? 'Off-plan' : 'Ready',
        clear: () => updateFilter({ saleType: 'all' })
      });
    }
    for (const pt of $filters.propertyTypes) {
      tags.push({ label: pt, clear: () => {
        updateFilter({ propertyTypes: $filters.propertyTypes.filter(p => p !== pt) });
      }});
    }
    for (const l of $filters.layouts) {
      tags.push({ label: l, clear: () => {
        updateFilter({ layouts: $filters.layouts.filter(x => x !== l) });
      }});
    }
    return tags;
  });
</script>

<div class="sticky top-0 z-10 bg-white/98 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
  <div class="px-4 sm:px-6 py-3">
    <!-- Single row: all filters -->
    <div class="flex flex-wrap items-center gap-2">
      <DistrictSearch searchType="district" />

      <div class="h-5 w-px bg-gray-200"></div>

      <SaleTypeToggle />

      <div class="h-5 w-px bg-gray-200"></div>

      <PropertyTypeFilter />
      <LayoutFilter />

      <div class="h-5 w-px bg-gray-200"></div>

      <DateRangePicker />

      {#if hasActiveFilters}
        <button
          type="button"
          onclick={resetFilters}
          class="ml-auto inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Clear all
        </button>
      {/if}
    </div>

    <!-- Active filter tags -->
    {#if activeFilterTags().length > 0}
      <div class="mt-2 pt-2 border-t border-gray-100 flex flex-wrap items-center gap-1.5">
        <span class="text-[10px] font-medium uppercase tracking-wider text-gray-400 mr-1">Active:</span>
        {#each activeFilterTags() as tag}
          <span class="inline-flex items-center gap-1 rounded-full bg-brand-50 border border-brand-200 px-2.5 py-1 text-xs font-medium text-brand-700">
            {tag.label}
            <button
              type="button"
              onclick={tag.clear}
              class="rounded-full p-0.5 text-brand-400 hover:bg-brand-100 hover:text-brand-600 transition-colors"
              aria-label="Remove {tag.label}"
            >
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </span>
        {/each}
      </div>
    {/if}
  </div>
</div>
