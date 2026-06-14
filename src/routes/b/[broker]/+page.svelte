<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const { broker, brokerDistricts } = data;

  let copied = $state(false);

  function initials(name: string) {
    return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  }

  async function copyLink() {
    await navigator.clipboard.writeText(window.location.href);
    copied = true;
    setTimeout(() => { copied = false; }, 2000);
  }

  function shareWhatsApp() {
    const text = `Abu Dhabi property data — ${broker.display_name}: ${window.location.href}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
  }

  onMount(() => {
    import('$lib/supabase').then(({ supabase }) => {
      supabase?.rpc('increment_broker_visit', { broker_slug: broker.slug });
    });
  });
</script>

<svelte:head>
  <title>{broker.display_name} — Abu Dhabi Property Data | ADInteract</title>
  <meta name="description" content="{broker.bio ?? `ADREC-verified Abu Dhabi property transactions curated by ${broker.display_name}. Real closing prices, updated daily. Free.`}" />
  <meta property="og:title" content="{broker.display_name} — Abu Dhabi Property Data" />
  <meta property="og:description" content="96,847 ADREC-verified transactions. Real closing prices, not listings. Free." />
  <meta property="og:url" content="https://adinteract.co/b/{broker.slug}" />
</svelte:head>

<div class="min-h-screen bg-white">

  <!-- Nav -->
  <nav class="bg-[#0a2318] px-6 py-3 flex items-center justify-between sticky top-0 z-10">
    <a href="/" class="flex items-baseline gap-1">
      <span class="text-[#dfb83c] font-black text-base tracking-wide">AD</span>
      <span class="text-[#C8A951] font-normal italic text-[10px] tracking-widest">INTERACT</span>
    </a>
    <div class="hidden sm:flex items-center gap-6">
      <a href="/" class="text-white/40 text-xs hover:text-white/70 transition-colors">Districts</a>
      <a href="/project" class="text-white/40 text-xs hover:text-white/70 transition-colors">Projects</a>
      <a href="/" class="text-white/40 text-xs hover:text-white/70 transition-colors">Market Pulse</a>
    </div>
  </nav>

  <!-- Broker hero -->
  <div class="border-b border-gray-100 bg-white px-6 py-6">
    <div class="max-w-3xl mx-auto flex gap-5 items-start">
      {#if broker.photo_url}
        <img
          src={broker.photo_url}
          alt={broker.display_name}
          class="w-20 h-20 rounded-full object-cover border-2 border-[#dfb83c] flex-shrink-0"
        />
      {:else}
        <div class="w-20 h-20 rounded-full bg-[#dfb83c]/15 border-2 border-[#dfb83c] flex items-center justify-center flex-shrink-0">
          <span class="text-[#dfb83c] font-black text-xl">{initials(broker.display_name)}</span>
        </div>
      {/if}

      <div class="flex-1 min-w-0">
        <p class="text-[#dfb83c] text-[10px] font-bold tracking-widest uppercase mb-1">Abu Dhabi Property Analyst</p>
        <h1 class="text-2xl font-black text-[#0a2318] leading-tight mb-1">{broker.display_name}</h1>
        {#if broker.agency}
          <p class="text-gray-400 text-sm mb-1">{broker.agency}</p>
        {/if}
        <p class="text-gray-500 text-sm mb-5 leading-relaxed">
          {broker.bio ?? 'ADREC-verified Abu Dhabi property data. Every number on this page is a closed deal — not a listing.'}
        </p>
        <div class="flex gap-3 flex-wrap">
          <button
            onclick={shareWhatsApp}
            class="bg-[#0a2318] text-[#dfb83c] text-xs font-bold px-4 py-2.5 rounded-lg hover:bg-[#0d2e1f] transition-colors"
          >
            Share with a client
          </button>
          <button
            onclick={copyLink}
            class="border border-[#0a2318] text-[#0a2318] text-xs font-bold px-4 py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {copied ? 'Copied!' : 'Copy link'}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Data source badge -->
  <div class="bg-[#f4f7f4] border-b border-[#e0e8e0] px-6 py-2.5">
    <div class="max-w-3xl mx-auto flex items-center gap-2 text-xs flex-wrap">
      <span class="text-gray-400">Data source:</span>
      <span class="font-bold text-[#0a2318]">Abu Dhabi Real Estate Centre (ADREC)</span>
      <span class="text-gray-400">· Updated daily · 96,847 transactions</span>
    </div>
  </div>

  <!-- Districts -->
  <div class="bg-gray-50 px-6 py-8">
    <div class="max-w-3xl mx-auto">

      {#if brokerDistricts.length > 0}
        <p class="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-5">Districts</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
          {#each brokerDistricts as d}
            <a
              href="/area/{d.slug}?utm_source=broker&utm_medium=vanity&utm_campaign={broker.slug}"
              class="block bg-white border border-gray-200 rounded-xl p-4 hover:border-[#dfb83c] hover:shadow-sm transition-all group"
            >
              <p class="text-xs font-bold text-[#0a2318] mb-2 leading-tight">{d.name}</p>
              <p class="text-2xl font-black text-[#dfb83c] leading-none">
                {d.median_psf ? Math.round(d.median_psf).toLocaleString() : '—'}
              </p>
              <p class="text-[9px] text-gray-400 mt-1 tracking-wide uppercase">AED / sqft median</p>
              <div class="h-px bg-gray-100 my-3"></div>
              <p class="text-xs text-gray-500">
                {d.tx_count_12m ? d.tx_count_12m.toLocaleString() : '—'} sales · 12 mo
              </p>
              <p class="text-[10px] text-[#0a2318] font-bold mt-2 group-hover:text-[#dfb83c] transition-colors">
                View district →
              </p>
            </a>
          {/each}
        </div>
      {/if}

      <div class="text-center">
        <a
          href="/?utm_source=broker&utm_medium=vanity&utm_campaign={broker.slug}"
          class="text-sm font-bold text-[#0a2318] border-b-2 border-[#dfb83c] pb-0.5 hover:text-[#dfb83c] transition-colors"
        >
          View all 40+ Abu Dhabi districts →
        </a>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="bg-[#0a2318] px-6 py-5">
    <div class="max-w-3xl mx-auto flex items-center justify-between gap-4">
      <div>
        <p class="text-white text-sm font-bold">adinteract.co/b/{broker.slug}</p>
        <p class="text-white/30 text-xs mt-0.5">Free ADREC data for your clients</p>
      </div>
      <button
        onclick={copyLink}
        class="flex-shrink-0 bg-[#dfb83c] text-[#0a2318] text-xs font-black px-5 py-2.5 rounded-lg hover:bg-[#c9a830] transition-colors"
      >
        {copied ? 'Copied!' : 'Copy link'}
      </button>
    </div>
  </div>

</div>
