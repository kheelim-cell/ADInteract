<script lang="ts">
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { metadata, rentalMetadata } from '$lib/stores/db';
  import { user, isAuthenticated, openSignIn, signOut } from '$lib/stores/auth';
  import { supabaseEnabled } from '$lib/supabase';

  let { lastUpdated = '' } = $props();

  let avatarMenuOpen = $state(false);

  function getInitials(u: typeof $user): string {
    if (!u) return '?';
    const name = u.user_metadata?.full_name as string | undefined;
    if (name) return name.split(' ').slice(0, 2).map((n) => n[0]).join('').toUpperCase();
    const email = u.email ?? '';
    return email[0]?.toUpperCase() ?? '?';
  }

  function getDisplayName(u: typeof $user): string {
    if (!u) return '';
    return (u.user_metadata?.full_name as string | undefined) ??
      u.user_metadata?.whatsapp_number ??
      u.email ??
      'User';
  }

  let isRentalPage   = $derived($page.url.pathname.includes('/rental'));
  let isInvestorPage = $derived($page.url.pathname.includes('/investors'));
  let hasRental      = $derived($rentalMetadata !== null);

  function formatUpdated(ts: string): string {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Dubai'
      }) + ' GST';
    } catch {
      return ts;
    }
  }

  function dataRange(min: string, max: string): string {
    const fmt = (d: string) => new Date(d).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
    return `${fmt(min)} – ${fmt(max)}`;
  }
</script>

<!-- Gold accent line at very top -->
<div class="h-0.5 w-full bg-gradient-to-r from-transparent via-brand-500 to-transparent"></div>

<header class="bg-gradient-to-b from-[#1e4d3a] to-navy border-b border-white/5">
  <div class="max-w-7xl mx-auto px-4 sm:px-6">

    <!-- Main row: logo | [desktop: tabs] | right items -->
    <div class="flex items-center justify-between gap-3 sm:gap-6 py-3 sm:py-4">

      <!-- Left: Logo + brand -->
      <div class="flex items-center gap-2 sm:gap-4 min-w-0">

        <!-- Skyline silhouette icon -->
        <div class="flex-shrink-0 flex items-center justify-center w-9 h-8 sm:w-12 sm:h-11 rounded-xl bg-white/8 border border-brand-500/30 shadow-inner">
          <svg class="w-7 h-5 sm:w-10 sm:h-8 text-brand-400" viewBox="0 0 80 40" fill="currentColor">
            <path d="M 0,38 L 0,30 L 5,30 L 5,26 L 10,26 L 10,30 L 11,30 L 11,25 Q 15.5,18 20,25 L 20,30 L 21,30 L 21,21 L 23,21 L 23,13 L 25,3 L 27,13 L 27,21 L 29,21 L 29,17 L 31,17 L 31,7 L 32,7 L 32,2 L 32.5,0 L 33,2 L 33,7 L 34,7 L 34,17 L 35,17 L 35,21 L 37,21 L 37,13 L 39.5,7 L 42,13 L 42,21 L 44,21 L 44,16 L 47,13 L 50,16 L 50,21 L 52,21 L 52,27 L 57,27 L 57,23 L 64,23 L 64,27 L 72,27 L 72,31 L 80,31 L 80,38 Z"/>
          </svg>
        </div>

        <!-- Text logo -->
        <div class="min-w-0">
          <div class="flex items-center gap-2.5">
            <h1 class="leading-none">
              <span class="text-[26px] font-extrabold text-brand-400 tracking-tight">AD</span><span class="text-[26px] font-light italic text-brand-400 tracking-tight">INTERACT</span>
            </h1>
            <span class="hidden sm:inline-flex items-center gap-1 rounded-full bg-white/8 border border-white/15 px-2 py-0.5 text-[10px] font-semibold text-white/40 tracking-wide">
              Data: ADREC
            </span>
          </div>
          <p class="text-[10px] text-white/35 font-semibold tracking-widest uppercase mt-1">
            Abu Dhabi Property Transactions
          </p>
        </div>
      </div>

      <!-- Centre: Sales / Rental / Investors tabs — desktop only -->
      {#if hasRental}
        <nav class="hidden sm:flex items-center rounded-full bg-white/10 border border-white/25 p-1 gap-1">
          <a
            href="{base}/"
            class="rounded-full w-28 py-2 text-sm font-bold text-center transition-colors tracking-wide
                   {!isRentalPage && !isInvestorPage ? 'bg-brand-500 text-white shadow-md' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Sales
          </a>
          <a
            href="{base}/rental"
            class="rounded-full w-28 py-2 text-sm font-bold text-center transition-colors tracking-wide
                   {isRentalPage ? 'bg-brand-500 text-white shadow-md' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Rental
          </a>
          <a
            href="{base}/investors"
            class="rounded-full w-28 py-2 text-sm font-bold text-center transition-colors tracking-wide
                   {isInvestorPage ? 'bg-emerald-600 text-white shadow-md' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Investors
          </a>
        </nav>
      {/if}

      <!-- Right: avatar + dataset stats -->
      <div class="flex items-center gap-3 flex-shrink-0">

        <!-- User avatar (only when signed in) -->
        {#if supabaseEnabled && $isAuthenticated && $user}
          <div class="relative">
            <button
              type="button"
              onclick={() => (avatarMenuOpen = !avatarMenuOpen)}
              class="flex items-center gap-2 rounded-full bg-white/10 border border-white/20 hover:bg-white/20 px-2 py-1.5 transition-colors"
            >
              <span class="flex items-center justify-center w-7 h-7 rounded-full bg-brand-500 text-white text-xs font-bold">
                {getInitials($user)}
              </span>
              <span class="hidden sm:block text-xs font-semibold text-white/80 max-w-[120px] truncate">
                {getDisplayName($user)}
              </span>
            </button>

            {#if avatarMenuOpen}
              <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
              <div
                class="absolute right-0 z-30 mt-2 w-44 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden"
                onclick={() => (avatarMenuOpen = false)}
              >
                <div class="px-4 py-3 border-b border-gray-100">
                  <p class="text-xs text-gray-400">Signed in as</p>
                  <p class="text-sm font-semibold text-gray-900 truncate">{getDisplayName($user)}</p>
                </div>
                <button
                  type="button"
                  onclick={signOut}
                  class="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                  </svg>
                  Sign out
                </button>
              </div>
            {/if}
          </div>
        {/if}

        <!-- Dataset stats + last updated (desktop only) -->
        <div class="hidden md:flex flex-col items-end gap-1">
          {#if $metadata}
            <div class="flex items-center gap-1.5 text-[11px] font-semibold text-white/60">
              <svg class="h-3.5 w-3.5 text-brand-500/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694 4.125-8.25 4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
              </svg>
              <span class="text-white/80">{$metadata.rowCount.toLocaleString()}</span> transactions
              {#if $metadata.dateRange?.min && $metadata.dateRange?.max}
                <span class="text-white/30">·</span>
                <span>{dataRange($metadata.dateRange.min, $metadata.dateRange.max)}</span>
              {/if}
            </div>
          {/if}
          {#if lastUpdated}
            <div class="flex items-center gap-1.5 text-white/30 text-[10px] font-medium">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Updated {formatUpdated(lastUpdated)}
            </div>
          {/if}
        </div>

      </div>
    </div>

    <!-- Mobile-only second row: Sales / Rental / Investors tabs centred -->
    {#if hasRental}
      <div class="sm:hidden flex justify-center pb-3">
        <nav class="flex items-center rounded-full bg-white/10 border border-white/25 p-0.5 gap-0.5">
          <a
            href="{base}/"
            class="rounded-full w-[5.5rem] py-1.5 text-xs font-semibold text-center transition-colors
                   {!isRentalPage && !isInvestorPage ? 'bg-brand-500 text-white shadow-sm' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Sales
          </a>
          <a
            href="{base}/rental"
            class="rounded-full w-[5.5rem] py-1.5 text-xs font-semibold text-center transition-colors
                   {isRentalPage ? 'bg-brand-500 text-white shadow-sm' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Rental
          </a>
          <a
            href="{base}/investors"
            class="rounded-full w-[5.5rem] py-1.5 text-xs font-semibold text-center transition-colors
                   {isInvestorPage ? 'bg-emerald-600 text-white shadow-sm' : 'text-white/60 hover:text-white hover:bg-white/10'}"
          >
            Investors
          </a>
        </nav>
      </div>
    {/if}

  </div>
</header>
