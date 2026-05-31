<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';

  let { data } = $props();
  const { districtName, summary } = data;

  const periodLabel = summary?.is_12m ? 'the past 12 months' : 'the available dataset';

  // Redirect users to the homepage with district filter applied.
  // Google reads the prerendered HTML above before any JS runs.
  // Users land here briefly, then get the familiar /?district= interactive view.
  onMount(() => {
    goto(`${base}/?district=${encodeURIComponent(districtName)}`, { replaceState: true });
  });

  function fmtNum(n: number | null): string {
    if (n == null) return '—';
    return n.toLocaleString('en-AE');
  }
</script>

<svelte:head>
  <title>
    {districtName} Property Prices — AED/sqft &amp; Transactions | ADInteract
  </title>
  <meta
    name="description"
    content={summary
      ? `${fmtNum(summary.tx_count_12m)} ADREC-verified property transactions in ${districtName}. Median AED ${fmtNum(summary.median_psf)}/sqft. View off-plan and ready sales data, price trends, and top projects.`
      : `Property transaction data for ${districtName}, Abu Dhabi. ADREC-sourced price trends, median AED/sqft, and top projects.`}
  />
  <!-- Canonical is the clean slug URL — tells Google this is the authoritative page -->
  <link rel="canonical" href="https://www.adinteract.co{base}/area/{summary?.slug ?? districtName.toLowerCase().replace(/\s+/g, '-')}" />
</svelte:head>

<!-- ── Prose block ────────────────────────────────────────────────────────
     This HTML is baked in at build time. Google reads it without running JS.
     Users see it for ~100 ms before the onMount redirect fires.
──────────────────────────────────────────────────────────────────────── -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-16">

  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-5">
    <a href="{base}/" class="hover:text-brand-600 transition-colors">Overview</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="font-medium text-gray-900">{districtName}</span>
  </nav>

  <h1 class="text-3xl font-bold text-navy mb-1">{districtName}</h1>
  <p class="text-sm text-gray-400 mb-6">
    Abu Dhabi property transactions · ADREC-verified data · updated daily
  </p>

  {#if summary}
    <div class="rounded-xl border border-gray-100 bg-gray-50 px-6 py-5 text-sm text-gray-700 leading-relaxed max-w-3xl">
      <p>
        <strong>{districtName}</strong> recorded
        <strong>{fmtNum(summary.tx_count_12m)} ADREC-verified property transactions</strong>
        in {periodLabel}.
        {#if summary.median_psf}
          The median price is <strong>AED {fmtNum(summary.median_psf)}/sqft</strong>
          {#if summary.p10_psf && summary.p90_psf}
            , with most properties trading between
            AED {fmtNum(summary.p10_psf)} and AED {fmtNum(summary.p90_psf)}/sqft.
          {:else}
            .
          {/if}
        {/if}
        {#if summary.median_price}
          The median transaction value is <strong>AED {fmtNum(summary.median_price)}</strong>.
        {/if}
        {#if summary.top_layouts.length}
          The most actively traded property types are
          <strong>{summary.top_layouts.join(', ')}</strong>.
        {/if}
      </p>
      <p class="mt-2 text-xs text-gray-400">
        Data sourced from the Abu Dhabi Real Estate Centre (ADREC) and refreshed daily.
        {fmtNum(summary.tx_count_all)} total transactions recorded since 2019.
        Last transaction: {summary.last_sale}.
      </p>
    </div>

    <!-- CTA — visible to users for the ~100 ms before redirect fires -->
    <p class="mt-5 text-sm text-gray-500">
      Loading interactive charts…
      <a
        href="{base}/?district={encodeURIComponent(districtName)}"
        class="text-brand-600 underline hover:text-brand-700"
      >Click here if not redirected</a>
    </p>
  {:else}
    <p class="text-gray-500 text-sm">
      Loading {districtName} data…
      <a href="{base}/?district={encodeURIComponent(districtName)}" class="text-brand-600 underline">
        Go to {districtName} analytics →
      </a>
    </p>
  {/if}

</div>
