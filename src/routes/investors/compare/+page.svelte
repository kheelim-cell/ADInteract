<script lang="ts">
  import DistrictComparison from '$lib/components/investors/DistrictComparison.svelte';
  import AskingVsActualHero from '$lib/components/home/AskingVsActualHero.svelte';
  import { m } from '$lib/paraglide/messages.js';
</script>

<svelte:head>
  <title>{m.seo_compare_title()}</title>
  <meta name="description" content={m.seo_compare_description()} />
  <meta property="og:title" content={m.seo_compare_title()} />
  <meta property="og:description" content={m.seo_compare_og_description()} />

  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Abu Dhabi District Investment Comparison",
    "description": "Side-by-side comparison of Abu Dhabi real estate districts across median sale price, AED/sqft appreciation, gross rental yield, service charges, transaction volume, and supply pipeline — sourced from ADREC registered transactions.",
    "creator": { "@type": "Organization", "name": "ADInteract" },
    "keywords": ["Abu Dhabi property investment", "district comparison", "real estate yield", "ADREC", "ADInteract"],
    "license": "https://creativecommons.org/licenses/by/4.0/"
  })}</script>`}
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">
  <AskingVsActualHero />
  <DistrictComparison />
</div>
