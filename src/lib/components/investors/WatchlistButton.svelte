<script lang="ts">
  import { watchlist, addProject, removeItem } from '$lib/stores/watchlist';
  import { m } from '$lib/paraglide/messages.js';

  let {
    project_name,
    district = '',
    size = 'sm'
  }: { project_name: string; district?: string; size?: 'sm' | 'md' } = $props();

  const id = `project_${project_name}`;
  let saved = $derived($watchlist.some((i) => i.id === id));

  function toggle() {
    if (saved) removeItem(id);
    else addProject(project_name, district);
  }
</script>

<button
  type="button"
  onclick={toggle}
  title={saved ? m.watchlist_saved() : m.watchlist_save_project()}
  class="inline-flex items-center gap-1.5 rounded-lg border transition-all
    {size === 'md' ? 'px-3 py-2 text-sm' : 'px-2 py-1.5 text-xs'}
    {saved
      ? 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'
      : 'border-gray-200 bg-white text-gray-500 hover:border-amber-300 hover:text-amber-600'}"
>
  <svg
    class="{size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5'}"
    viewBox="0 0 24 24"
    stroke="currentColor"
    stroke-width="2"
    fill={saved ? 'currentColor' : 'none'}
  >
    <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
  </svg>
  {saved ? m.watchlist_saved() : m.watchlist_save_project()}
</button>
