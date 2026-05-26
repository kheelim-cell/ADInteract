<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';
  import { browser } from '$app/environment';

  // ── Panel open/close ──────────────────────────────────────────────
  let open      = $state(false);
  let panelEl   = $state<HTMLDivElement>();

  // ── Draft state (committed only on Apply) ─────────────────────────
  let draftSequence = $state<'all' | 'primary' | 'secondary'>('all');
  let draftAreaMin  = $state('');
  let draftAreaMax  = $state('');

  function openPanel() {
    draftSequence = $filters.saleSequence;
    draftAreaMin  = $filters.areaSqftMin != null ? String($filters.areaSqftMin) : '';
    draftAreaMax  = $filters.areaSqftMax != null ? String($filters.areaSqftMax) : '';
    open = true;
  }

  function apply() {
    updateFilter({
      saleSequence: draftSequence,
      areaSqftMin:  draftAreaMin  ? Number(draftAreaMin)  : null,
      areaSqftMax:  draftAreaMax  ? Number(draftAreaMax)  : null
    });
    open = false;
  }

  function resetAll() {
    draftSequence = 'all';
    draftAreaMin  = '';
    draftAreaMax  = '';
    updateFilter({ saleSequence: 'all', areaSqftMin: null, areaSqftMax: null });
  }

  // ── Click outside to close ────────────────────────────────────────
  function handleClickOutside(e: MouseEvent) {
    if (panelEl && !panelEl.contains(e.target as Node)) open = false;
  }

  $effect(() => {
    if (!browser) return;
    if (open) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });

  // ── Active badge count ────────────────────────────────────────────
  let activeCount = $derived(
    ($filters.saleSequence !== 'all' ? 1 : 0) +
    ($filters.areaSqftMin  != null   ? 1 : 0) +
    ($filters.areaSqftMax  != null   ? 1 : 0)
  );

  const sequenceOptions = [
    { label: 'All',       value: 'all'       as const },
    { label: 'Primary',   value: 'primary'   as const },
    { label: 'Secondary', value: 'secondary' as const }
  ];
</script>

<div class="relative" bind:this={panelEl}>

  <!-- Trigger button -->
  <button
    type="button"
    onclick={openPanel}
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold border transition-colors
           {open || activeCount > 0
             ? 'border-brand-300 bg-brand-50 text-brand-700'
             : 'border-gray-200 bg-white text-gray-700 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50'}"
  >
    <!-- Funnel icon -->
    <svg class="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
    </svg>
    <span>Filters</span>
    {#if activeCount > 0}
      <span class="inline-flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white leading-none">
        {activeCount}
      </span>
    {/if}
  </button>

  <!-- Dropdown panel -->
  {#if open}
    <div class="absolute right-0 z-30 mt-2 w-72 max-w-[calc(100vw-1rem)] rounded-2xl border border-gray-200 bg-white shadow-xl overflow-hidden">

      <!-- Header -->
      <div class="px-4 py-3 border-b border-gray-100">
        <h3 class="text-sm font-semibold text-gray-900">Other Filters</h3>
      </div>

      <div class="px-4 py-4 space-y-5">

        <!-- Sale Sequence -->
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">Sale Sequence</p>
          <div class="inline-flex rounded-full border border-gray-200 bg-gray-50 p-0.5">
            {#each sequenceOptions as opt}
              <button
                type="button"
                onclick={() => (draftSequence = opt.value)}
                class="rounded-full px-3 py-1.5 text-xs font-semibold transition-all
                       {draftSequence === opt.value
                         ? 'bg-brand-600 text-white shadow-sm'
                         : 'text-gray-700 hover:bg-white'}"
              >
                {opt.label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Property Size -->
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">Property Size (sqft)</p>
          <div class="flex items-center gap-2">
            <input
              type="number"
              placeholder="Min"
              min="0"
              bind:value={draftAreaMin}
              class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder-gray-400
                     focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-400 transition-colors"
            />
            <span class="flex-shrink-0 text-xs text-gray-400">to</span>
            <input
              type="number"
              placeholder="Max"
              min="0"
              bind:value={draftAreaMax}
              class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder-gray-400
                     focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-400 transition-colors"
            />
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between gap-2 border-t border-gray-100 px-4 py-3">
        <button
          type="button"
          onclick={resetAll}
          class="text-xs font-medium text-gray-500 hover:text-red-600 transition-colors"
        >
          Reset all
        </button>
        <button
          type="button"
          onclick={apply}
          class="rounded-full bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 transition-colors"
        >
          Apply filters
        </button>
      </div>

    </div>
  {/if}

</div>
