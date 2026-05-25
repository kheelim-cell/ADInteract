<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';

  let showCustom = $state(false);
  let customStart = $state($filters.customDateStart || '');
  let customEnd = $state($filters.customDateEnd || '');

  const presets = [
    { label: '1M',  value: '1m'  as const },
    { label: '3M',  value: '3m'  as const },
    { label: '6M',  value: '6m'  as const },
    { label: '12M', value: '12m' as const },
    { label: 'YTD', value: 'ytd' as const },
    { label: '3Y',  value: '3y'  as const }
  ];

  function selectPreset(value: '1m' | '3m' | '6m' | '12m' | 'ytd' | '3y') {
    showCustom = false;
    updateFilter({ dateRange: value, customDateStart: null, customDateEnd: null });
  }

  function toggleCustom() {
    showCustom = !showCustom;
    if (showCustom) {
      updateFilter({ dateRange: 'custom' });
    } else {
      updateFilter({ dateRange: '12m', customDateStart: null, customDateEnd: null });
    }
  }

  function applyCustom() {
    updateFilter({
      dateRange: 'custom',
      customDateStart: customStart || null,
      customDateEnd: customEnd || null
    });
  }
</script>

<div class="flex flex-col sm:flex-row sm:items-center gap-2">
  <!-- Preset pill — horizontally scrollable on mobile so it never wraps -->
  <div class="overflow-x-auto scrollbar-none -mx-4 sm:mx-0 px-4 sm:px-0">
    <div class="inline-flex rounded-full border border-gray-200 bg-gray-50 p-0.5 min-w-max">
      {#each presets as preset}
        <button
          type="button"
          onclick={() => selectPreset(preset.value)}
          class="rounded-full px-3 py-1 text-xs font-semibold transition-all whitespace-nowrap
                 {$filters.dateRange === preset.value
                   ? 'bg-brand-600 text-white shadow-sm'
                   : 'text-gray-900 hover:text-gray-900 hover:bg-white'}"
        >
          {preset.label}
        </button>
      {/each}
      <button
        type="button"
        onclick={toggleCustom}
        class="rounded-full px-3 py-1 text-xs font-semibold transition-all inline-flex items-center gap-1 whitespace-nowrap
               {$filters.dateRange === 'custom'
                 ? 'bg-brand-600 text-white shadow-sm'
                 : 'text-gray-900 hover:text-gray-900 hover:bg-white'}"
      >
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        Custom
      </button>
    </div>
  </div>

  {#if showCustom || $filters.dateRange === 'custom'}
    <div class="flex items-center gap-2">
      <input
        type="date"
        bind:value={customStart}
        onchange={applyCustom}
        class="rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 w-full sm:w-auto"
      />
      <span class="text-xs text-gray-400 flex-shrink-0">to</span>
      <input
        type="date"
        bind:value={customEnd}
        onchange={applyCustom}
        class="rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 w-full sm:w-auto"
      />
    </div>
  {/if}
</div>
