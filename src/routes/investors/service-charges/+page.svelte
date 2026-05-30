<script lang="ts">
  import { metadata } from '$lib/stores/db';
  import ServiceChargeTable from '$lib/components/investors/ServiceChargeTable.svelte';
  import PopularAreaChips from '$lib/components/ui/PopularAreaChips.svelte';
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import GatedBlur from '$lib/components/auth/GatedBlur.svelte';

  let filterDistrict = $state('');
  let searchQuery    = $state('');

  let hasFilter = $derived(!!(filterDistrict || searchQuery.trim()));

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

      <!-- Search -->
      <div class="relative">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          placeholder="Search project or developer…"
          bind:value={searchQuery}
          class="pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-white focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 min-w-[200px]"
        />
      </div>

      {#if hasFilter}
        <button
          type="button"
          onclick={() => { filterDistrict = ''; searchQuery = ''; }}
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-colors"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
          Clear filters
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
      <ServiceChargeTable district={filterDistrict} {searchQuery} />
    </GatedBlur>
  </GatedSection>

</div>
