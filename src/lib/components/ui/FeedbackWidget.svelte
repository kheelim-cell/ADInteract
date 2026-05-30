<script lang="ts">
  import { page } from '$app/stores';

  // Formspree endpoint — replace XXXXXXXX with your form ID from formspree.io
  const APPS_SCRIPT_URL = 'https://formspree.io/f/XXXXXXXX';

  type FeedbackType = 'bug' | 'feedback' | 'other';

  let isOpen = $state(false);
  let submitted = $state(false);
  let submitting = $state(false);
  let error = $state('');

  let feedbackType = $state<FeedbackType>('feedback');
  let message = $state('');
  let email = $state('');

  function open() {
    isOpen = true;
    submitted = false;
    error = '';
    message = '';
    email = '';
    feedbackType = 'feedback';
  }

  function close() {
    isOpen = false;
  }

  async function submit() {
    if (!message.trim()) return;
    submitting = true;
    error = '';

    try {
      const body: Record<string, string> = {
        type: feedbackType,
        message: message.trim(),
        page: $page.url.href,
        userAgent: navigator.userAgent,
      };
      if (email.trim()) body.email = email.trim();

      const res = await fetch(APPS_SCRIPT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      submitted = true;
    } catch {
      error = 'Failed to send. Please try again.';
    } finally {
      submitting = false;
    }
  }

  const TYPE_OPTIONS: { value: FeedbackType; label: string; icon: string }[] = [
    { value: 'bug',      label: 'Bug',      icon: '🐛' },
    { value: 'feedback', label: 'Feedback', icon: '💡' },
    { value: 'other',    label: 'Other',    icon: '💬' },
  ];
</script>

<!-- Floating trigger button -->
{#if !isOpen}
  <button
    onclick={open}
    aria-label="Share feedback"
    class="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-[#0a2318] text-white text-sm font-semibold px-4 py-3 shadow-lg hover:bg-[#143524] transition-all duration-200 hover:scale-105 active:scale-95"
  >
    <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 0 1 .778-.332 48.294 48.294 0 0 0 5.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
    </svg>
    <span>Feedback</span>
  </button>
{/if}

<!-- Modal overlay -->
{#if isOpen}
  <!-- Backdrop -->
  <button
    class="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
    onclick={close}
    aria-label="Close feedback"
  ></button>

  <!-- Panel -->
  <div
    class="fixed bottom-6 right-6 z-50 w-[340px] rounded-2xl bg-white shadow-2xl border border-gray-100 overflow-hidden"
    role="dialog"
    aria-modal="true"
    aria-label="Feedback form"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 bg-[#0a2318]">
      <div>
        <p class="text-white font-semibold text-sm">Share your feedback</p>
        <p class="text-white/50 text-xs mt-0.5">Bugs, suggestions, or anything else</p>
      </div>
      <button
        onclick={close}
        class="text-white/60 hover:text-white transition-colors rounded-lg p-1"
        aria-label="Close"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Body -->
    <div class="px-5 py-5">
      {#if submitted}
        <!-- Success state -->
        <div class="flex flex-col items-center gap-3 py-6 text-center">
          <div class="flex items-center justify-center w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200">
            <svg class="h-6 w-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          </div>
          <div>
            <p class="font-semibold text-gray-900 text-sm">Got it — thank you!</p>
            <p class="text-gray-500 text-xs mt-1">Your feedback helps improve ADInteract.</p>
          </div>
          <button
            onclick={close}
            class="mt-1 text-xs font-medium text-gray-400 hover:text-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      {:else}
        <!-- Form -->
        <form onsubmit={(e) => { e.preventDefault(); submit(); }} class="space-y-4">

          <!-- Type selector -->
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Type</p>
            <div class="flex gap-2">
              {#each TYPE_OPTIONS as opt}
                <button
                  type="button"
                  onclick={() => feedbackType = opt.value}
                  class="flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all {feedbackType === opt.value
                    ? 'border-[#0a2318] bg-[#0a2318] text-white'
                    : 'border-gray-200 bg-gray-50 text-gray-600 hover:border-gray-300 hover:bg-gray-100'}"
                >
                  <span>{opt.icon}</span>
                  <span>{opt.label}</span>
                </button>
              {/each}
            </div>
          </div>

          <!-- Message -->
          <div>
            <label for="fb-message" class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              {feedbackType === 'bug' ? 'What went wrong?' : feedbackType === 'feedback' ? 'What would you improve?' : 'Your message'}
            </label>
            <textarea
              id="fb-message"
              bind:value={message}
              rows="4"
              required
              placeholder={feedbackType === 'bug'
                ? 'Describe the issue — what you did, what you expected, what happened…'
                : feedbackType === 'feedback'
                ? 'A filter you wish existed, a chart that would help, anything…'
                : 'What\'s on your mind?'}
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0a2318]/20 focus:border-[#0a2318] resize-none transition-colors"
            ></textarea>
          </div>

          <!-- Email (optional) -->
          <div>
            <label for="fb-email" class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Email <span class="font-normal normal-case text-gray-400">(optional — for follow-up)</span>
            </label>
            <input
              id="fb-email"
              type="email"
              bind:value={email}
              placeholder="you@example.com"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0a2318]/20 focus:border-[#0a2318] transition-colors"
            />
          </div>

          {#if error}
            <p class="text-xs text-red-600">{error}</p>
          {/if}

          <button
            type="submit"
            disabled={!message.trim() || submitting}
            class="w-full rounded-lg bg-[#0a2318] text-white text-sm font-semibold py-2.5 hover:bg-[#143524] disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
          >
            {submitting ? 'Sending…' : 'Send feedback'}
          </button>

          <p class="text-center text-[10px] text-gray-400">
            Page: {$page.url.pathname}
          </p>
        </form>
      {/if}
    </div>
  </div>
{/if}
