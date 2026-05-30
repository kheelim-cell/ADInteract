<script lang="ts">
  // ── FAQ data ───────────────────────────────────────────────────────────────
  type FaqItem = {
    id: number;
    q: string;
    intro?: string;
    a?: string;
    bullets?: { label: string; text: string }[];
  };

  const FAQS: FaqItem[] = [
    {
      id: 1,
      q: 'Can I, as a foreign investor, own property 100% freehold in Abu Dhabi?',
      a: 'Yes, but only in designated "Investment Zones." Foreigners (non-GCC nationals) can buy freehold land and property with 100% absolute ownership in specific master-planned areas like Yas Island, Saadiyat Island, Al Reem Island, and Al Raha Beach. Outside these zones, property ownership is restricted to UAE/GCC nationals.',
    },
    {
      id: 2,
      q: 'What are the upfront transaction costs when buying a property?',
      intro: 'Unlike some global markets with massive stamp duties, Abu Dhabi is relatively lean.',
      bullets: [
        { label: 'ADREC Transfer Fee', text: '2% of the purchase price (paid to the Abu Dhabi Real Estate Centre).' },
        { label: 'Agency Commission', text: 'Typically 2% (+ 5% VAT).' },
        { label: 'Developer Admin Fee', text: 'Usually AED 1,000 to AED 5,000.' },
        { label: 'Mortgage Registration Fee (if financing)', text: '0.1% of the loan amount.' },
      ],
    },
    {
      id: 3,
      q: 'How does the UAE Golden Visa work through property, and do off-plan projects count?',
      a: 'If your total property equity reaches AED 2 million (approx. $545,000 USD) or more, you qualify for a 10-year residency Golden Visa. You can combine multiple properties to hit this threshold. Crucially, off-plan properties qualify as long as the developer confirms your equity contribution has reached the AED 2 million mark.',
    },
    {
      id: 4,
      q: 'How well-protected is my money if I buy an off-plan property?',
      a: 'Highly protected. Abu Dhabi heavily regulates off-plan sales. Developers are legally required to open a project-specific Escrow Account monitored by ADREC. Your payment plan installments go directly into this account and are only disbursed to the developer based on verified construction milestones, drastically minimising delivery risk.',
    },
    {
      id: 5,
      q: 'Is there a rent cap in Abu Dhabi to prevent tenants from locking into low rates forever?',
      a: 'No fixed city-wide cap exists anymore. Abu Dhabi previously had a 5% rent cap, but it was abolished. However, rent increases must still match market valuations. Tenants can dispute unfair hikes via the Rental Dispute Settlement Committee (RDSC) if the landlord asks for an increase vastly above the prevailing market average for that specific building.',
    },
    {
      id: 6,
      q: 'How does the tax structure affect my rental income and capital gains?',
      a: 'This is Abu Dhabi\'s biggest selling point. There is 0% personal income tax on rental yields and 0% capital gains tax when you flip or sell the property. No annual municipal property taxes apply either. The only tax consideration is a standard 5% VAT applied strictly to commercial property transactions or agency/management services — not residential rent.',
    },
    {
      id: 7,
      q: 'What is the historical developer track record for handovers?',
      a: 'The market is dominated by massive, government-backed or highly capitalised master developers like Aldar, Modon, and Bloom. While minor delays of 3–6 months can happen globally, these tier-1 developers have an exceptional track record of finishing projects to high standards, which keeps secondary market demand robust.',
    },
    {
      id: 8,
      q: 'Should I focus on Apartments or Villas for the best long-term play?',
      intro: 'It depends on your strategy.',
      bullets: [
        { label: 'Apartments (e.g., Al Reem Island)', text: 'Traditionally yield higher net rental returns (6%–8%) and attract a steady stream of young professional tenants.' },
        { label: 'Villas/Townhouses (e.g., Yas Island or Saadiyat)', text: 'Yield slightly lower (4%–6%) but have seen massive capital appreciation due to limited supply and high demand from affluent families.' },
      ],
    },
  ];

  // ── Accordion state ────────────────────────────────────────────────────────
  let openIds = $state<Set<number>>(new Set([1]));

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
      category: '1. Government Transfer / Registration',
      rows: [
        { item: 'Rate', abu_dhabi: '2% of purchase price', dubai: '4% of purchase price' },
        { item: 'Convention', abu_dhabi: 'Split 1% buyer / 1% seller (negotiable)', dubai: 'Buyer pays full 4%' },
        { item: 'Off-plan registration', abu_dhabi: '2% via DARI/Tamleek', dubai: '4% Oqood at SPA signing' },
        { item: 'Title deed issuance', abu_dhabi: 'AED 1,000 flat', dubai: 'AED 250 + map fees (~AED 580)' },
        { item: 'Late registration penalty', abu_dhabi: 'AED 10,000 (if >21 days)', dubai: 'More lenient' },
      ],
    },
    {
      category: '2. Trustee / Admin Fees',
      rows: [
        { item: 'Trustee office fee', abu_dhabi: 'N/A (via DARI portal)', dubai: 'AED 4,200 (>AED 500K, incl. 5% VAT)' },
        { item: 'Admin / knowledge fees', abu_dhabi: 'AED 540–1,000', dubai: 'AED 600' },
      ],
    },
    {
      category: '3. Agency Commission (Ready/Resale)',
      rows: [
        { item: 'Standard rate', abu_dhabi: '2% + 5% VAT = 2.1%', dubai: '2% + 5% VAT = 2.1%' },
        { item: 'Luxury (>AED 10M)', abu_dhabi: 'Up to 3%', dubai: 'Typically stays at 2%' },
        { item: 'Who pays', abu_dhabi: 'Negotiable (often seller)', dubai: 'Negotiable (often seller)' },
      ],
    },
    {
      category: '4. Developer Admin Fee (Off-plan)',
      rows: [
        { item: 'Registration fee', abu_dhabi: 'AED 2,000 (<500K) / AED 4,000 (>500K)', dubai: 'Included in Oqood; admin ~AED 580–1,000' },
        { item: 'Handover / admin fee', abu_dhabi: 'AED 2,000–5,000', dubai: 'AED 1,000–5,000 (developer-specific)' },
      ],
    },
    {
      category: '5. NOC Fee (Ready/Resale)',
      rows: [
        { item: 'Range', abu_dhabi: 'AED 500–2,500', dubai: 'AED 500–5,000' },
        { item: 'Typical', abu_dhabi: '~AED 1,000', dubai: '~AED 1,000–5,000' },
        { item: 'Who pays', abu_dhabi: 'Usually seller', dubai: 'Usually seller' },
      ],
    },
    {
      category: '6. Mortgage Fees',
      rows: [
        { item: 'Mortgage registration fee', abu_dhabi: '0.1% of loan (min AED 500, max AED 1,000) + AED 450', dubai: '0.25% of loan + AED 290' },
        { item: 'Bank processing / arrangement', abu_dhabi: '0.5%–1% of loan', dubai: '0.5%–1% of loan' },
        { item: 'Property valuation', abu_dhabi: 'AED 2,500–3,500', dubai: 'AED 2,500–3,500' },
        { item: 'Life insurance (annual)', abu_dhabi: '~0.4–0.6% of loan', dubai: '~0.4–0.6% of loan' },
      ],
    },
    {
      category: '7. Other Costs',
      rows: [
        { item: 'Conveyancing / legal (optional)', abu_dhabi: 'AED 5,000–15,000', dubai: 'AED 5,000–15,000' },
        { item: 'Utility connection + deposit', abu_dhabi: 'AED 1,000–2,500 + deposit (ADDC)', dubai: 'AED 1,000–2,500 + deposit (DEWA)' },
        { item: 'Home insurance (annual)', abu_dhabi: 'AED 1,000–3,000', dubai: 'AED 1,000–3,000' },
        { item: 'Service charges (annual)', abu_dhabi: 'AED 10–40/sqft/year', dubai: 'AED 10–40/sqft/year' },
      ],
    },
  ];
</script>

<svelte:head>
  <title>Investor FAQs — ADInteract</title>
  <meta name="description" content="Key Abu Dhabi property investment questions answered: foreign ownership, transaction costs, Golden Visa, escrow protection, taxes, and Abu Dhabi vs Dubai cost comparison." />
</svelte:head>

<div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-8 space-y-12">

  <!-- ── FAQ section ─────────────────────────────────────────────────────────── -->
  <section>
    <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">
      Frequently Asked Questions · Abu Dhabi Property Investment
    </h3>

    <div class="space-y-2">
      {#each FAQS as faq}
        {@const isOpen = openIds.has(faq.id)}
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden transition-shadow {isOpen ? 'shadow-sm' : ''}">

          <!-- Question row -->
          <button
            type="button"
            onclick={() => toggle(faq.id)}
            class="w-full flex items-start gap-4 px-5 py-4 text-left hover:bg-gray-50 transition-colors"
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
            <div class="px-5 pb-5 pl-[3.75rem] border-t border-gray-100">
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
        Buying in Abu Dhabi vs Dubai — Transaction Cost Comparison
      </h3>
      <p class="text-xs text-gray-400">All costs are buyer-side estimates unless noted. Figures are indicative; verify with your agent and legal adviser.</p>
    </div>

    <div class="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
      <table class="w-full table-fixed text-sm min-w-[480px]">
        <!-- Table header -->
        <thead>
          <tr class="bg-gray-800 text-white">
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-left text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[26%]">Fee Category</th>
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-left text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[22%]">Line Item</th>
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-left text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[26%]">
              <span class="inline-flex items-center gap-1">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>
                Abu Dhabi
              </span>
            </th>
            <th class="px-2 sm:px-4 py-2 sm:py-3 text-left text-[10px] sm:text-xs font-bold uppercase tracking-wider w-[26%]">
              <span class="inline-flex items-center gap-1">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-sky-400 flex-shrink-0"></span>
                Dubai
              </span>
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          {#each TABLE_SECTIONS as section, si}
            <!-- Category header row -->
            <tr class="bg-gray-50">
              <td colspan="4" class="px-2 sm:px-4 py-2 text-[10px] sm:text-xs font-bold text-gray-600 uppercase tracking-wider border-t-2 border-gray-200">
                {section.category}
              </td>
            </tr>

            <!-- Data rows -->
            {#each section.rows as row, ri}
              <tr class="{ri % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-emerald-50/30 transition-colors">
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-400"></td>
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-600 font-medium">{row.item}</td>
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-800">{row.abu_dhabi}</td>
                <td class="px-2 sm:px-4 py-1.5 sm:py-2 text-[10px] sm:text-xs text-gray-500">{row.dubai}</td>
              </tr>
            {/each}
          {/each}

          <!-- Total row -->
          <tr class="bg-emerald-50 border-t-2 border-emerald-200">
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs font-bold text-gray-700 uppercase tracking-wider">Total Closing Costs</td>
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs text-gray-500">excl. down payment</td>
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-bold text-emerald-700">~4–7% of purchase price</td>
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-semibold text-gray-600">~7–9% of purchase price</td>
          </tr>

          <!-- Net delta row -->
          <tr class="bg-emerald-100/60">
            <td class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs font-bold text-gray-700 uppercase tracking-wider">Net Delta</td>
            <td class="px-2 sm:px-4 py-2 sm:py-3"></td>
            <td colspan="2" class="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-sm font-bold text-emerald-700">
              Abu Dhabi saves ~2–3 percentage points vs Dubai
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>
  </section>

</div>
