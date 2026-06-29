<script lang="ts">
  import type { LayoutSummaryRow } from '$lib/db/types';

  let { data = [] as LayoutSummaryRow[] } = $props();

  let maxCount = $derived(Math.max(...data.map((r) => r.count), 1));

  function capitalise(s: string): string {
    if (!s) return s;
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
</script>

{#if data.length === 0}
  <div class="h-48 flex items-center justify-center">
    <p class="text-sm text-gray-400">No layout data for this period</p>
  </div>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-100">
          <th class="pb-2.5 text-start text-[10px] font-bold uppercase tracking-wider text-gray-400">Layout</th>
          <th class="pb-2.5 text-end text-[10px] font-bold uppercase tracking-wider text-gray-400">Deals</th>
          <th class="pb-2.5 text-end text-[10px] font-bold uppercase tracking-wider text-gray-400">Median Price</th>
          <th class="pb-2.5 text-end text-[10px] font-bold uppercase tracking-wider text-gray-400">AED / sqft</th>
          <th class="pb-2.5 w-20"></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        {#each data as row}
          <tr class="hover:bg-gray-50/50 transition-colors">
            <td class="py-2.5 pe-3 font-medium text-gray-900">{capitalise(row.layout)}</td>
            <td class="py-2.5 text-end tabular-nums text-gray-600">{row.count.toLocaleString()}</td>
            <td class="py-2.5 text-end tabular-nums text-gray-700 whitespace-nowrap">
              {row.medianPrice ? `AED ${Math.round(row.medianPrice).toLocaleString()}` : '—'}
            </td>
            <td class="py-2.5 text-end tabular-nums font-semibold text-gray-900 whitespace-nowrap">
              {row.medianRate ? Math.round(row.medianRate).toLocaleString() : '—'}
            </td>
            <!-- Deal-share mini bar -->
            <td class="py-2.5 ps-3">
              <div class="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  class="bg-brand-400 h-1.5 rounded-full transition-all"
                  style="width: {Math.round((row.count / maxCount) * 100)}%"
                ></div>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
