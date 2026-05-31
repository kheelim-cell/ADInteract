<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { updateFilter } from '$lib/stores/filters';
  import DashboardContent from '$lib/components/DashboardContent.svelte';

  let { data } = $props();

  // summary may be null for districts not in the generated JSON
  const { summary } = data;

  let districtName = $derived(decodeURIComponent($page.params.district));

  // Human-readable period label for prose
  const periodLabel = summary?.is_12m ? 'the past 12 months' : 'the available dataset';

  onMount(() => {
    updateFilter({ district: districtName, project: null });
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
      : `Property transaction data for ${districtName}, Abu Dhabi. View ADREC-sourced price trends, median AED/sqft, and top projects.`}
  />
  <link rel="canonical" href="https://adinteract.co/area/{encodeURIComponent(districtName)}" />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6">
  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-4">
    <a href="{base}/" class="hover:text-brand-600 transition-colors">Overview</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="font-medium text-gray-900">{districtName}</span>
  </nav>

  <div class="flex items-start justify-between mb-4">
    <div>
      <h1 class="text-2xl font-bold text-navy">{districtName}</h1>
      <p class="text-sm text-gray-400 mt-0.5">District analytics · Abu Dhabi property transactions</p>
    </div>
    <a
      href="{base}/"
      class="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-brand-600 transition-colors bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-brand-300 shadow-sm"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
      </svg>
      Back
    </a>
  </div>

  <!-- Static prose block — pre-rendered at build time, visible to Google before JS loads -->
  {#if summary}
    <div class="rounded-xl border border-gray-100 bg-gray-50 px-5 py-4 mb-6 text-sm text-gray-700 leading-relaxed">
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
        {summary.tx_count_all.toLocaleString('en-AE')} total transactions recorded since 2019.
      </p>
    </div>
  {/if}
</div>

<DashboardContent
  topAreasLabel="Top Projects by Volume"
  topAreasClickable={false}
  useTopProjects={true}
/>
