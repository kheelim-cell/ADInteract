<script lang="ts">
  let { district = null }: { district?: string | null } = $props();

  let email = $state('');
  let status = $state<'idle' | 'loading' | 'success' | 'error'>('idle');
  let errorMsg = $state('');

  async function submit(e: Event) {
    e.preventDefault();
    if (!email || status === 'loading') return;

    status = 'loading';
    errorMsg = '';

    try {
      const { supabase } = await import('$lib/supabase');
      if (!supabase) throw new Error('not_configured');

      // RLS only allows INSERT for anon — a duplicate email comes back as
      // 23505, which is still a successful subscribe from the user's view.
      const row = {
        email: email.trim().toLowerCase(),
        district,
        source: window.location.pathname + window.location.search
      };
      let { error } = await supabase.from('email_subscribers').insert(row);

      // 42703: district/source columns not migrated yet — store the email anyway
      if (error && error.code === '42703') {
        ({ error } = await supabase.from('email_subscribers').insert({ email: row.email }));
      }
      if (error && error.code !== '23505') throw error;

      const w = window as unknown as { gtag?: (...args: unknown[]) => void };
      w.gtag?.('event', 'sign_up', { method: 'email_capture', item_id: district ?? 'home' });
      status = 'success';
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes('not_configured') || msg.includes('does not exist') || msg.includes('42P01')) {
        status = 'success'; // degrade gracefully if table/config missing
      } else {
        status = 'error';
        errorMsg = 'Something went wrong. Please try again.';
      }
    }
  }
</script>

<div class="mt-8 rounded-2xl border border-brand-100 bg-gradient-to-r from-[#1e4d3a]/5 to-brand-50/30 px-5 py-5">
  {#if status === 'success'}
    <div class="flex items-center gap-3">
      <span class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-full bg-brand-100">
        <svg class="w-5 h-5 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </span>
      <div>
        <p class="text-sm font-semibold text-gray-900">You're in.</p>
        <p class="text-xs text-gray-500">Weekly Abu Dhabi market updates will land in your inbox every Monday.</p>
      </div>
    </div>
  {:else}
    <div class="flex flex-col sm:flex-row sm:items-center gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <svg class="w-4 h-4 text-brand-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
          </svg>
          <span class="text-sm font-bold text-gray-900">Get the weekly Abu Dhabi market update</span>
        </div>
        <p class="text-xs text-gray-500">Top transactions, price moves, and yield shifts — every Monday. Free.</p>
      </div>

      <form onsubmit={submit} class="flex gap-2 flex-shrink-0 w-full sm:w-auto">
        <input
          type="email"
          bind:value={email}
          placeholder="your@email.com"
          required
          class="flex-1 min-w-0 sm:flex-none sm:w-52 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={status === 'loading'}
          class="flex-shrink-0 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 px-4 py-2 text-sm font-semibold text-white transition-colors"
        >
          {status === 'loading' ? 'Subscribing…' : 'Subscribe'}
        </button>
      </form>
    </div>

    {#if errorMsg}
      <p class="mt-2 text-xs text-red-600">{errorMsg}</p>
    {/if}
  {/if}
</div>
