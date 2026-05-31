<script lang="ts">
  import type { FlipRow } from '$lib/db/investor_queries';
  import { base } from '$app/paths';

  type SortCol = 'roiPct' | 'psfGain' | 'exitPsf' | 'entryPsf' | 'offplanCount' | 'secondaryCount';

  let {
    rows,
    loading,
  }: {
    rows: FlipRow[];
    loading: boolean;
  } = $props();

  let sortCol = $state<SortCol>('roiPct');
  let sortDir = $state<'asc' | 'desc'>('desc');

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortCol = col;
      sortDir = 'desc';
    }
  }

  let sorted = $derived.by(() => {
    const r = [...rows];
    r.sort((a, b) => {
      const av = a[sortCol] as number;
      const bv = b[sortCol] as number;
      return sortDir === 'desc' ? bv - av : av - bv;
    });
    return r;
  });

  function fmt(n: number): string {
    return new Intl.NumberFormat('en-AE', { maximumFractionDigits: 0 }).format(n);
  }

  function fmtDate(s: string): string {
    // e.g. "2023-04-15" → "Apr 2023"
    if (!s) return '-';
    const d = new Date(s);
    return d.toLocaleDateString('en-AE', { month: 'short', year: 'numeric' });
  }

  function projectSlug(name: string): string {
    return encodeURIComponent(name.toLowerCase().replace(/\s+/g, '-'));
  }

  const TH = 'text-left text-[10px] font-bold uppercase tracking-wider text-gray-400 py-2 px-3 whitespace-nowrap select-none cursor-pointer hover:text-gray-600 transition-colors';
  const TD = 'py-2.5 px-3 text-sm';

  function arrow(col: SortCol): string {
    if (sortCol !== col) return '↕';
    return sortDir === 'desc' ? '↓' : '↑';
  }

  // ROI colour bands
  function roiClass(pct: number): string {
    if (pct >= 30) return 'text-emerald-700 bg-emerald-50 font-bold';
    if (pct >= 15) return 'text-emerald-600 bg-emerald-50/60 font-semibold';
    if (pct >= 5)  return 'text-amber-700 bg-amber-50 font-semibold';
    return 'text-gray-600';
  }
</script>

<div class="overflow-x-auto rounded-xl border border-gray-100 bg-white shadow-sm">
  {#if loading}
    <!-- Skeleton -->
    <div class="space-y-2 p-4">
      {#each Array(8) as _}
        <div class="h-9 w-full animate-pulse rounded-lg bg-gray-100"></div>
      {/each}
    </div>
  {:else if sorted.length === 0}
    <div class="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
      </svg>
      <p class="text-sm font-semibold text-gray-500">No flip opportunities found</p>
      <p class="text-xs text-gray-400">Try broadening the district or layout filter</p>
    </div>
  {:else}
    <table class="w-full border-collapse text-left">
      <thead class="border-b border-gray-100 bg-gray-50/80">
        <tr>
          <th class="{TH} pl-4" style="min-width:180px">Project</th>
          <th class={TH}>District</th>
          <th class={TH}>Layout</th>
          <!-- sortable columns -->
          <th class={TH} onclick={() => toggleSort('entryPsf')}>
            Entry PSF {arrow('entryPsf')}
          </th>
          <th class={TH} onclick={() => toggleSort('exitPsf')}>
            Exit PSF {arrow('exitPsf')}
          </th>
          <th class={TH} onclick={() => toggleSort('psfGain')}>
            PSF Gain {arrow('psfGain')}
          </th>
          <th class={TH} onclick={() => toggleSort('roiPct')}>
            ROI % {arrow('roiPct')}
          </th>
          <th class="{TH}" onclick={() => toggleSort('offplanCount')}>
            Off-plan Tx {arrow('offplanCount')}
          </th>
          <th class="{TH}" onclick={() => toggleSort('secondaryCount')}>
            Secondary Tx {arrow('secondaryCount')}
          </th>
          <th class={TH}>Entry Window</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        {#each sorted as row, i}
          <tr class="hover:bg-gray-50/60 transition-colors {i % 2 === 0 ? '' : 'bg-gray-50/30'}">
            <!-- Project name → link -->
            <td class="{TD} pl-4 font-medium text-gray-900" style="min-width:180px">
              <a
                href="{base}/project/{projectSlug(row.projectName)}"
                class="hover:text-brand-600 hover:underline transition-colors line-clamp-2"
              >
                {row.projectName}
              </a>
            </td>

            <!-- District → link -->
            <td class="{TD} text-gray-600">
              <a
                href="{base}/area/{encodeURIComponent(row.district.toLowerCase().replace(/\s+/g, '-'))}"
                class="hover:text-brand-600 transition-colors whitespace-nowrap"
              >
                {row.district}
              </a>
            </td>

            <!-- Layout -->
            <td class="{TD} capitalize whitespace-nowrap text-gray-600">{row.layout}</td>

            <!-- Entry PSF -->
            <td class="{TD} text-right font-mono text-gray-700 whitespace-nowrap">
              {fmt(row.entryPsf)}
            </td>

            <!-- Exit PSF -->
            <td class="{TD} text-right font-mono text-gray-700 whitespace-nowrap">
              {fmt(row.exitPsf)}
            </td>

            <!-- PSF Gain -->
            <td class="{TD} text-right font-mono font-semibold text-emerald-700 whitespace-nowrap">
              +{fmt(row.psfGain)}
            </td>

            <!-- ROI % — colour banded -->
            <td class="{TD} text-right whitespace-nowrap">
              <span class="inline-block rounded-full px-2 py-0.5 text-xs {roiClass(row.roiPct)}">
                +{row.roiPct.toFixed(1)}%
              </span>
            </td>

            <!-- Off-plan count with tooltip-style confidence -->
            <td class="{TD} text-right text-gray-500 whitespace-nowrap">
              {row.offplanCount}
            </td>

            <!-- Secondary count -->
            <td class="{TD} text-right text-gray-500 whitespace-nowrap">
              {row.secondaryCount}
            </td>

            <!-- Entry window: "Apr 2022 – Mar 2024" -->
            <td class="{TD} whitespace-nowrap text-xs text-gray-400">
              {fmtDate(row.earliestOffplan)} – {fmtDate(row.latestOffplan)}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>

    <!-- Footer legend -->
    <div class="border-t border-gray-100 px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-1.5 text-[10px] text-gray-400">
      <span>{sorted.length} project–layout combinations</span>
      <span class="hidden sm:inline">·</span>
      <span>Entry PSF = median off-plan rate/sqft (12–48 months ago)</span>
      <span class="hidden sm:inline">·</span>
      <span>Exit PSF = median secondary-market rate/sqft (last 12 months)</span>
      <span class="hidden sm:inline">·</span>
      <span>ROI = price-per-sqft appreciation only — excludes transaction costs, DLD fees, and financing</span>
    </div>
  {/if}
</div>
