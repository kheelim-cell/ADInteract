<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';

  const options = [
    { label: 'All',       value: 'all'       as const },
    { label: 'Primary',   value: 'primary'   as const },
    { label: 'Secondary', value: 'secondary' as const }
  ];
</script>

<div class="inline-flex rounded-full border border-gray-200 bg-gray-50 p-0.5">
  {#each options as option}
    <button
      type="button"
      onclick={() => updateFilter({ saleSequence: option.value })}
      class="rounded-full px-3 py-1.5 text-xs font-semibold transition-all
             {$filters.saleSequence === option.value
               ? 'bg-brand-600 text-white shadow-sm'
               : 'text-gray-900 hover:text-gray-900 hover:bg-white'}"
    >
      {option.label}
    </button>
  {/each}
</div>
