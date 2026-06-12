<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import Header from '$lib/components/ui/Header.svelte';
  import Footer from '$lib/components/ui/Footer.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
  import SignInModal from '$lib/components/auth/SignInModal.svelte';
  import { initDuckDB, loadData, loadRentalData } from '$lib/db/duckdb';
  import { dbReady, dbError, dbLoading, metadata, rentalMetadata } from '$lib/stores/db';
  import { showSignInModal } from '$lib/stores/auth';
  import { base } from '$app/paths';
  import { browser } from '$app/environment';
  import { page } from '$app/stores';
  import type { Metadata } from '$lib/db/types';
  import type { RentalMetadata } from '$lib/db/rental_types';

  let { children } = $props();

  const SITE_URL = 'https://adinteract.co';
  let canonicalUrl = $derived(`${SITE_URL}${$page.url.pathname}`);

  onMount(async () => {
    try {
      await initDuckDB();
      await loadData(base || '');

      try {
        const res = await fetch(`${base}/data/meta.json`);
        if (res.ok) {
          const meta: Metadata = await res.json();
          metadata.set(meta);
        }
      } catch {
        /* meta.json is optional */
      }

      // Load rental data in parallel (non-blocking — failure just means no rental tab)
      try {
        const rentalOk = await loadRentalData(base || '');
        if (rentalOk) {
          const rRes = await fetch(`${base}/data/rental_meta.json`);
          if (rRes.ok) {
            const rmeta: RentalMetadata = await rRes.json();
            rentalMetadata.set(rmeta);
          }
        }
      } catch {
        /* rental data is optional */
      }

      dbReady.set(true);
    } catch (e) {
      dbError.set(e instanceof Error ? e.message : 'Failed to initialize database');
    } finally {
      dbLoading.set(false);
    }
  });
</script>

<svelte:head>
  <!-- /area/ pages set their own meta (title, description, OG, canonical) — don't double-emit -->
  {#if !$page.url.pathname.startsWith('/area/')}
    <meta name="description" content="Abu Dhabi real estate transaction analytics — search, filter, and analyse property sales data powered by ADREC." />
    <link rel="canonical" href={canonicalUrl} />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="ADInteract — Abu Dhabi Property Prices & Transactions" />
    <meta property="og:description" content="Search Abu Dhabi property transactions from ADREC. Filter by district, project, and price. Median prices, volumes, and trends — updated daily." />
    <meta property="og:url" content={canonicalUrl} />
    <meta property="og:image" content="https://adinteract.co/brand/og-image.png" />
    <meta property="og:image:width" content="1789" />
    <meta property="og:image:height" content="937" />
    <meta property="og:image:type" content="image/png" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="ADInteract — Abu Dhabi Property Prices & Transactions" />
    <meta name="twitter:description" content="Search Abu Dhabi property transactions from ADREC. Filter by district, project, and price. Median prices, volumes, and trends — updated daily." />
    <meta name="twitter:image" content="https://adinteract.co/brand/og-image.png" />
  {/if}
</svelte:head>

<div class="min-h-screen flex flex-col bg-[#FAFAF6]">
  <Header lastUpdated={$metadata?.lastUpdated ?? ''} />

  {#if $showSignInModal}
    <SignInModal />
  {/if}

  <main class="flex-1">
    <!-- During SSR/prerender, always render children so SEO pages emit their
         prose and head tags. The DuckDB loading gate only applies in-browser. -->
    {#if browser && $dbLoading}
      <!-- Hero renders immediately while DuckDB loads in background — prevents bounce -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <!-- Value prop -->
        <div class="text-center mb-10">
          <h2 class="text-2xl sm:text-3xl font-bold text-navy mb-3">
            Abu Dhabi Property Transactions — Live ADREC Data
          </h2>
          <p class="text-gray-500 text-sm sm:text-base max-w-2xl mx-auto">
            Search and analyse 97,000+ registered property sales. Filter by district, project,
            price, and date. Median prices, volumes, and trends updated daily.
          </p>
        </div>

        <!-- Skeleton stat cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-8">
          {#each ['Transaction Volume', 'Median Price', 'Median AED/sqft', 'Total Value'] as label}
            <div class="stat-card">
              <p class="text-xs font-semibold text-gray-500 mb-2">{label}</p>
              <div class="h-7 w-28 bg-gray-200 rounded animate-pulse mb-2"></div>
              <div class="h-3 w-16 bg-gray-200 rounded animate-pulse"></div>
            </div>
          {/each}
        </div>

        <!-- Skeleton charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {#each [1, 2] as _}
            <div class="chart-card">
              <div class="h-4 w-32 bg-gray-200 rounded animate-pulse mb-4"></div>
              <div class="h-56 bg-gray-100 rounded-lg animate-pulse"></div>
            </div>
          {/each}
        </div>

        <!-- Investor tool teasers — visible during load so users know what's here -->
        <div class="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white px-5 py-4 mb-8">
          <p class="text-xs font-bold text-emerald-700 uppercase tracking-wide mb-3">Investor Tools</p>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {#each ['ROI Calculator', 'Compare Districts', 'Flip Scanner', 'Rental Yield'] as tool}
              <div class="rounded-xl border border-emerald-100 bg-white px-4 py-3">
                <div class="h-3 w-20 bg-emerald-100 rounded animate-pulse mb-2"></div>
                <p class="text-xs text-gray-400">{tool}</p>
              </div>
            {/each}
          </div>
        </div>

        <div class="flex items-center justify-center gap-3 text-gray-500 text-sm">
          <LoadingSpinner />
          <span>Loading transaction data…</span>
        </div>
      </div>
    {:else if $dbError}
      <div class="flex flex-col items-center justify-center min-h-[60vh] gap-4 px-4">
        <div class="rounded-xl bg-red-50 border border-red-200 p-6 max-w-lg w-full text-center">
          <svg class="mx-auto h-10 w-10 text-red-400 mb-3" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <h3 class="text-red-800 font-semibold text-lg mb-1">Failed to Load Data</h3>
          <p class="text-red-600 text-sm">{$dbError}</p>
          <button
            class="mt-4 btn-primary bg-red-600 hover:bg-red-700 focus:ring-red-500"
            onclick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    {:else}
      {@render children()}
    {/if}
  </main>

  <Footer />
</div>
