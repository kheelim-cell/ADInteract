<script lang="ts">
  import { base } from '$app/paths';
  import { m } from '$lib/paraglide/messages.js';
  import { watchlist, removeItem, clearAll } from '$lib/stores/watchlist';

  let deals    = $derived($watchlist.filter(i => i.type === 'deal'));
  let projects = $derived($watchlist.filter(i => i.type === 'project'));

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleDateString('en-AE', { day: 'numeric', month: 'short', year: 'numeric' });
  }
</script>

<svelte:head>
  <title>{m.watchlist_page_title()} — ADInteract</title>
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8">
  <div class="flex items-center justify-between gap-4 mb-6">
    <div>
      <h1 class="text-xl font-bold text-gray-900 mb-1">{m.watchlist_page_title()}</h1>
      <p class="text-sm text-gray-500">{m.watchlist_page_subtitle()}</p>
    </div>
    {#if $watchlist.length > 0}
      <button
        type="button"
        onclick={clearAll}
        class="text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
      >
        {m.watchlist_clear_all()}
      </button>
    {/if}
  </div>

  {#if $watchlist.length === 0}
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-100">
        <svg class="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
        </svg>
      </div>
      <h2 class="text-base font-bold text-gray-700 mb-2">{m.watchlist_empty_title()}</h2>
      <p class="text-sm text-gray-400 max-w-sm">{m.watchlist_empty_sub()}</p>
      <a href="{base}/investors/projects" class="mt-6 inline-flex items-center gap-1.5 rounded-full bg-emerald-600 text-white px-5 py-2 text-sm font-semibold hover:bg-emerald-700 transition-colors">
        {m.projects_page_title()} →
      </a>
    </div>
  {:else}
    <div class="space-y-8">

      <!-- Projects -->
      {#if projects.length > 0}
        <section>
          <h2 class="text-sm font-bold text-gray-600 uppercase tracking-wider mb-3">{m.watchlist_section_projects()}</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {#each projects as item}
              {#if item.type === 'project'}
                <div class="rounded-xl border border-gray-200 bg-white p-4 flex flex-col gap-2">
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <p class="text-sm font-semibold text-gray-900 leading-snug">{item.project_name}</p>
                      <p class="text-xs text-gray-400">{item.district}</p>
                    </div>
                    <button
                      type="button"
                      onclick={() => removeItem(item.id)}
                      class="text-xs text-red-400 hover:text-red-600 flex-shrink-0"
                    >{m.watchlist_remove()}</button>
                  </div>
                  <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
                    <span class="text-[10px] text-gray-400">{m.watchlist_added({ date: fmtDate(item.added_at) })}</span>
                    <a
                      href="{base}/project/{encodeURIComponent(item.project_name)}"
                      class="text-xs font-semibold text-emerald-600 hover:text-emerald-800"
                    >{m.watchlist_view_project()}</a>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </section>
      {/if}

      <!-- Deals -->
      {#if deals.length > 0}
        <section>
          <h2 class="text-sm font-bold text-gray-600 uppercase tracking-wider mb-3">{m.watchlist_section_deals()}</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {#each deals as item}
              {#if item.type === 'deal'}
                <div class="rounded-xl border border-gray-200 bg-white p-4 flex flex-col gap-2">
                  <div class="flex items-start justify-between gap-2">
                    <p class="text-sm font-semibold text-gray-900 leading-snug">{item.label}</p>
                    <button
                      type="button"
                      onclick={() => removeItem(item.id)}
                      class="text-xs text-red-400 hover:text-red-600 flex-shrink-0"
                    >{m.watchlist_remove()}</button>
                  </div>
                  <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
                    <span class="text-[10px] text-gray-400">{m.watchlist_added({ date: fmtDate(item.added_at) })}</span>
                    <a
                      href={item.url}
                      class="text-xs font-semibold text-blue-600 hover:text-blue-800"
                    >{m.watchlist_open_deal()}</a>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </section>
      {/if}
    </div>
  {/if}
</div>
