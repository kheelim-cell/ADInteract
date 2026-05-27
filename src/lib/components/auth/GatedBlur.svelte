<script lang="ts">
  import { getContext } from 'svelte';

  let { children }: { children: import('svelte').Snippet } = $props();

  const gatedCtx = getContext<{ get: () => boolean } | undefined>('gated-locked');
  let locked = $derived(gatedCtx?.get() ?? false);
</script>

<!-- Blur wrapper: apply blur-[2px] to charts/canvases when the parent GatedSection is locked -->
<div class={locked ? 'blur-[3px]' : ''}>
  {@render children()}
</div>
