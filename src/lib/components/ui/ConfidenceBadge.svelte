<script lang="ts">
  let { count, showLabel = false }: { count: number; showLabel?: boolean } = $props();

  function getLevel(n: number) {
    if (n >= 100) return { label: 'High confidence', color: '#16a34a', icon: '●' };
    if (n >= 30)  return { label: 'Moderate confidence', color: '#d97706', icon: '◕' };
    if (n >= 10)  return { label: 'Limited data', color: '#dc2626', icon: '◑' };
    return { label: 'Insufficient data', color: '#6b7280', icon: '○' };
  }

  let level = $derived(getLevel(count));
  let formatted = $derived(count.toLocaleString('en-AE'));
</script>

<span
  class="inline-flex items-center gap-1 text-xs font-medium leading-none"
  style="color: {level.color}"
  title="{level.label} — based on {formatted} ADREC registered transactions"
>
  <span aria-hidden="true">{level.icon}</span>
  <span>{formatted} sales</span>
  {#if showLabel}
    <span class="opacity-70">· {level.label}</span>
  {/if}
</span>
