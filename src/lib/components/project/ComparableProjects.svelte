<script lang="ts">
  import { base } from '$app/paths';
  import type { ComparableProject } from '$lib/db/types';

  let { data = [] as ComparableProject[] } = $props();

  function pctLabel(diff: number): string {
    const abs = Math.abs(diff * 100).toFixed(1);
    return `${diff >= 0 ? '+' : '−'}${abs}%`;
  }
</script>

{#if data.length === 0}
  <div class="h-48 flex items-center justify-center">
    <p class="text-sm text-gray-400">No comparable projects found in same district</p>
  </div>
{:else}
  <div class="divide-y divide-gray-50">
    {#each data as project, i}
      <a
        href="{base}/project/{encodeURIComponent(project.project_name)}"
        class="flex items-center gap-3 py-3 -mx-1 px-1 rounded-lg hover:bg-gray-50/80 transition-colors group"
      >
        <!-- Rank bubble -->
        <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:bg-brand-100 group-hover:text-brand-600 transition-colors">
          {i + 1}
        </span>

        <!-- Name + deal count -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate group-hover:text-brand-700 transition-colors">
            {project.project_name}
          </p>
          <p class="text-xs text-gray-400">{project.volume.toLocaleString()} transactions</p>
        </div>

        <!-- Median rate + % diff vs current project -->
        <div class="text-right flex-shrink-0">
          <p class="text-sm font-semibold text-gray-900 tabular-nums">
            {Math.round(project.medianRate).toLocaleString()}
            <span class="text-xs text-gray-400 font-normal"> AED/sqft</span>
          </p>
          <span class="text-[11px] font-semibold tabular-nums {project.rateDiff >= 0 ? 'text-emerald-600' : 'text-red-500'}">
            {pctLabel(project.rateDiff)}
          </span>
        </div>

        <!-- Chevron -->
        <svg
          class="h-4 w-4 flex-shrink-0 text-gray-300 group-hover:text-brand-400 transition-colors"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </a>
    {/each}
  </div>
{/if}
