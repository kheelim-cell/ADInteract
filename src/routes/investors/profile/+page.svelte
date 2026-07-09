<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';
  import { investorProfile, saveProfile, clearProfile, type InvestorProfile, type RiskPreference } from '$lib/stores/investorProfile';

  let step = $state(1);
  let saved = $state(false);

  const LAYOUTS = ['studio', '1 bed', '2 beds', '3 beds', '4 beds', '5 beds+'];

  // Form state (initialised from saved profile)
  let budgetMin    = $state($investorProfile?.budget_min    ?? null as number | null);
  let budgetMax    = $state($investorProfile?.budget_max    ?? null as number | null);
  let horizon      = $state($investorProfile?.investment_horizon_years ?? 5);
  let risk         = $state<RiskPreference>($investorProfile?.risk_preference ?? 'balanced');
  let yieldTarget  = $state($investorProfile?.target_yield_pct ?? 5);
  let layouts      = $state<string[]>($investorProfile?.preferred_layouts ?? []);
  let visaInterest = $state($investorProfile?.visa_interest ?? false);

  function toggleLayout(l: string) {
    layouts = layouts.includes(l) ? layouts.filter(x => x !== l) : [...layouts, l];
  }

  function save() {
    const profile: InvestorProfile = {
      budget_min: budgetMin,
      budget_max: budgetMax,
      target_yield_pct: yieldTarget,
      investment_horizon_years: horizon,
      risk_preference: risk,
      preferred_layouts: layouts,
      visa_interest: visaInterest,
    };
    saveProfile(profile);
    saved = true;
    setTimeout(() => { saved = false; }, 2000);
  }

  const riskOptions: { value: RiskPreference; label: () => string }[] = [
    { value: 'yield',    label: m.profile_risk_yield    },
    { value: 'balanced', label: m.profile_risk_balanced },
    { value: 'growth',   label: m.profile_risk_growth   },
  ];
</script>

<svelte:head>
  <title>{m.profile_page_title()} — ADInteract</title>
</svelte:head>

<div class="max-w-[800px] mx-auto px-4 sm:px-8 py-8">
  <div class="mb-6">
    <h1 class="text-xl font-bold text-gray-900 mb-1">{m.profile_page_title()}</h1>
    <p class="text-sm text-gray-500">{m.profile_page_subtitle()}</p>
  </div>

  <!-- Step indicator -->
  <div class="flex items-center gap-2 mb-8">
    {#each [1,2,3] as s}
      <div class="flex items-center gap-2 {s < 3 ? 'flex-1' : ''}">
        <div class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors
          {step === s ? 'bg-emerald-600 text-white' : step > s ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-400'}">
          {#if step > s}
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          {:else}
            {s}
          {/if}
        </div>
        {#if s < 3}
          <div class="flex-1 h-0.5 {step > s ? 'bg-emerald-300' : 'bg-gray-100'}"></div>
        {/if}
      </div>
    {/each}
  </div>

  <div class="rounded-2xl border border-gray-200 bg-white p-6">
    {#if step === 1}
      <h2 class="text-base font-bold text-gray-800 mb-5">{m.profile_step1_title()}</h2>
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1">{m.profile_budget_min()}</label>
            <input type="number" min="0" step="100000" bind:value={budgetMin}
              class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-emerald-400" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1">{m.profile_budget_max()}</label>
            <input type="number" min="0" step="100000" bind:value={budgetMax}
              class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-emerald-400" />
          </div>
        </div>
        <div>
          <div class="flex justify-between mb-1">
            <label class="text-xs font-semibold text-gray-600">{m.profile_horizon()}</label>
            <span class="text-xs font-bold text-emerald-700">{horizon} yrs</span>
          </div>
          <input type="range" min="1" max="20" bind:value={horizon} class="w-full accent-emerald-600" />
        </div>
      </div>

    {:else if step === 2}
      <h2 class="text-base font-bold text-gray-800 mb-5">{m.profile_step2_title()}</h2>
      <div class="space-y-5">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-2">Risk Preference</label>
          <div class="grid grid-cols-3 gap-2">
            {#each riskOptions as opt}
              <button
                type="button"
                onclick={() => { risk = opt.value; }}
                class="rounded-xl border py-3 text-sm font-semibold transition-all
                  {risk === opt.value ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-gray-200 bg-white text-gray-600 hover:border-emerald-300'}"
              >
                {opt.label()}
              </button>
            {/each}
          </div>
        </div>
        <div>
          <div class="flex justify-between mb-1">
            <label class="text-xs font-semibold text-gray-600">{m.profile_yield_target()}</label>
            <span class="text-xs font-bold text-emerald-700">{yieldTarget}%</span>
          </div>
          <input type="range" min="2" max="15" step="0.5" bind:value={yieldTarget} class="w-full accent-emerald-600" />
        </div>
      </div>

    {:else}
      <h2 class="text-base font-bold text-gray-800 mb-5">{m.profile_step3_title()}</h2>
      <div class="space-y-5">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-2">Preferred Layouts (select all that apply)</label>
          <div class="flex flex-wrap gap-2">
            {#each LAYOUTS as l}
              <button
                type="button"
                onclick={() => toggleLayout(l)}
                class="rounded-full px-3 py-1.5 text-xs font-semibold border transition-all
                  {layouts.includes(l) ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-gray-200 bg-white text-gray-600 hover:border-emerald-300'}"
              >
                {l}
              </button>
            {/each}
          </div>
        </div>
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" bind:checked={visaInterest} class="rounded accent-emerald-600 w-4 h-4" />
          <span class="text-sm text-gray-700">{m.profile_visa_interest()}</span>
        </label>
      </div>
    {/if}

    <!-- Actions -->
    <div class="flex items-center justify-between mt-8 pt-5 border-t border-gray-100">
      <div class="flex gap-2">
        {#if step > 1}
          <button type="button" onclick={() => { step--; }} class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-50">
            {m.profile_back()}
          </button>
        {/if}
        {#if $investorProfile}
          <button type="button" onclick={clearProfile} class="text-xs font-semibold text-red-400 hover:text-red-600 px-2">
            {m.profile_clear()}
          </button>
        {/if}
      </div>
      {#if step < 3}
        <button type="button" onclick={() => { step++; }} class="rounded-lg bg-emerald-600 px-6 py-2 text-sm font-bold text-white hover:bg-emerald-700">
          {m.profile_next()}
        </button>
      {:else}
        <button type="button" onclick={save} class="rounded-lg bg-emerald-600 px-6 py-2 text-sm font-bold text-white hover:bg-emerald-700">
          {saved ? m.profile_saved() : m.profile_save()}
        </button>
      {/if}
    </div>
  </div>

  <!-- Current profile summary -->
  {#if $investorProfile}
    <div class="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
      <p class="text-xs font-semibold text-emerald-800 mb-1">Current profile</p>
      <p class="text-sm text-emerald-700">
        {$investorProfile.risk_preference} · {$investorProfile.investment_horizon_years}yr
        {#if $investorProfile.budget_min != null || $investorProfile.budget_max != null}
          · AED {($investorProfile.budget_min ?? 0).toLocaleString('en-AE')}–{($investorProfile.budget_max ?? 0).toLocaleString('en-AE')}
        {/if}
        · Target yield {$investorProfile.target_yield_pct}%
      </p>
    </div>
  {/if}
</div>
