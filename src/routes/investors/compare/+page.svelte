<script lang="ts">
  import DistrictComparison from '$lib/components/investors/DistrictComparison.svelte';
  import AskingVsActualHero from '$lib/components/home/AskingVsActualHero.svelte';
</script>

<svelte:head>
  <title>Abu Dhabi District Comparison — Side-by-Side Investment Metrics | ADInteract</title>
  <meta name="description" content="Compare 2–3 Abu Dhabi districts side by side: median sale price, AED/sqft, YoY price growth, gross rental yield, service charges, transaction volume, and supply pipeline. Powered by ADREC transaction data." />
  <meta property="og:title" content="Abu Dhabi District Comparison — Side-by-Side Investment Metrics | ADInteract" />
  <meta property="og:description" content="Which Abu Dhabi district wins on yield, price growth, or liquidity? Compare up to 3 areas across 7 investment metrics from ADREC-registered transaction data." />

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
