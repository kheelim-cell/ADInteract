<script lang="ts">
  import { filters, updateFilter } from '$lib/stores/filters';
  import { m } from '$lib/paraglide/messages.js';

  let options = $derived([
    { label: m.filter_common_all(),               value: 'all'       as const },
    { label: m.filter_sale_sequence_primary(),     value: 'primary'   as const },
    { label: m.filter_sale_sequence_secondary(),   value: 'secondary' as const }
  ]);
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
