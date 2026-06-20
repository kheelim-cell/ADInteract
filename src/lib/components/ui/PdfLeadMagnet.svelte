<script lang="ts">
  import { base } from '$app/paths';

  // Pre-generated server-side guide (scripts/generate_price_guide.py),
  // refreshed alongside the daily data pipeline. Served straight from
  // static/data/ — not built client-side.
  const PDF_PATH = `${base}/data/price-guide-2026.pdf`;

  let email = $state('');
  let status = $state<'idle' | 'fetching' | 'emailing' | 'success' | 'error'>('idle');
  let errorMsg = $state('');

  async function submit(e: Event) {
    e.preventDefault();
    if (!email || status !== 'idle') return;

    const emailTrimmed = email.trim().toLowerCase();
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(emailTrimmed)) {
      errorMsg = 'Please enter a valid email address.';
      return;
    }

    try {
      status = 'fetching';
      errorMsg = '';

      const res = await fetch(PDF_PATH);
      if (!res.ok) throw new Error(`PDF fetch failed: ${res.status}`);
      const blob = await res.blob();

      // Store email in Supabase
      status = 'emailing';
      try {
        const { supabase } = await import('$lib/supabase');
        if (supabase) {
          const row = {
            email: emailTrimmed,
            source: 'pdf_guide',
            district: null as string | null,
          };
          const { error } = await supabase.from('email_subscribers').insert(row);
          // 23505 = duplicate email (already subscribed) — still deliver the PDF
          if (error && error.code !== '23505') {
            console.warn('Email save error:', error.message);
          }
        }
      } catch {
        /* Supabase optional — still deliver PDF */
      }

      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'AD Interact - ABU DHABI PROPERTY INVESTOR GUIDE 2026.pdf';
      a.click();
      URL.revokeObjectURL(url);

      status = 'success';
    } catch (err) {
      status = 'error';
      errorMsg = 'Failed to download guide. Please try again.';
      console.error(err);
    }
  }
</script>

<div class="rounded-2xl border border-brand-100 bg-gradient-to-br from-[#0F2B1F]/5 to-white px-5 py-5">
  {#if status === 'success'}
    <div class="flex items-start gap-3">
      <div class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-full bg-brand-100">
        <svg class="w-5 h-5 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div>
        <p class="text-sm font-semibold text-gray-900">PDF downloading now.</p>
        <p class="text-xs text-gray-500 mt-0.5">You'll also receive weekly market updates.</p>
      </div>
    </div>
  {:else}
    <div class="flex items-center gap-2 mb-3">
      <svg class="w-5 h-5 text-brand-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
      <span class="text-sm font-bold text-gray-900">Free Abu Dhabi Investment Guide 2026</span>
    </div>
    <p class="text-xs text-gray-500 mb-4 leading-relaxed">
      Median prices, district deep-dives and investment scores for Abu Dhabi's top districts.
      Official ADREC data.
    </p>

    <form onsubmit={submit} class="flex flex-col sm:flex-row gap-2">
      <input
        type="email"
        bind:value={email}
        placeholder="your@email.com"
        required
        disabled={status !== 'idle'}
        class="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={status !== 'idle'}
        class="flex-shrink-0 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 px-4 py-2 text-sm font-semibold text-white transition-colors flex items-center gap-1.5"
      >
        {#if status === 'fetching'}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Preparing…
        {:else if status === 'emailing'}
          Saving…
        {:else}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Download free guide
        {/if}
      </button>
    </form>

    {#if errorMsg}
      <p class="mt-2 text-xs text-red-600">{errorMsg}</p>
    {:else}
      <p class="mt-2 text-[10px] text-gray-400">No spam. Unsubscribe anytime.</p>
    {/if}
  {/if}
</div>
