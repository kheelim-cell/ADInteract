<script lang="ts">
  import { filters, resetFilters } from '$lib/stores/filters';
  import { DEFAULT_FILTERS } from '$lib/db/types';
  import { browser } from '$app/environment';
  import DistrictSearch from './DistrictSearch.svelte';
  import DateRangePicker from './DateRangePicker.svelte';
  import SaleTypeToggle from './SaleTypeToggle.svelte';
  import OtherFilters from './OtherFilters.svelte';
  import PropertyTypeFilter from './PropertyTypeFilter.svelte';
  import LayoutFilter from './LayoutFilter.svelte';
  import { m } from '$lib/paraglide/messages.js';

  // ── Share state ───────────────────────────────────────────────────
  let copied        = $state(false);
  let shareMenuOpen = $state(false);
  let shareEl       = $state<HTMLDivElement>();

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
    const msg = encodeURIComponent(m.filter_whatsapp_share_text({ url: currentUrl() }));
    window.open(`https://wa.me/?text=${msg}`, '_blank');
    shareMenuOpen = false;
  }

  // ── Derived ───────────────────────────────────────────────────────
  let hasActiveFilters = $derived(
    $filters.district      !== null ||
    $filters.project       !== null ||
    $filters.dateRange     !== DEFAULT_FILTERS.dateRange  ||
    $filters.saleType      !== DEFAULT_FILTERS.saleType   ||
    $filters.saleSequence  !== DEFAULT_FILTERS.saleSequence ||
    $filters.propertyTypes.length > 0 ||
    $filters.layouts.length > 0 ||
    $filters.areaSqftMin   !== null ||
    $filters.areaSqftMax   !== null
  );
</script>

<!-- ── Filter bar: sticky on sm+ only — on phones a ~200px sticky block eats a quarter of the viewport -->
<div class="relative sm:sticky sm:top-0 z-30 bg-white/98 backdrop-blur-md border-b border-gray-200/80 shadow-sm">
  <div class="px-4 sm:px-6 py-3">

    <!-- Row 1: search + toggles (side-by-side searches on mobile, wraps naturally on larger screens) -->
    <div class="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center">
      <DistrictSearch searchType="district" />
      <DistrictSearch searchType="project" />

      <div class="hidden sm:block h-5 w-px bg-gray-200"></div>

      <SaleTypeToggle />

      <div class="hidden sm:block h-5 w-px bg-gray-200"></div>

      <PropertyTypeFilter />
      <LayoutFilter />
      <OtherFilters />
    </div>

    <!-- Row 2: date range + clear + share (never wraps — pills scroll, actions pinned right) -->
    <div class="flex mt-2 items-center gap-2">
      <div class="flex-1 min-w-0">
        <DateRangePicker />
      </div>

      <div class="flex-shrink-0 flex items-center gap-1.5">
        {#if hasActiveFilters}
          <button
            type="button"
            onclick={resetFilters}
            title={m.filter_clear_all_title()}
            class="inline-flex items-center gap-1 rounded-full px-2 sm:px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200 transition-colors"
          >
            <svg class="h-3 w-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span class="hidden sm:inline whitespace-nowrap">{m.filter_clear_all()}</span>
          </button>
        {/if}

        <!-- Share button -->
        <div class="relative" bind:this={shareEl}>
          <button
            type="button"
            onclick={() => (shareMenuOpen = !shareMenuOpen)}
            title={m.filter_share_title()}
            class="inline-flex items-center gap-1.5 rounded-full px-2 sm:px-3 py-1.5 text-xs font-medium border transition-colors
                   {copied
                     ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                     : 'border-gray-200 bg-white text-gray-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50'}"
          >
            {#if copied}
              <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span class="hidden sm:inline">{m.filter_copied()}</span>
            {:else}
              <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
              </svg>
              <span class="hidden sm:inline">{m.filter_share()}</span>
            {/if}
          </button>

          {#if shareMenuOpen}
            <div class="absolute end-0 z-30 mt-1.5 w-52 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
              <button
                type="button"
                onclick={copyLink}
                class="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <svg class="h-4 w-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
                </svg>
                {m.filter_copy_link()}
              </button>
              <button
                type="button"
                onclick={shareWhatsApp}
                class="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors border-t border-gray-100"
              >
                <svg class="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="#25D366">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                {m.filter_share_whatsapp()}
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>

  </div>
</div>
