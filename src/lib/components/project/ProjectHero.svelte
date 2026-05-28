<script lang="ts">
  import { dbReady } from '$lib/stores/db';
  import { dateRangeMs } from '$lib/stores/filters';
  import { queryProjectInfo } from '$lib/db/queries';
  import type { ProjectInfo } from '$lib/db/types';
  import { base } from '$app/paths';

  let { projectName }: { projectName: string } = $props();

  let info = $state<ProjectInfo | null>(null);
  let loading = $state(true);

  $effect(() => {
    const ready = $dbReady;
    const range = $dateRangeMs;
    if (!ready || !projectName) return;
    loading = true;
    queryProjectInfo(projectName, range.start, range.end)
      .then((result) => { info = result; })
      .finally(() => { loading = false; });
  });

  function formatMonth(d: string): string {
    if (!d) return '—';
    try {
      return new Date(d).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
    } catch {
      return d;
    }
  }

  function pctLabel(diff: number): string {
    const abs = Math.abs(diff * 100).toFixed(1);
    return `${diff >= 0 ? '+' : '−'}${abs}%`;
  }

  function capitalise(s: string): string {
    if (!s) return s;
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
</script>

{#if loading}
  <div class="mb-6 rounded-2xl bg-white border border-gray-200 shadow-sm p-5 animate-pulse">
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-5">
      {#each Array(4) as _}
        <div>
          <div class="h-3 w-20 bg-gray-200 rounded mb-2"></div>
          <div class="h-5 w-32 bg-gray-200 rounded mb-1"></div>
          <div class="h-3 w-24 bg-gray-100 rounded"></div>
        </div>
      {/each}
    </div>
  </div>
{:else if info}
  <div class="mb-6 rounded-2xl bg-white border border-gray-200 shadow-sm p-5">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-y-6 divide-gray-100 lg:divide-x">

      <!-- Col 1: Location -->
      <div class="lg:pr-5">
        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">Location</p>
        <a
          href="{base}/area/{encodeURIComponent(info.district)}"
          class="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline"
        >
          {info.district}
        </a>
        {#if info.community && info.community !== info.district}
          <p class="text-xs text-gray-500 mt-0.5">{info.community}</p>
        {/if}
        <p class="text-xs text-gray-400 mt-2.5">
          <span class="font-medium text-gray-500">{formatMonth(info.firstSale)}</span>
          <span class="mx-1 text-gray-300">–</span>
          <span class="font-medium text-gray-500">{formatMonth(info.lastSale)}</span>
        </p>
      </div>

      <!-- Col 2: Property types + layouts -->
      <div class="lg:px-5">
        {#if info.propertyTypes.length > 0}
          <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">Property Type</p>
          <p class="text-sm text-gray-900">{info.propertyTypes.join(', ')}</p>
        {/if}
        {#if info.layouts.length > 0}
          <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5 mt-3">Layouts</p>
          <div class="flex flex-wrap gap-1">
            {#each info.layouts as layout}
              <span class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                {capitalise(layout)}
              </span>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Col 3: Off-plan / Ready split -->
      <div class="lg:px-5 sm:col-span-1 border-t sm:border-t-0 border-gray-100 pt-4 sm:pt-0">
        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Sale Type Mix</p>
        {#if info.totalCount > 0}
          {@const offPct = Math.round((info.offPlanCount / info.totalCount) * 100)}
          {@const readyPct = 100 - offPct}
          <!-- Split bar -->
          <div class="flex rounded-full overflow-hidden h-2 mb-2.5 gap-px bg-gray-100">
            {#if offPct > 0}
              <div
                class="bg-brand-500 h-full transition-all"
                style="width: {offPct}%"
              ></div>
            {/if}
            {#if readyPct > 0}
              <div
                class="bg-navy/25 h-full transition-all"
                style="width: {readyPct}%"
              ></div>
            {/if}
          </div>
          <div class="flex items-center gap-3 text-xs text-gray-600">
            <span class="flex items-center gap-1.5">
              <span class="inline-block w-2 h-2 rounded-full bg-brand-500 flex-shrink-0"></span>
              Off-plan <span class="font-semibold text-gray-900">{offPct}%</span>
            </span>
            <span class="flex items-center gap-1.5">
              <span class="inline-block w-2 h-2 rounded-full bg-navy/25 flex-shrink-0"></span>
              Ready <span class="font-semibold text-gray-900">{readyPct}%</span>
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-1.5">{info.totalCount.toLocaleString()} transactions</p>
        {:else}
          <span class="text-sm text-gray-400">—</span>
        {/if}
      </div>

      <!-- Col 4: vs District benchmark -->
      <div class="lg:pl-5 border-t sm:border-t-0 border-gray-100 pt-4 sm:pt-0">
        <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">vs {info.district}</p>
        {#if info.projectMedianRate && info.districtMedianRate}
          {@const diff = (info.projectMedianRate - info.districtMedianRate) / info.districtMedianRate}
          {@const isAbove = diff >= 0}
          {@const isFlat = Math.abs(diff) < 0.001}
          <div class="flex items-baseline gap-2 mb-1">
            <span class="text-2xl font-bold tabular-nums {isFlat ? 'text-gray-500' : isAbove ? 'text-emerald-600' : 'text-red-500'}">
              {pctLabel(diff)}
            </span>
          </div>
          <p class="text-xs text-gray-500">
            AED {Math.round(info.projectMedianRate).toLocaleString()} /sqft this project
          </p>
          <p class="text-xs text-gray-400 mt-0.5">
            vs AED {Math.round(info.districtMedianRate).toLocaleString()} /sqft district avg
          </p>
        {:else}
          <span class="text-sm text-gray-400">Not enough data</span>
        {/if}
      </div>

    </div>
  </div>
{/if}
