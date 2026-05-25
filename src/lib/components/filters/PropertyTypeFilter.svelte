<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';

  let open = $state(false);
  let el = $state<HTMLDivElement>();

  const PROPERTY_OPTIONS = [
    { label: 'Apartment',                value: 'apartment' },
    { label: 'Duplex',                   value: 'duplex' },
    { label: 'Townhouse / Attached Villa', value: 'townhouse / attached villa' },
    { label: 'Villa',                    value: 'villa' },
    { label: 'Office',                   value: 'office' },
    { label: 'Retail',                   value: 'retail' },
  ];

  let selected = $derived($filters.propertyTypes);
  let count = $derived(selected.length);

  function toggle(value: string) {
    const current = [...selected];
    const idx = current.indexOf(value);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(value);
    }
    updateFilter({ propertyTypes: current });
  }

  function clearAll() {
    updateFilter({ propertyTypes: [] });
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
             : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50'}"
  >
    Property Type
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
    <div class="absolute z-20 mt-1.5 w-56 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
      {#if count > 0}
        <div class="border-b border-gray-100 px-3 py-2 flex items-center justify-between">
          <span class="text-[10px] font-medium uppercase tracking-wider text-gray-400">{count} selected</span>
          <button
            type="button"
            onclick={clearAll}
            class="text-xs text-brand-600 hover:text-brand-800 font-medium transition-colors"
          >
            Clear
          </button>
        </div>
      {/if}
      <div class="max-h-60 overflow-y-auto py-1">
        {#each PROPERTY_OPTIONS as option}
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
