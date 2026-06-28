<script lang="ts">
  import { metadata } from '$lib/stores/db';
  import { m } from '$lib/paraglide/messages.js';

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
          <span class="text-sm font-bold text-navy tracking-wide">{m.site_name()}</span>
          <span class="text-gray-300">·</span>
          <span class="text-xs text-gray-500">{m.site_tagline()}</span>
        </div>
        <p class="text-xs text-gray-400">
          {m.footer_data_source_prefix()}
          <a
            href="https://adrec.gov.ae"
            target="_blank"
            rel="noopener noreferrer"
            class="text-brand-600 hover:text-brand-700 hover:underline font-medium"
          >
            {m.footer_data_source_name()}
          </a>
          {m.footer_data_source_suffix()}
        </p>
        <p class="text-[11px] text-gray-400">
          {m.footer_disclaimer()}
        </p>
      </div>

      <!-- Dataset stats + copyright -->
      <div class="flex flex-col items-start sm:items-end gap-1.5">
        {#if $metadata}
          <div class="flex items-center gap-1.5 text-xs text-gray-400">
            <svg class="h-3.5 w-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
            {$metadata.rowCount.toLocaleString()} {m.footer_transactions_suffix()}
            {#if $metadata.dateRange?.min && $metadata.dateRange?.max}
              · {new Date($metadata.dateRange.min).getFullYear()}–{new Date($metadata.dateRange.max).getFullYear()}
            {/if}
          </div>
          {#if $metadata.lastUpdated}
            <div class="flex items-center gap-1.5 text-xs text-gray-400">
              <svg class="h-3.5 w-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {m.footer_last_updated_prefix({ date: formatUpdated($metadata.lastUpdated) })}
            </div>
          {/if}
        {/if}
        <p class="text-[11px] text-gray-300">{m.footer_copyright({ year: String(currentYear) })}</p>
      </div>

    </div>
  </div>
</footer>
