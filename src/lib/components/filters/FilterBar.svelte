<script lang="ts">
  import { filters, resetFilters, updateFilter } from '$lib/stores/filters';
  import { metadata } from '$lib/stores/db';
  import DistrictSearch from './DistrictSearch.svelte';
  import DateRangePicker from './DateRangePicker.svelte';
  import SaleTypeToggle from './SaleTypeToggle.svelte';
  import PropertyTypeFilter from './PropertyTypeFilter.svelte';
  import LayoutFilter from './LayoutFilter.svelte';
  import { DEFAULT_FILTERS } from '$lib/db/types';
  import { browser } from '$app/environment';

  // ── Share state ───────────────────────────────────────────────────
  let copied = $state(false);
  let shareMenuOpen = $state(false);
  let shareEl = $state<HTMLDivElement>();

  function handleShareClickOutside(e: MouseEvent) {
    if (shareEl && !shareEl.contains(e.target as Node)) shareMenuOpen = false;
  }

  $effect(() => {
    if (!browser) return;
    if (shareMenuOpen) {
      document.addEventListener('click', handleShareClickOutside);
      return () => document.removeEventListener('click', handleShareClickOutside);
    }
  });

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
    const msg = encodeURIComponent('Check out this Abu Dhabi property data view: ' + currentUrl());
    window.open(`https://wa.me/?text=${msg}`, '_blank');
    shareMenuOpen = false;
  }

  // ── Mobile bottom sheet state ─────────────────────────────────────
  let mobileFiltersOpen = $state(false);

  // Mobile inline autocomplete state
  let mobileDQuery = $state('');
  let mobileDOpen  = $state(false);
  let mobilePQuery = $state('');
  let mobilePOpen  = $state(false);

  // Body scroll lock when drawer is open
  $effect(() => {
    if (!browser || !mobileFiltersOpen) return;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  });

  // Reset autocomplete when drawer closes
  $effect(() => {
    if (!mobileFiltersOpen) {
      mobileDQuery = '';
      mobileDOpen  = false;
      mobilePQuery = '';
      mobilePOpen  = false;
    }
  });

  // District / project options
  let districtOptions = $derived($metadata?.districts ?? []);
  let projectOptions  = $derived($metadata?.projects  ?? []);

  let mobileDMatches = $derived(() => {
    const q = mobileDQuery.trim().toLowerCase();
    if (!q) return districtOptions.slice(0, 40);
    return districtOptions.filter((d) => d.toLowerCase().includes(q));
  });

  let mobilePMatches = $derived(() => {
    const q = mobilePQuery.trim().toLowerCase();
    if (q.length < 2) return [];
    return projectOptions.filter((p) => p.toLowerCase().includes(q));
  });

  function mobileSelectDistrict(d: string) {
    updateFilter({ district: d, project: null });
    mobileDQuery = '';
    mobileDOpen  = false;
  }

  function mobileSelectProject(p: string) {
    updateFilter({ project: p, district: null });
    mobilePQuery = '';
    mobilePOpen  = false;
  }

  // Inline options for mobile drawer (mirrors sub-components)
  const PROPERTY_OPTIONS = [
    { label: 'Apartment',                   value: 'apartment' },
    { label: 'Duplex',                       value: 'duplex' },
    { label: 'Townhouse / Attached Villa',   value: 'townhouse / attached villa' },
    { label: 'Villa',                        value: 'villa' },
    { label: 'Office',                       value: 'office' },
    { label: 'Retail',                       value: 'retail' },
  ];

  const LAYOUT_OPTIONS = [
    { label: 'Studio',  value: 'studio'  },
    { label: '1 Bed',   value: '1 bed'   },
    { label: '2 Beds',  value: '2 beds'  },
    { label: '3 Beds',  value: '3 beds'  },
    { label: '4 Beds',  value: '4 beds'  },
    { label: '5 Beds',  value: '5 beds'  },
    { label: '6+ Beds', value: '6+ beds' },
  ];

  function togglePropertyType(value: string) {
    const next = $filters.propertyTypes.includes(value)
      ? $filters.propertyTypes.filter((v) => v !== value)
      : [...$filters.propertyTypes, value];
    updateFilter({ propertyTypes: next });
  }

  function toggleLayout(value: string) {
    const next = $filters.layouts.includes(value)
      ? $filters.layouts.filter((v) => v !== value)
      : [...$filters.layouts, value];
    updateFilter({ layouts: next });
  }

  // ── Derived display values ────────────────────────────────────────
  let hasActiveFilters = $derived(
    $filters.district !== null ||
    $filters.project !== null ||
    $filters.dateRange !== DEFAULT_FILTERS.dateRange ||
    $filters.saleType !== DEFAULT_FILTERS.saleType ||
    $filters.propertyTypes.length > 0 ||
    $filters.layouts.length > 0
  );

  let activeFilterCount = $derived(
    ($filters.district !== null ? 1 : 0) +
    ($filters.project  !== null ? 1 : 0) +
    ($filters.dateRange !== DEFAULT_FILTERS.dateRange ? 1 : 0) +
    ($filters.saleType  !== DEFAULT_FILTERS.saleType  ? 1 : 0) +
    $filters.propertyTypes.length +
    $filters.layouts.length
  );

  let dateRangeLabel = $derived(() => {
    switch ($filters.dateRange) {
      case '1m':  return '1M';
      case '3m':  return '3M';
      case '6m':  return '6M';
      case '12m': return '12M';
      case 'ytd': return 'YTD';
      case '3y':  return '3Y';
      case 'custom': {
        const s = $filters.customDateStart;
        const e = $filters.customDateEnd;
        if (s && e) return `${s.slice(0, 7)} – ${e.slice(0, 7)}`;
        if (s) return `From ${s.slice(0, 7)}`;
        if (e) return `To ${e.slice(0, 7)}`;
        return 'Custom';
      }
      default: return String($filters.dateRange);
    }
  });

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
      tags.push({ label: pt, clear: () => updateFilter({ propertyTypes: $filters.propertyTypes.filter((p) => p !== pt) }) });
    }
    for (const l of $filters.layouts) {
      tags.push({ label: l, clear: () => updateFilter({ layouts: $filters.layouts.filter((x) => x !== l) }) });
    }
    return tags;
  });
</script>

<!-- ── Sticky filter bar ─────────────────────────────────────────── -->
<div class="sticky top-0 z-10 bg-white/98 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
  <div class="px-4 sm:px-6 py-3">

    <!-- Mobile compact bar (hidden sm+) -->
    <div class="flex sm:hidden items-center h-9 gap-2">
      <!-- Scrollable active-context chips -->
      <div class="flex-1 min-w-0 overflow-x-auto scrollbar-none">
        <div class="inline-flex items-center gap-1.5">
          <span class="inline-flex items-center rounded-full bg-brand-600 text-white px-2.5 py-1 text-xs font-semibold whitespace-nowrap">
            {dateRangeLabel()}
          </span>
          {#if $filters.district}
            <span class="inline-flex items-center rounded-full bg-brand-50 border border-brand-200 text-brand-700 px-2.5 py-1 text-xs font-medium whitespace-nowrap max-w-[130px] truncate">
              {$filters.district}
            </span>
          {/if}
          {#if $filters.project}
            <span class="inline-flex items-center rounded-full bg-brand-50 border border-brand-200 text-brand-700 px-2.5 py-1 text-xs font-medium whitespace-nowrap max-w-[130px] truncate">
              {$filters.project}
            </span>
          {/if}
          {#if $filters.saleType !== DEFAULT_FILTERS.saleType}
            <span class="inline-flex items-center rounded-full bg-brand-50 border border-brand-200 text-brand-700 px-2.5 py-1 text-xs font-medium whitespace-nowrap">
              {$filters.saleType === 'off-plan' ? 'Off-plan' : 'Ready'}
            </span>
          {/if}
          {#if $filters.propertyTypes.length > 0}
            <span class="inline-flex items-center rounded-full bg-brand-50 border border-brand-200 text-brand-700 px-2.5 py-1 text-xs font-medium whitespace-nowrap">
              {$filters.propertyTypes.length} type{$filters.propertyTypes.length > 1 ? 's' : ''}
            </span>
          {/if}
          {#if $filters.layouts.length > 0}
            <span class="inline-flex items-center rounded-full bg-brand-50 border border-brand-200 text-brand-700 px-2.5 py-1 text-xs font-medium whitespace-nowrap">
              {$filters.layouts.length} layout{$filters.layouts.length > 1 ? 's' : ''}
            </span>
          {/if}
        </div>
      </div>
      <!-- Filters pill -->
      <button
        type="button"
        onclick={() => (mobileFiltersOpen = true)}
        class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors
               {activeFilterCount > 0
                 ? 'border-brand-300 bg-brand-50 text-brand-700'
                 : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'}"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 4h18M7 12h10M11 20h2" />
        </svg>
        Filters
        {#if activeFilterCount > 0}
          <span class="inline-flex items-center justify-center rounded-full bg-brand-600 text-white text-[10px] font-bold min-w-[16px] h-4 px-1">
            {activeFilterCount}
          </span>
        {/if}
      </button>
    </div>

    <!-- Desktop Row 1 (hidden on mobile) -->
    <div class="hidden sm:flex flex-wrap items-center gap-2">
      <DistrictSearch searchType="district" />
      <DistrictSearch searchType="project" />

      <div class="h-5 w-px bg-gray-200"></div>

      <SaleTypeToggle />

      <div class="h-5 w-px bg-gray-200"></div>

      <PropertyTypeFilter />
      <LayoutFilter />
    </div>

    <!-- Desktop Row 2: date range + clear + share (hidden on mobile) -->
    <div class="hidden sm:flex mt-2 flex-wrap items-center gap-2">
      <DateRangePicker />

      <div class="ml-auto flex items-center gap-2">
        {#if hasActiveFilters}
          <button
            type="button"
            onclick={resetFilters}
            class="inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors"
          >
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Clear all
          </button>
        {/if}

        <!-- Share button -->
        <div class="relative" bind:this={shareEl}>
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
    </div>

    <!-- Desktop active filter tags (hidden on mobile) -->
    {#if activeFilterTags().length > 0}
      <div class="hidden sm:flex mt-2 pt-2 border-t border-gray-100 flex-wrap items-center gap-1.5">
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

<!-- ── Mobile bottom sheet (outside sticky, sm:hidden) ───────────── -->
{#if mobileFiltersOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-40 bg-black/40 sm:hidden"
    onclick={() => (mobileFiltersOpen = false)}
    aria-hidden="true"
  ></div>

  <!-- Panel -->
  <div
    class="fixed bottom-0 left-0 right-0 z-50 sm:hidden rounded-t-2xl bg-white shadow-2xl flex flex-col"
    style="max-height: 88vh"
  >
    <!-- Header -->
    <div class="relative flex-shrink-0 flex items-center justify-between px-4 pt-5 pb-3 border-b border-gray-100">
      <div class="absolute top-2 left-1/2 -translate-x-1/2 w-8 h-1 rounded-full bg-gray-200"></div>
      <h2 class="text-sm font-semibold text-gray-900">Filters</h2>
      <button
        type="button"
        onclick={() => (mobileFiltersOpen = false)}
        class="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
        aria-label="Close filters"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-5">

      <!-- Date Range -->
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2">Date Range</p>
        <DateRangePicker />
      </div>

      <!-- Sale Type -->
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2">Sale Type</p>
        <SaleTypeToggle />
      </div>

      <!-- District -->
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2">District</p>
        {#if $filters.district}
          <div class="flex items-center justify-between rounded-xl border border-brand-200 bg-brand-50 px-3 py-2.5">
            <span class="text-xs font-medium text-brand-700 truncate">{$filters.district}</span>
            <button
              type="button"
              onclick={() => updateFilter({ district: null })}
              class="ml-2 flex-shrink-0 rounded-full p-1 text-brand-400 hover:bg-brand-100 hover:text-brand-600 transition-colors"
              aria-label="Clear district"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {:else}
          <div class="flex items-center rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 gap-2">
            <svg class="h-3.5 w-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              bind:value={mobileDQuery}
              oninput={() => { mobileDOpen = true; }}
              onfocus={() => { mobileDOpen = true; }}
              placeholder="Search district..."
              class="flex-1 bg-transparent text-xs text-gray-900 placeholder-gray-400 focus:outline-none"
            />
            {#if mobileDQuery}
              <button
                type="button"
                onclick={() => { mobileDQuery = ''; mobileDOpen = false; }}
                class="flex-shrink-0 text-gray-300 hover:text-gray-500"
                aria-label="Clear"
              >
                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            {/if}
          </div>
          {#if mobileDOpen && mobileDMatches().length > 0}
            <div class="mt-1 rounded-xl border border-gray-200 bg-white overflow-hidden max-h-44 overflow-y-auto shadow-sm">
              {#each mobileDMatches() as d}
                <button
                  type="button"
                  onclick={() => mobileSelectDistrict(d)}
                  class="flex w-full items-center gap-2 px-3 py-2.5 text-xs text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors border-b border-gray-50 last:border-0 text-left"
                >
                  <svg class="h-3 w-3 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {d}
                </button>
              {/each}
            </div>
          {/if}
        {/if}
      </div>

      <!-- Project -->
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-2">Project</p>
        {#if $filters.project}
          <div class="flex items-center justify-between rounded-xl border border-brand-200 bg-brand-50 px-3 py-2.5">
            <span class="text-xs font-medium text-brand-700 truncate">{$filters.project}</span>
            <button
              type="button"
              onclick={() => updateFilter({ project: null })}
              class="ml-2 flex-shrink-0 rounded-full p-1 text-brand-400 hover:bg-brand-100 hover:text-brand-600 transition-colors"
              aria-label="Clear project"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        {:else}
          <div class="flex items-center rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 gap-2">
            <svg class="h-3.5 w-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              bind:value={mobilePQuery}
              oninput={() => { mobilePOpen = mobilePQuery.length >= 2; }}
              placeholder="Type 2+ chars to search projects..."
              class="flex-1 bg-transparent text-xs text-gray-900 placeholder-gray-400 focus:outline-none"
            />
            {#if mobilePQuery}
              <button
                type="button"
                onclick={() => { mobilePQuery = ''; mobilePOpen = false; }}
                class="flex-shrink-0 text-gray-300 hover:text-gray-500"
                aria-label="Clear"
              >
                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            {/if}
          </div>
          {#if mobilePQuery.length > 0 && mobilePQuery.length < 2}
            <p class="mt-1.5 text-xs text-gray-400 text-center">Type at least 2 characters</p>
          {:else if mobilePOpen && mobilePMatches().length > 0}
            <div class="mt-1 rounded-xl border border-gray-200 bg-white overflow-hidden max-h-44 overflow-y-auto shadow-sm">
              {#each mobilePMatches() as p}
                <button
                  type="button"
                  onclick={() => mobileSelectProject(p)}
                  class="flex w-full items-center gap-2 px-3 py-2.5 text-xs text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors border-b border-gray-50 last:border-0 text-left"
                >
                  <svg class="h-3 w-3 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                  </svg>
                  {p}
                </button>
              {/each}
            </div>
          {:else if mobilePOpen && mobilePQuery.length >= 2 && mobilePMatches().length === 0}
            <p class="mt-1.5 text-xs text-gray-400 text-center">No results for "{mobilePQuery.trim()}"</p>
          {/if}
        {/if}
      </div>

      <!-- Property Type -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Property Type</p>
          {#if $filters.propertyTypes.length > 0}
            <button
              type="button"
              onclick={() => updateFilter({ propertyTypes: [] })}
              class="text-xs text-brand-600 hover:text-brand-800 font-medium transition-colors"
            >
              Clear
            </button>
          {/if}
        </div>
        <div class="flex flex-wrap gap-1.5">
          {#each PROPERTY_OPTIONS as opt}
            <button
              type="button"
              onclick={() => togglePropertyType(opt.value)}
              class="rounded-full px-3 py-1.5 text-xs font-medium border transition-all
                     {$filters.propertyTypes.includes(opt.value)
                       ? 'bg-brand-600 text-white border-brand-600'
                       : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300 hover:bg-gray-50'}"
            >
              {opt.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Layout -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Layout</p>
          {#if $filters.layouts.length > 0}
            <button
              type="button"
              onclick={() => updateFilter({ layouts: [] })}
              class="text-xs text-brand-600 hover:text-brand-800 font-medium transition-colors"
            >
              Clear
            </button>
          {/if}
        </div>
        <div class="flex flex-wrap gap-1.5">
          {#each LAYOUT_OPTIONS as opt}
            <button
              type="button"
              onclick={() => toggleLayout(opt.value)}
              class="rounded-full px-3 py-1.5 text-xs font-medium border transition-all
                     {$filters.layouts.includes(opt.value)
                       ? 'bg-brand-600 text-white border-brand-600'
                       : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300 hover:bg-gray-50'}"
            >
              {opt.label}
            </button>
          {/each}
        </div>
      </div>

    </div>

    <!-- Footer -->
    <div class="flex-shrink-0 px-4 py-3 border-t border-gray-100 flex items-center gap-2">
      {#if hasActiveFilters}
        <button
          type="button"
          onclick={() => { resetFilters(); mobileFiltersOpen = false; }}
          class="inline-flex items-center gap-1 rounded-full px-4 py-2 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Clear all
        </button>
      {/if}
      <!-- Share / copy link -->
      <button
        type="button"
        onclick={copyLink}
        class="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-xs font-medium border transition-colors
               {copied
                 ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                 : 'border-gray-200 bg-white text-gray-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50'}"
        aria-label="Copy link"
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
      <button
        type="button"
        onclick={() => (mobileFiltersOpen = false)}
        class="ml-auto rounded-full px-5 py-2 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
      >
        Done
      </button>
    </div>
  </div>
{/if}
