<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';
  import { metadata } from '$lib/stores/db';
  import { m } from '$lib/paraglide/messages.js';

  let open = $state(false);
  let el = $state<HTMLDivElement>();

  let LAYOUT_OPTIONS = $derived([
    { label: m.filter_layout_studio(),      value: 'studio' },
    { label: m.filter_layout_1_bed(),       value: '1 bed' },
    { label: m.filter_layout_2_beds(),      value: '2 beds' },
    { label: m.filter_layout_3_beds(),      value: '3 beds' },
    { label: m.filter_layout_4_beds(),      value: '4 beds' },
    { label: m.filter_layout_5_beds(),      value: '5 beds' },
    { label: m.filter_layout_6_plus_beds(), value: '6+ beds' },
  ]);
  let selected = $derived($filters.layouts);
  let count = $derived(selected.length);

  function toggle(value: string) {
    const current = [...selected];
    const idx = current.indexOf(value);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(value);
    }
    updateFilter({ layouts: current });
  }

  function clearAll() {
    updateFilter({ layouts: [] });
  }

  function handleClickOutside(e: MouseEvent) {
    if (el && !el.contains(e.target as Node)) {
      open = false;
    }
  }

  $effect(() => {
    if (open) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });
</script>

<div class="relative" bind:this={el}>
  <button
    type="button"
    onclick={() => (open = !open)}
    class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer select-none
           {count > 0
             ? 'border-brand-300 bg-brand-50 text-brand-700'
             : 'border-gray-200 bg-white text-gray-900 hover:border-gray-300 hover:bg-gray-50'}"
  >
    {m.filter_layout_label()}
    {#if count > 0}
      <span class="inline-flex items-center justify-center rounded-full bg-brand-600 text-white text-[10px] font-bold min-w-[18px] h-[18px] px-1">
        {count}
      </span>
    {/if}
    <svg class="h-3 w-3 text-gray-400 transition-transform {open ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  </button>

  {#if open}
    <div class="absolute z-20 mt-1.5 w-48 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
      {#if count > 0}
        <div class="border-b border-gray-100 px-3 py-2 flex items-center justify-between">
          <span class="text-[10px] font-medium uppercase tracking-wider text-gray-400">{m.filter_selected_count({ count: String(count) })}</span>
          <button
            type="button"
            onclick={clearAll}
            class="text-xs text-brand-600 hover:text-brand-800 font-medium transition-colors"
          >
            {m.filter_clear()}
          </button>
        </div>
      {/if}
      <div class="max-h-60 overflow-y-auto py-1">
        {#each LAYOUT_OPTIONS as option}
          <label class="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors">
            <input
              type="checkbox"
              checked={selected.includes(option.value)}
              onchange={() => toggle(option.value)}
              class="h-3.5 w-3.5 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
            />
            <span class="truncate text-xs">{option.label}</span>
          </label>
        {/each}
      </div>
    </div>
  {/if}
</div>
