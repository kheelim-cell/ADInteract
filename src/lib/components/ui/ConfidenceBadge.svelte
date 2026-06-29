<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';

  let { count, showLabel = false }: { count: number; showLabel?: boolean } = $props();

  function getLevel(n: number) {
    if (n >= 100) return { label: m.confidence_high(), color: '#16a34a', icon: '●' };
    if (n >= 30)  return { label: m.confidence_moderate(), color: '#d97706', icon: '◕' };
    if (n >= 10)  return { label: m.confidence_limited(), color: '#dc2626', icon: '◑' };
    return { label: m.confidence_insufficient(), color: '#6b7280', icon: '○' };
  }

  let level = $derived(getLevel(count));
  let formatted = $derived(count.toLocaleString('en-AE'));
</script>

<span
  class="inline-flex items-center gap-1 text-xs font-medium leading-none"
  style="color: {level.color}"
  title={m.confidence_title({ label: level.label, count: formatted })}
>
  <span aria-hidden="true">{level.icon}</span>
  <span>{formatted} {m.confidence_sales_suffix()}</span>
  {#if showLabel}
    <span class="opacity-70">· {level.label}</span>
  {/if}
</span>
