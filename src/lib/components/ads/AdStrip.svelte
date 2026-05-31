<script lang="ts">
  /**
   * AdStrip — horizontal sponsored content strip.
   *
   * Shows 5 ad slots (one per category). Images and destination URLs are
   * intentionally left empty — fill them in when advertisers are onboarded.
   *
   * Usage:
   *   <AdStrip context="sales" />
   *   <AdStrip context="rental" />
   */

  type AdSlot = {
    id:       string;
    category: string;
    tagline:  string;
    // Populate when live:
    logoSrc:  string | null;  // absolute URL to advertiser logo
    href:     string | null;  // destination URL (use UTM-tagged link)
    cta:      string;         // button label
  };

  const SLOTS: AdSlot[] = [
    {
      id:       'developer',
      category: 'Developer',
      tagline:  'Showcase off-plan projects to active Abu Dhabi buyers',
      logoSrc:  null,
      href:     null,
      cta:      'View Projects',
    },
    {
      id:       'brokerage',
      category: 'Brokerage',
      tagline:  'Connect your agents with serious property seekers',
      logoSrc:  null,
      href:     null,
      cta:      'Find an Agent',
    },
    {
      id:       'snagging',
      category: 'Snagging Inspection',
      tagline:  'Reach buyers in the weeks before and after handover',
      logoSrc:  null,
      href:     null,
      cta:      'Book Inspection',
    },
    {
      id:       'furnishing',
      category: 'Furnishing',
      tagline:  'Target new homeowners planning their interiors',
      logoSrc:  null,
      href:     null,
      cta:      'Get a Quote',
    },
    {
      id:       'mortgage',
      category: 'Mortgage Advisory',
      tagline:  'Engage buyers at the moment of financial decision',
      logoSrc:  null,
      href:     null,
      cta:      'Calculate Rate',
    },
  ];

  let { context = 'sales' }: { context?: 'sales' | 'rental' } = $props();
</script>

<div class="mt-6" data-ad-context={context}>

  <!-- Label row -->
  <div class="flex items-center gap-3 mb-3">
    <span class="text-[10px] font-semibold tracking-widest text-gray-300 uppercase select-none">
      Sponsored
    </span>
    <div class="flex-1 h-px bg-gray-100"></div>
  </div>

  <!-- 5-column slot grid — 2 col on mobile, 3 on sm, 5 on lg -->
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
    {#each SLOTS as slot (slot.id)}
      <div
        class="group relative flex flex-col items-center text-center gap-3 rounded-xl border border-dashed border-gray-200 bg-white px-3 py-4 transition-colors hover:border-brand-300 hover:bg-brand-50/20"
      >

        <!-- Logo placeholder — swap for <img> when live -->
        <div
          class="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-50 ring-1 ring-gray-200 group-hover:bg-brand-50 transition-colors"
          aria-label="{slot.category} logo placeholder"
        >
          {#if slot.id === 'developer'}
            <!-- Building icon -->
            <svg class="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
            </svg>
          {:else if slot.id === 'brokerage'}
            <!-- Handshake / people icon -->
            <svg class="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
            </svg>
          {:else if slot.id === 'snagging'}
            <!-- Magnifying glass / clipboard icon -->
            <svg class="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
          {:else if slot.id === 'furnishing'}
            <!-- Home / interior icon -->
            <svg class="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
          {:else if slot.id === 'mortgage'}
            <!-- Currency / bank icon -->
            <svg class="h-6 w-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
            </svg>
          {/if}
        </div>

        <!-- Copy -->
        <div class="flex-1">
          <p class="text-xs font-semibold text-gray-700 leading-tight">{slot.category}</p>
          <p class="mt-1 text-[10px] leading-tight text-gray-400">{slot.tagline}</p>
        </div>

        <!-- CTA stub — href populated when advertiser is live -->
        <a
          href={slot.href ?? '#'}
          class="mt-auto inline-block rounded-full border border-brand-200 px-3 py-1 text-[10px] font-semibold text-brand-600 transition-colors hover:border-brand-400 hover:text-brand-700 group-hover:border-brand-400"
          onclick={slot.href ? undefined : (e: MouseEvent) => e.preventDefault()}
          rel="sponsored noopener"
        >
          {slot.cta}
        </a>

      </div>
    {/each}
  </div>

</div>
