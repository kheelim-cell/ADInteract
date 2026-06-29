<script lang="ts">
  import { m } from '$lib/paraglide/messages.js';

  // ── FAQ data ───────────────────────────────────────────────────────────────
  type FaqItem = {
    id: number;
    q: string;
    intro?: string;
    a?: string;
    bullets?: { label: string; text: string }[];
  };

  const FAQS: FaqItem[] = [
    { id: 1, q: m.faqs_q1(), a: m.faqs_a1() },
    {
      id: 2,
      q: m.faqs_q2(),
      intro: m.faqs_intro2(),
      bullets: [
        { label: m.faqs_b2_1_label(), text: m.faqs_b2_1_text() },
        { label: m.faqs_b2_2_label(), text: m.faqs_b2_2_text() },
        { label: m.faqs_b2_3_label(), text: m.faqs_b2_3_text() },
        { label: m.faqs_b2_4_label(), text: m.faqs_b2_4_text() },
      ],
    },
    { id: 3, q: m.faqs_q3(), a: m.faqs_a3() },
    { id: 4, q: m.faqs_q4(), a: m.faqs_a4() },
    { id: 5, q: m.faqs_q5(), a: m.faqs_a5() },
    { id: 6, q: m.faqs_q6(), a: m.faqs_a6() },
    { id: 7, q: m.faqs_q7(), a: m.faqs_a7() },
    {
      id: 8,
      q: m.faqs_q8(),
      intro: m.faqs_intro8(),
      bullets: [
        { label: m.faqs_b8_1_label(), text: m.faqs_b8_1_text() },
        { label: m.faqs_b8_2_label(), text: m.faqs_b8_2_text() },
      ],
    },
  ];

  // ── JSON-LD schema (FAQ rich results) ─────────────────────────────────────
  const faqSchema = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQS.map(f => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: f.a
          ? f.a
          : (f.intro ?? '') + (f.bullets ? ' ' + f.bullets.map(b => `${b.label}: ${b.text}`).join(' ') : '')
      }
    }))
  });

  // ── Accordion state ────────────────────────────────────────────────────────
  let openIds = $state<Set<number>>(new Set());

  function toggle(id: number) {
    const next = new Set(openIds);
    if (next.has(id)) { next.delete(id); } else { next.add(id); }
    openIds = next;
  }

  // ── Comparison table ───────────────────────────────────────────────────────
  type TableRow = { item: string; abu_dhabi: string; dubai: string };
  type TableSection = { category: string; rows: TableRow[] };

  const TABLE_SECTIONS: TableSection[] = [
    {
      category: m.faqs_table_cat1(),
      rows: [
        { item: m.faqs_table_s1_r1_item(), abu_dhabi: m.faqs_table_s1_r1_ad(), dubai: m.faqs_table_s1_r1_dxb() },
        { item: m.faqs_table_s1_r2_item(), abu_dhabi: m.faqs_table_s1_r2_ad(), dubai: m.faqs_table_s1_r2_dxb() },
        { item: m.faqs_table_s1_r3_item(), abu_dhabi: m.faqs_table_s1_r3_ad(), dubai: m.faqs_table_s1_r3_dxb() },
        { item: m.faqs_table_s1_r4_item(), abu_dhabi: m.faqs_table_s1_r4_ad(), dubai: m.faqs_table_s1_r4_dxb() },
        { item: m.faqs_table_s1_r5_item(), abu_dhabi: m.faqs_table_s1_r5_ad(), dubai: m.faqs_table_s1_r5_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat2(),
      rows: [
        { item: m.faqs_table_s2_r1_item(), abu_dhabi: m.faqs_table_s2_r1_ad(), dubai: m.faqs_table_s2_r1_dxb() },
        { item: m.faqs_table_s2_r2_item(), abu_dhabi: m.faqs_table_s2_r2_ad(), dubai: m.faqs_table_s2_r2_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat3(),
      rows: [
        { item: m.faqs_table_s3_r1_item(), abu_dhabi: m.faqs_table_s3_r1_ad(), dubai: m.faqs_table_s3_r1_dxb() },
        { item: m.faqs_table_s3_r2_item(), abu_dhabi: m.faqs_table_s3_r2_ad(), dubai: m.faqs_table_s3_r2_dxb() },
        { item: m.faqs_table_s3_r3_item(), abu_dhabi: m.faqs_table_s3_r3_ad(), dubai: m.faqs_table_s3_r3_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat4(),
      rows: [
        { item: m.faqs_table_s4_r1_item(), abu_dhabi: m.faqs_table_s4_r1_ad(), dubai: m.faqs_table_s4_r1_dxb() },
        { item: m.faqs_table_s4_r2_item(), abu_dhabi: m.faqs_table_s4_r2_ad(), dubai: m.faqs_table_s4_r2_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat5(),
      rows: [
        { item: m.faqs_table_s5_r1_item(), abu_dhabi: m.faqs_table_s5_r1_ad(), dubai: m.faqs_table_s5_r1_dxb() },
        { item: m.faqs_table_s5_r2_item(), abu_dhabi: m.faqs_table_s5_r2_ad(), dubai: m.faqs_table_s5_r2_dxb() },
        { item: m.faqs_table_s5_r3_item(), abu_dhabi: m.faqs_table_s5_r3_ad(), dubai: m.faqs_table_s5_r3_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat6(),
      rows: [
        { item: m.faqs_table_s6_r1_item(), abu_dhabi: m.faqs_table_s6_r1_ad(), dubai: m.faqs_table_s6_r1_dxb() },
        { item: m.faqs_table_s6_r2_item(), abu_dhabi: m.faqs_table_s6_r2_ad(), dubai: m.faqs_table_s6_r2_dxb() },
        { item: m.faqs_table_s6_r3_item(), abu_dhabi: m.faqs_table_s6_r3_ad(), dubai: m.faqs_table_s6_r3_dxb() },
        { item: m.faqs_table_s6_r4_item(), abu_dhabi: m.faqs_table_s6_r4_ad(), dubai: m.faqs_table_s6_r4_dxb() },
      ],
    },
    {
      category: m.faqs_table_cat7(),
      rows: [
        { item: m.faqs_table_s7_r1_item(), abu_dhabi: m.faqs_table_s7_r1_ad(), dubai: m.faqs_table_s7_r1_dxb() },
        { item: m.faqs_table_s7_r2_item(), abu_dhabi: m.faqs_table_s7_r2_ad(), dubai: m.faqs_table_s7_r2_dxb() },
        { item: m.faqs_table_s7_r3_item(), abu_dhabi: m.faqs_table_s7_r3_ad(), dubai: m.faqs_table_s7_r3_dxb() },
        { item: m.faqs_table_s7_r4_item(), abu_dhabi: m.faqs_table_s7_r4_ad(), dubai: m.faqs_table_s7_r4_dxb() },
      ],
    },
  ];
</script>

<svelte:head>
  <title>{m.faqs_meta_title()}</title>
  <meta name="description" content={m.faqs_meta_description()} />
  <meta property="og:title" content={m.faqs_og_title()} />
  <meta property="og:description" content={m.faqs_og_description()} />

  {@html `<script type="application/ld+json">${faqSchema}</script>`}
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-12">

  <!-- ── FAQ section ─────────────────────────────────────────────────────────── -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">
      {m.faqs_section_heading()}
    </h3>

    <div class="space-y-2">
      {#each FAQS as faq}
        {@const isOpen = openIds.has(faq.id)}
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden transition-shadow {isOpen ? 'shadow-sm' : ''}">

          <!-- Question row -->
          <button
            type="button"
            onclick={() => toggle(faq.id)}
            class="w-full flex items-start gap-4 px-5 py-4 text-start hover:bg-gray-50 transition-colors"
          >
            <!-- Q number badge -->
            <span class="flex-shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/12 border border-emerald-500/25 text-[10px] font-bold text-emerald-600 mt-0.5">
              {faq.id}
            </span>

            <span class="flex-1 text-sm font-semibold text-gray-800 leading-snug">
              {faq.q}
            </span>

            <!-- Chevron -->
            <svg
              class="flex-shrink-0 w-4 h-4 text-gray-400 mt-0.5 transition-transform duration-200 {isOpen ? 'rotate-180' : ''}"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </button>

          <!-- Answer -->
          {#if isOpen}
            <div class="px-5 pb-5 ps-[3.75rem] border-t border-gray-100">
              <div class="pt-4 space-y-3 text-sm text-gray-600 leading-relaxed">
                {#if faq.intro}
                  <p>{faq.intro}</p>
                {/if}

                {#if faq.a}
                  <p>{faq.a}</p>
                {/if}

                {#if faq.bullets}
                  <ul class="space-y-2 mt-1">
                    {#each faq.bullets as bullet}
                      <li class="flex gap-2">
                        <span class="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2"></span>
                        <span>
                          <span class="font-semibold text-gray-700">{bullet.label}:</span>
                          {' '}{bullet.text}
                        </span>
                      </li>
                    {/each}
                  </ul>
                {/if}
              </div>
            </div>
          {/if}

        </div>
      {/each}
    </div>
  </section>

  <!-- ── Abu Dhabi vs Dubai comparison table ─────────────────────────────────── -->
  <section>
    <div class="mb-6">
      <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">
        {m.faqs_table_heading()}
      </h3>
      <p class="text-xs text-gray-400">{m.faqs_table_subtitle()}</p>
    </div>

    <div class="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
      <table class="w-full table-fixed text-sm min-w-[360px]">
        <!-- Table header — 3 columns (Fee Category removed) -->
        <thead>
          <tr class="bg-gray-800 text-white">
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-start text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[30%]">{m.faqs_table_th_line_item()}</th>
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-start text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[35%]">
              <span class="inline-flex items-center gap-1">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>
                {m.faqs_table_th_abudhabi()}
              </span>
            </th>
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-start text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[35%]">
              <span class="inline-flex items-center gap-1">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-sky-400 flex-shrink-0"></span>
                {m.faqs_table_th_dubai()}
              </span>
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          {#each TABLE_SECTIONS as section, si}
            <!-- Category header row spans all 3 columns -->
            <tr class="bg-gray-50">
              <td colspan="3" class="px-2 sm:px-4 py-2 text-[10px] sm:text-xs font-bold text-gray-600 uppercase tracking-wider border-t-2 border-gray-200">
                {section.category}
              </td>
            </tr>

            <!-- Data rows — 3 columns -->
            {#each section.rows as row, ri}
              <tr class="{ri % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-emerald-50/30 transition-colors">
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-600 font-medium">{row.item}</td>
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-800">{row.abu_dhabi}</td>
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-500">{row.dubai}</td>
              </tr>
            {/each}
          {/each}

          <!-- Total row -->
          <tr class="bg-emerald-50 border-t-2 border-emerald-200">
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs font-bold text-gray-700 uppercase tracking-wider">
              {m.faqs_table_total_label()}
              <span class="block text-[9px] sm:text-[10px] font-normal normal-case text-gray-500 mt-0.5">{m.faqs_table_total_sublabel()}</span>
            </td>
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-bold text-emerald-700">{m.faqs_table_total_ad()}</td>
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-semibold text-gray-600">{m.faqs_table_total_dxb()}</td>
          </tr>

          <!-- Net delta row -->
          <tr class="bg-emerald-100/60">
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs font-bold text-gray-700 uppercase tracking-wider">{m.faqs_table_delta_label()}</td>
            <td colspan="2" class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-bold text-emerald-700">
              {m.faqs_table_delta_text()}
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>
  </section>

</div>
