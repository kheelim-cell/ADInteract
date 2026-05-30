<script lang="ts">
  import { metadata } from '$lib/stores/db';
  import ServiceChargeTable from '$lib/components/investors/ServiceChargeTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import GatedBlur from '$lib/components/auth/GatedBlur.svelte';

  let filterDistrict = $state('');

  let hasFilter = $derived(!!filterDistrict);

  let districts = $derived($metadata?.districts ?? []);

  const sel = 'text-xs font-medium text-gray-700 border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[9rem]';
</script>

<svelte:head>
  <title>Service Charges — ADInteract Investor Intelligence</title>
  <meta name="description" content="Annual ADREC-registered service charge rates by Abu Dhabi project in AED/sqft." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-6">

  <!-- ── Filter bar ──────────────────────────────────────────────────────── -->
  <div>
    <div class="flex flex-wrap items-center gap-3">
      <select bind:value={filterDistrict} class={sel}>
        <option value="">All Districts</option>
        {#each districts as d}
          <option value={d}>{d}</option>
        {/each}
      </select>

      {#if hasFilter}
        <button
          type="button"
          onclick={() => { filterDistrict = ''; }}
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
          Clear filter
        </button>
      {/if}
    </div>
    <PopularAreaChips activeDistrict={filterDistrict || null} onSelect={(d) => { filterDistrict = d; }} />
  </div>

  <!-- ── Section heading ─────────────────────────────────────────────────── -->
  <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">
    Annual Service Charges · ADREC Registered Projects
  </h3>

  <!-- ── Service charge table ────────────────────────────────────────────── -->
  <GatedSection proOnly={true}>
    <GatedBlur>
      <ServiceChargeTable district={filterDistrict} />
    </GatedBlur>
  </GatedSection>

</div>
