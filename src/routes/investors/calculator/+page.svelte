<script lang="ts">
  import GatedSection from '$lib/components/auth/GatedSection.svelte';
  import OffplanCalculator from '$lib/components/investors/OffplanCalculator.svelte';
  import ReadyCalculator from '$lib/components/investors/ReadyCalculator.svelte';
  import { m } from '$lib/paraglide/messages.js';

  let calcTab = $state<'offplan' | 'ready'>('offplan');
</script>

<svelte:head>
  <title>{m.seo_calculator_title()}</title>
  <meta name="description" content={m.seo_calculator_description()} />
  <meta property="og:title" content={m.seo_calculator_title()} />
  <meta property="og:description" content={m.seo_calculator_og_description()} />

  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to Calculate Abu Dhabi Property ROI",
    "description": "Model net rental yield, capital gain CAGR, and total return on investment for Abu Dhabi off-plan and ready properties using live ADREC transaction data.",
    "step": [
      { "@type": "HowToStep", "name": "Select property type", "text": "Choose between off-plan (under construction) or ready (completed) property to match your investment scenario." },
      { "@type": "HowToStep", "name": "Enter purchase details", "text": "Input the property price, size in sqft, and select the district and layout. The calculator auto-populates comparable rent and price appreciation from ADREC data." },
      { "@type": "HowToStep", "name": "Set your holding period", "text": "Choose how many years you plan to hold the property before resale." },
      { "@type": "HowToStep", "name": "Review your returns", "text": "The calculator outputs net rental yield %, capital gain CAGR %, and total ROI — accounting for all transaction costs, service charges, and financing." }
    ]
  })}</script>`}
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">
  <GatedSection proOnly={true}>
    <!-- Tab toggle -->
    <div class="flex gap-2 mb-6">
      <button
        type="button"
        onclick={() => { calcTab = 'offplan'; }}
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all
          {calcTab === 'offplan'
            ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
            : 'bg-gray-100 border-gray-300 text-gray-500 hover:bg-gray-200 hover:border-gray-400 hover:text-gray-700'}"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
        {m.calc_tab_offplan()}
      </button>
      <button
        type="button"
        onclick={() => { calcTab = 'ready'; }}
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all
          {calcTab === 'ready'
            ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
            : 'bg-gray-100 border-gray-300 text-gray-500 hover:bg-gray-200 hover:border-gray-400 hover:text-gray-700'}"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
        {m.calc_tab_ready()}
      </button>
    </div>

    <!-- Calculator -->
    {#if calcTab === 'offplan'}
      <OffplanCalculator />
    {:else}
      <ReadyCalculator />
    {/if}
  </GatedSection>
</div>
