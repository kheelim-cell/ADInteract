<script lang="ts">
  const POPULAR_DISTRICTS = [
    'Al Reem Island',
    'Yas Island',
    'Al Saadiyat Island',
    'Al Rahah',
    'Khalifa City',
    'Al Reef',
  ] as const;

  let {
    activeDistrict = null,
    alwaysShow = false,
    onSelect,
  }: {
    activeDistrict: string | null;
    alwaysShow?: boolean;
    onSelect: (district: string) => void;
  } = $props();
</script>

{#if alwaysShow || !activeDistrict}
  <div class="flex flex-wrap items-center gap-2 mt-3">
    <span class="text-xs font-medium text-gray-400 shrink-0">Popular:</span>
    {#each POPULAR_DISTRICTS as district}
      <button
        type="button"
        onclick={() => onSelect(district)}
        class="inline-flex items-center rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700 transition-colors"
      >
        {district}
      </button>
    {/each}
  </div>
{/if}
