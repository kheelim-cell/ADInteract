<script lang="ts">
  import { getContext } from 'svelte';

  let { children }: { children: import('svelte').Snippet } = $props();

  const gatedCtx = getContext<{ get: () => boolean } | undefined>('gated-locked');
  let locked = $derived(gatedCtx?.get() ?? false);
</script>

<!-- Blur wrapper: apply blur-sm to charts/canvases when the parent GatedSection is locked -->
<div class={locked ? 'blur-sm' : ''}>
  {@render children()}
</div>
