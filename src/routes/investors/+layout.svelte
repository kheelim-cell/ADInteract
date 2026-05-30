<script lang="ts">
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { goto } from '$app/navigation';
  import { metadata } from '$lib/stores/db';

  let { children } = $props();

  const thisCalendarYear = new Date().getFullYear();

  let salesYear = $derived.by(() => {
    const maxStr = $metadata?.dateRange?.max;
    if (!maxStr) return thisCalendarYear - 1;
    const maxDataYear = new Date(maxStr).getFullYear();
    return maxDataYear >= thisCalendarYear ? thisCalendarYear - 1 : maxDataYear;
  });

  let prevSalesYear = $derived(salesYear - 1);

  const NAV_ITEMS = [
    {
      href: `${base}/investors/calculator`,
      label: 'Investment ROI Calculator',
      description: 'Model net yield, capital gain CAGR, and total ROI before you commit — for both ready and off-plan properties. Auto-populated with live ADREC rent and appreciation data.',
      iconPath: 'M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V13.5Zm0 2.25h.008v.008H8.25v-.008Zm2.25-4.5h.008v.008H10.5v-.008Zm0 2.25h.008v.008H10.5V13.5Zm0 2.25h.008v.008H10.5v-.008Zm2.25-4.5h.008v.008H12.75v-.008Zm0 2.25h.008v.008H12.75V13.5Zm0 2.25h.008v.008H12.75v-.008ZM6.75 6.75h10.5v10.5H6.75V6.75ZM6 3.75A2.25 2.25 0 0 1 8.25 1.5h7.5A2.25 2.25 0 0 1 18 3.75v.75H6v-.75Z',
    },
    {
      href: `${base}/investors/price-growth`,
      label: 'Price Growth',
      description: 'Year-on-year appreciation leaders ranked by median AED/sqft across districts, sale projects, and rental projects — sourced directly from ADREC registered transactions.',
      iconPath: 'M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941',
    },
    {
      href: `${base}/investors/rental-yield`,
      label: 'Rental Yield',
      description: 'Gross rental yield benchmarks by community: registered rents divided by sale prices. Use this to shortlist high-yield areas before running a detailed calculator scenario.',
      iconPath: 'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z',
    },
    {
      href: `${base}/investors/service-charges`,
      label: 'Service Charges',
      description: 'Annual ADREC-registered service charge rates by project in AED/sqft. This recurring cost directly erodes net rental yield and must be verified before any purchase decision.',
      iconPath: 'M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z',
    },
    {
      href: `${base}/investors/faqs`,
      label: 'Investor FAQs',
      description: 'Key questions answered: foreign ownership rules, transaction costs, Golden Visa eligibility, escrow protection, taxes, and Abu Dhabi vs Dubai cost comparison.',
      iconPath: 'M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z',
    },
  ];

  let hoveredNav = $state<string | null>(null);

  let currentPath = $derived($page.url.pathname);
</script>

<!-- ── Hero ────────────────────────────────────────────────────────────────── -->
<div class="bg-gradient-to-b from-[#0a2318] to-[#0e2d45] border-b border-white/5">
  <div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-4 sm:py-5">
    <div class="flex items-center gap-3">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400 tracking-wider uppercase flex-shrink-0">
        <svg class="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
        </svg>
        Investor Intelligence
      </span>
      <h2 class="text-base sm:text-lg font-bold text-white leading-tight">
        Abu Dhabi Property Investment Insights
      </h2>
      <p class="hidden sm:block text-xs text-white/40 border-l border-white/10 pl-3 ml-1">
        ADREC transaction data · {prevSalesYear}–{salesYear}
      </p>
    </div>
  </div>
</div>

<!-- ── Nav strip ────────────────────────────────────────────────────────────── -->
<div class="bg-[#071913] border-b border-white/8">
  <div class="max-w-[1400px] mx-auto px-4 sm:px-8">

    <!-- Mobile nav dropdown (hidden on sm+) -->
    <div class="block sm:hidden py-3">
      <div class="relative">
        <select
          onchange={(e) => goto((e.currentTarget as HTMLSelectElement).value)}
          class="w-full bg-[#0a1a10] border border-white/15 rounded-lg px-3 py-2.5 text-sm font-semibold text-white appearance-none cursor-pointer focus:outline-none focus:border-emerald-500/40"
        >
          {#each NAV_ITEMS as item}
            <option value={item.href} selected={currentPath === item.href || currentPath.startsWith(item.href + '/')}>
              {item.label}
            </option>
          {/each}
        </select>
        <svg class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </div>
      {@const activeNavItem = NAV_ITEMS.find(n => currentPath === n.href || currentPath.startsWith(n.href + '/'))}
      {#if activeNavItem}
        <p class="mt-2 text-[11px] leading-snug text-white/40 px-1">
          {activeNavItem.description}
        </p>
      {/if}
    </div>

    <!-- Tab buttons (desktop: sm+) -->
    <div class="hidden sm:flex gap-0.5 pt-3 overflow-x-auto scrollbar-none">
      {#each NAV_ITEMS as item}
        {@const isActive = currentPath === item.href || currentPath.startsWith(item.href + '/')}
        <a
          href={item.href}
          onmouseenter={() => { hoveredNav = item.href; }}
          onmouseleave={() => { hoveredNav = null; }}
          class="flex-shrink-0 inline-flex items-center gap-2 px-5 py-2.5 rounded-t-lg text-sm font-semibold border-b-2 transition-all duration-150 no-underline
            {isActive || hoveredNav === item.href
              ? 'text-emerald-300 border-emerald-400 bg-emerald-500/8'
              : 'text-white/40 border-transparent hover:text-white/65 hover:bg-white/4'}"
        >
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d={item.iconPath} />
          </svg>
          {item.label}
          <svg class="w-3 h-3 flex-shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </a>
      {/each}
    </div>

    <!-- Description strip (desktop: sm+) -->
    <div class="hidden sm:flex h-9 items-center">
      {#if hoveredNav}
        {@const item = NAV_ITEMS.find(n => n.href === hoveredNav)}
        {#if item}
          <p class="text-[11px] leading-snug text-white/50">
            <span class="font-semibold text-emerald-400">{item.label}:</span>
            {' '}{item.description}
          </p>
        {/if}
      {:else}
        <p class="text-[11px] text-white/20">Hover a section to learn more · click to navigate</p>
      {/if}
    </div>

  </div>
</div>

<!-- ── Page content ─────────────────────────────────────────────────────────── -->
{@render children()}
