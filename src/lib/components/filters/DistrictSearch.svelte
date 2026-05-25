<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';
  import { metadata } from '$lib/stores/db';

  let { searchType = 'district' as 'district' | 'project' } = $props();

  let query = $state('');
  let open = $state(false);
  let inputEl = $state<HTMLInputElement>();
  let containerEl = $state<HTMLDivElement>();

  let selected = $derived(
    searchType === 'district' ? $filters.district : $filters.project
  );

  let options = $derived(() => {
    if (!$metadata) return [];
    return searchType === 'district' ? $metadata.districts : $metadata.projects;
  });

  let filtered = $derived(() => {
    const items = options();
    if (!query.trim()) return items;
    const q = query.toLowerCase();
    return items.filter((item) => item.toLowerCase().includes(q));
  });

  function select(value: string) {
    if (searchType === 'district') {
      updateFilter({ district: value, project: null });
    } else {
      updateFilter({ project: value, district: null });
    }
    query = '';
    open = false;
  }

  function clear() {
    if (searchType === 'district') {
      updateFilter({ district: null });
    } else {
      updateFilter({ project: null });
    }
    query = '';
  }

  function handleInput() {
    open = query.length > 0 || document.activeElement === inputEl;
  }

  function handleFocus() {
    open = true;
  }

  function handleClickOutside(e: MouseEvent) {
    if (containerEl && !containerEl.contains(e.target as Node)) {
      open = false;
    }
  }

  $effect(() => {
    if (open) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });

  let placeholder = $derived(
    searchType === 'district' ? 'Search district...' : 'Search project...'
  );
</script>

<div class="relative" bind:this={containerEl}>
  {#if selected}
    <div class="inline-flex items-center gap-1.5 rounded-full border border-brand-300 bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700">
      <svg class="h-3 w-3 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <span class="max-w-[200px] truncate">{selected}</span>
      <button
        type="button"
        onclick={clear}
        class="rounded-full p-0.5 text-brand-400 hover:bg-brand-100 hover:text-brand-600 transition-colors"
        aria-label="Clear selection"
      >
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {:else}
    <div class="relative">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        bind:this={inputEl}
        type="text"
        bind:value={query}
        oninput={handleInput}
        onfocus={handleFocus}
        {placeholder}
        class="w-full min-w-[220px] rounded-full border border-gray-200 bg-gray-50 py-1.5 pl-8 pr-3 text-xs text-gray-700 placeholder-gray-400 transition-colors focus:bg-white focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
      />
    </div>

    {#if open && filtered().length > 0}
      <div class="absolute z-20 mt-1.5 w-full max-h-64 overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-lg">
        {#each filtered() as item}
          <button
            type="button"
            onclick={() => select(item)}
            class="flex w-full items-center gap-2 px-3 py-2 text-xs text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors text-left"
          >
            <svg class="h-3 w-3 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="truncate">{item}</span>
          </button>
        {/each}
      </div>
    {/if}
  {/if}
</div>
