<script lang="ts">
  import { base } from '$app/paths';

  let { theme = 'gold' }: { theme?: 'gold' | 'emerald' } = $props();

  const t = $derived(theme === 'gold' ? {
    border:    'border-brand-200',
    bg:        'from-brand-50 to-white',
    badge:     'bg-brand-600',
    label:     'text-brand-900',
    iconBg:    'bg-brand-50 group-hover:bg-brand-100',
    iconColor: 'text-brand-600',
    cardBorder:'border-brand-200 hover:border-brand-400',
    heading:   'text-brand-900',
  } : {
    border:    'border-emerald-100',
    bg:        'from-emerald-50 to-white',
    badge:     'bg-emerald-600',
    label:     'text-emerald-900',
    iconBg:    'bg-emerald-50 group-hover:bg-emerald-100',
    iconColor: 'text-emerald-600',
    cardBorder:'border-emerald-100 hover:border-emerald-400',
    heading:   'text-emerald-900',
  });
</script>

<!-- Investor Tools Strip: surfaces high-value tools that drive 65% of key events -->
<div class="mt-10 rounded-2xl border {t.border} bg-gradient-to-br {t.bg} px-5 py-5">
  <div class="flex items-center gap-2 mb-4">
    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full {t.badge} text-white">
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    </span>
    <h3 class="text-sm font-bold {t.heading} tracking-wide uppercase">Investor Tools</h3>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
    <!-- ROI Calculator -->
    <a
      href="{base}/investors/calculator"
      class="group flex flex-col gap-1.5 rounded-xl border {t.cardBorder} bg-white hover:shadow-md px-4 py-3.5 transition-all"
    >
      <div class="flex items-center gap-2">
        <span class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg {t.iconBg} transition-colors">
          <svg class="w-4 h-4 {t.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V13.5Zm0 2.25h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25V18Zm2.498-6.75h.007v.008h-.007v-.008Zm0 2.25h.007v.008h-.007V13.5Zm0 2.25h.007v.008h-.007v-.008Zm0 2.25h.007v.008h-.007V18Zm2.504-6.75h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V13.5Zm0 2.25h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V18Zm2.498-6.75h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V13.5ZM8.25 6h7.5v2.25h-7.5V6ZM12 2.25c-1.892 0-3.758.11-5.593.322C5.307 2.7 4.5 3.65 4.5 4.757V19.5a2.25 2.25 0 0 0 2.25 2.25h10.5a2.25 2.25 0 0 0 2.25-2.25V4.757c0-1.108-.806-2.057-1.907-2.185A48.507 48.507 0 0 0 12 2.25Z" />
          </svg>
        </span>
        <span class="text-sm font-semibold text-gray-900 group-hover:{t.label} transition-colors">ROI Calculator</span>
      </div>
      <p class="text-xs text-gray-500 leading-snug">Net yield, capital gain & total ROI — off-plan or ready</p>
    </a>

    <!-- District Comparison -->
    <a
      href="{base}/investors/compare"
      class="group flex flex-col gap-1.5 rounded-xl border {t.cardBorder} bg-white hover:shadow-md px-4 py-3.5 transition-all"
    >
      <div class="flex items-center gap-2">
        <span class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg {t.iconBg} transition-colors">
          <svg class="w-4 h-4 {t.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 4.5v15m6-15v15m-10.875 0h15.75c.621 0 1.125-.504 1.125-1.125V5.625c0-.621-.504-1.125-1.125-1.125H4.125C3.504 4.5 3 5.004 3 5.625v12.75c0 .621.504 1.125 1.125 1.125Z" />
          </svg>
        </span>
        <span class="text-sm font-semibold text-gray-900 group-hover:{t.label} transition-colors">Compare Districts</span>
      </div>
      <p class="text-xs text-gray-500 leading-snug">Side-by-side metrics across yield, growth & price</p>
    </a>

    <!-- Flip Scanner -->
    <a
      href="{base}/investors/flip-scanner"
      class="group flex flex-col gap-1.5 rounded-xl border {t.cardBorder} bg-white hover:shadow-md px-4 py-3.5 transition-all"
    >
      <div class="flex items-center gap-2">
        <span class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg {t.iconBg} transition-colors">
          <svg class="w-4 h-4 {t.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803Z" />
          </svg>
        </span>
        <span class="text-sm font-semibold text-gray-900 group-hover:{t.label} transition-colors">Flip Scanner</span>
      </div>
      <p class="text-xs text-gray-500 leading-snug">Off-plan projects priced below secondary market</p>
    </a>

    <!-- Off-Plan Pipeline -->
    <a
      href="{base}/investors/pipeline"
      class="group flex flex-col gap-1.5 rounded-xl border {t.cardBorder} bg-white hover:shadow-md px-4 py-3.5 transition-all"
    >
      <div class="flex items-center gap-2">
        <span class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg {t.iconBg} transition-colors">
          <svg class="w-4 h-4 {t.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h6M9 11.25h6M9 15.75h6" />
          </svg>
        </span>
        <span class="text-sm font-semibold text-gray-900 group-hover:{t.label} transition-colors">Off-Plan Pipeline</span>
      </div>
      <p class="text-xs text-gray-500 leading-snug">Registered-sales velocity by project — accelerating, slowing or stale</p>
    </a>

    <!-- Rental Yield -->
    <a
      href="{base}/investors/rental-yield"
      class="group flex flex-col gap-1.5 rounded-xl border {t.cardBorder} bg-white hover:shadow-md px-4 py-3.5 transition-all"
    >
      <div class="flex items-center gap-2">
        <span class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg {t.iconBg} transition-colors">
          <svg class="w-4 h-4 {t.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
          </svg>
        </span>
        <span class="text-sm font-semibold text-gray-900 group-hover:{t.label} transition-colors">Rental Yield</span>
      </div>
      <p class="text-xs text-gray-500 leading-snug">Gross yield % by community, type & layout</p>
    </a>
  </div>
</div>
