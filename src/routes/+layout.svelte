<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import Header from '$lib/components/ui/Header.svelte';
  import Footer from '$lib/components/ui/Footer.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
  import { initDuckDB, loadData } from '$lib/db/duckdb';
  import { dbReady, dbError, dbLoading, metadata } from '$lib/stores/db';
  import { base } from '$app/paths';
  import type { Metadata } from '$lib/db/types';

  let { children } = $props();

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

      dbReady.set(true);
    } catch (e) {
      dbError.set(e instanceof Error ? e.message : 'Failed to initialize database');
    } finally {
      dbLoading.set(false);
    }
  });
</script>

<div class="min-h-screen flex flex-col bg-[#F4F1EB]">
  <Header lastUpdated={$metadata?.lastUpdated ?? ''} />

  <main class="flex-1">
    {#if $dbLoading}
      <div class="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <LoadingSpinner />
        <p class="text-gray-500 text-sm">Loading Abu Dhabi real estate data...</p>
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
