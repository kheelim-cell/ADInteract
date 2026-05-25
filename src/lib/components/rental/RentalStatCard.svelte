<script lang="ts">
  let {
    label,
    value,
    sub = ''
  }: {
    label: string;
    value: string;
    sub?: string;
  } = $props();
</script>

<div class="stat-card flex flex-col gap-3">
  <span class="text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider sm:tracking-widest text-navy/40">
    {label}
  </span>
  <p class="text-2xl sm:text-3xl font-bold text-navy leading-none">{value}</p>
  {#if sub}
    <span class="text-xs text-navy/40 font-medium">{sub}</span>
  {/if}
</div>
