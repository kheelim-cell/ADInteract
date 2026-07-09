<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';
  import ShareToolButton from '$lib/components/ui/ShareToolButton.svelte';

  interface DeveloperRow {
    developer_name: string;
    project_count: number;
    total_tx: number;
    psf_premium_pct: number | null;
    secondary_market_ratio: number | null;
    pipeline_velocity: number | null;
    composite_score: number;
  }

  let data = $state<DeveloperRow[]>([]);
  let loading = $state(true);
  let error = $state('');

  async function load() {
    try {
      const res = await fetch('/data/developer_scores.json');
      if (!res.ok) throw new Error('not found');
      const json = await res.json();
      data = (json as DeveloperRow[]).sort((a, b) => b.composite_score - a.composite_score);
    } catch {
      error = m.developers_no_data();
    } finally {
      loading = false;
    }
  }

  load();

  function scoreColor(s: number) {
    if (s >= 70) return { bar: 'bg-emerald-500', text: 'text-emerald-700' };
    if (s >= 40) return { bar: 'bg-amber-400',   text: 'text-amber-700'   };
    return              { bar: 'bg-red-400',       text: 'text-red-600'    };
  }

  function fmt(n: number) { return n.toLocaleString('en-AE'); }
  function fmtPct(n: number | null) { return n == null ? '—' : n.toFixed(1) + '%'; }
</script>

<svelte:head>
  <title>{m.seo_developers_title()}</title>
  <meta name="description" content={m.seo_developers_description()} />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <h1 class="text-xl font-bold text-gray-900 mb-1">{m.developers_page_title()}</h1>
      <p class="text-sm text-gray-500">{m.developers_page_subtitle()}</p>
    </div>
    <ShareToolButton />
  </div>

  {#if loading}
    <div class="flex items-center gap-2 text-sm text-gray-500 py-8">
      <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
      </svg>
      {m.developers_loading()}
    </div>
  {:else if error}
    <div class="rounded-xl border border-amber-200 bg-amber-50 p-6 text-center">
      <p class="text-sm text-amber-700">{error}</p>
      <p class="text-xs text-amber-500 mt-1">Run <code class="font-mono bg-amber-100 px-1 rounded">python scripts/compute_developer_scores.py</code> to generate the data.</p>
    </div>
  {:else}
    <div class="rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-4 py-3 text-start text-[11px] font-semibold text-gray-500 uppercase tracking-wider w-10">{m.developers_th_rank()}</th>
            <th class="px-4 py-3 text-start text-[11px] font-semibold text-gray-500 uppercase tracking-wider">{m.developers_th_developer()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">{m.developers_th_projects()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">{m.developers_th_total_sales()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">{m.developers_th_psf_premium()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">{m.developers_th_secondary()}</th>
            <th class="px-4 py-3 text-end text-[11px] font-semibold text-gray-500 uppercase tracking-wider">{m.developers_score_label()}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          {#each data as dev, i}
            {@const colors = scoreColor(dev.composite_score)}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-gray-400 font-semibold text-center text-xs">{i + 1}</td>
              <td class="px-4 py-3">
                <p class="font-semibold text-gray-900">{dev.developer_name}</p>
              </td>
              <td class="px-4 py-3 text-end text-gray-600 hidden sm:table-cell">{dev.project_count}</td>
              <td class="px-4 py-3 text-end text-gray-600 hidden md:table-cell">{fmt(dev.total_tx)}</td>
              <td class="px-4 py-3 text-end hidden lg:table-cell">
                <span class="{dev.psf_premium_pct != null && dev.psf_premium_pct > 0 ? 'text-emerald-700' : 'text-red-500'} font-semibold text-xs">
                  {dev.psf_premium_pct != null && dev.psf_premium_pct > 0 ? '+' : ''}{fmtPct(dev.psf_premium_pct)}
                </span>
              </td>
              <td class="px-4 py-3 text-end text-gray-600 text-xs hidden lg:table-cell">{fmtPct(dev.secondary_market_ratio)}</td>
              <td class="px-4 py-3 text-end">
                <div class="flex items-center justify-end gap-2">
                  <div class="w-16 h-1.5 rounded-full bg-gray-100 overflow-hidden hidden sm:block">
                    <div class="h-full rounded-full {colors.bar}" style="width: {dev.composite_score}%"></div>
                  </div>
                  <span class="font-bold text-sm {colors.text}">{Math.round(dev.composite_score)}</span>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
      <div class="px-4 py-3 border-t border-gray-100 bg-gray-50">
        <p class="text-[10px] text-gray-400">{m.developers_score_method()}</p>
      </div>
    </div>
  {/if}
</div>
