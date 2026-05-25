<script lang="ts">
  import { metadata } from '$lib/stores/db';

  const currentYear = new Date().getFullYear();

  function formatUpdated(ts: string): string {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Dubai'
      });
    } catch {
      return ts;
    }
  }
</script>

<footer class="mt-16 border-t border-gray-200 bg-white">
  <div class="max-w-7xl mx-auto px-6 py-8">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">

      <!-- Brand + attribution -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-navy tracking-wide">ADInteract</span>
          <span class="text-gray-300">·</span>
          <span class="text-xs text-gray-500">Abu Dhabi Property Transactions</span>
        </div>
        <p class="text-xs text-gray-400">
          Data sourced from the public dashboard of the
          <a
            href="https://adrec.gov.ae"
            target="_blank"
            rel="noopener noreferrer"
            class="text-brand-600 hover:text-brand-700 hover:underline font-medium"
          >
            Abu Dhabi Real Estate Centre (ADREC)
          </a>
          — updated daily. ADInteract is an independent platform and is not affiliated with,
          endorsed by, or officially connected to ADREC or any Abu Dhabi government entity.
        </p>
        <p class="text-[11px] text-gray-400">
          Data is derived from ADREC's public dashboard and has been processed for analysis
          (unit conversion, normalisation). Figures may differ from official ADREC records.
          For informational purposes only. Not financial or investment advice.
        </p>
      </div>

      <!-- Dataset stats + copyright -->
      <div class="flex flex-col items-start sm:items-end gap-1.5">
        {#if $metadata}
          <div class="flex items-center gap-1.5 text-xs text-gray-400">
            <svg class="h-3.5 w-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
            {$metadata.rowCount.toLocaleString()} transactions
            {#if $metadata.dateRange?.min && $metadata.dateRange?.max}
              · {new Date($metadata.dateRange.min).getFullYear()}–{new Date($metadata.dateRange.max).getFullYear()}
            {/if}
          </div>
          {#if $metadata.lastUpdated}
            <div class="flex items-center gap-1.5 text-xs text-gray-400">
              <svg class="h-3.5 w-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Last updated {formatUpdated($metadata.lastUpdated)}
            </div>
          {/if}
        {/if}
        <p class="text-[11px] text-gray-300">© {currentYear} Khee Lim. All rights reserved.</p>
      </div>

    </div>
  </div>
</footer>
