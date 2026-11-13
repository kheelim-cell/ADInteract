<script lang="ts">
  import { base } from '$app/paths';
  import ConfidenceBadge from '$lib/components/ui/ConfidenceBadge.svelte';
  import InvestmentScoreCard from '$lib/components/district/InvestmentScoreCard.svelte';
  import PdfLeadMagnet from '$lib/components/ui/PdfLeadMagnet.svelte';
  import { m } from '$lib/paraglide/messages.js';
  import { localizeHref } from '$lib/paraglide/runtime';

  let { data } = $props();
  const { districtName, summary, psfRank, aboveCitywideMedian, offPlanMomentum } = data;

  const periodLabel = summary?.is_12m ? m.area_period_12m() : m.area_period_all();

  // NOTE: this page is intentionally a standalone, indexable landing page.
  // It used to auto-redirect to /?district= on mount, but Google honoured that
  // client-side redirect and flagged every district page as "Page with redirect"
  // (so none got indexed). Users now stay here and click through to the
  // interactive dashboard via the CTA button below.

  function fmtNum(n: number | null): string {
    if (n == null) return '—';
    return n.toLocaleString('en-AE');
  }

  const districtPath = `/area/${summary?.slug ?? districtName.toLowerCase().replace(/\s+/g, '-')}`;
  const canonicalUrl = `https://adinteract.co${localizeHref(districtPath)}`;
  const ogImageUrl = `https://adinteract.co/og/area/${summary?.slug ?? districtName.toLowerCase().replace(/\s+/g, '-')}.png`;

  // ── Quick-answer lead sentence ────────────────────────────────────────
  // Self-contained, positioned right after the H1 (before the Investment
  // Score widget) so it's the first substantive sentence on the page —
  // built for an AI system or human to quote standalone, not buried in the
  // prose block below.
  const leadSentence = summary
    ? summary.median_psf != null
      ? m.area_lead_sentence_with_psf({
          district: districtName,
          price: fmtNum(summary.median_price),
          psf: fmtNum(summary.median_psf),
          count: fmtNum(summary.tx_count_12m),
          period: periodLabel
        })
      : m.area_lead_sentence_no_psf({
          district: districtName,
          price: fmtNum(summary.median_price),
          count: fmtNum(summary.tx_count_12m),
          period: periodLabel
        })
    : null;

  // ── FAQ — natural question variants, each backed by real, already-
  //    computed data (nothing fabricated: districts without a median_psf
  //    skip the "expensive?" question rather than guess; districts without
  //    a computed growth score skip the momentum question rather than
  //    invent a trend). Feeds both the visible section below and the
  //    FAQPage JSON-LD in <svelte:head> — kept identical, since Google's
  //    structured-data guidelines require visible content to match markup.
  type FaqItem = { q: string; a: string };
  const faqItems: FaqItem[] = [];

  if (summary) {
    faqItems.push({
      q: m.area_faq_q_median_price({ district: districtName }),
      a:
        summary.median_psf != null
          ? m.area_faq_a_median_price_with_psf({
              district: districtName,
              price: fmtNum(summary.median_price),
              psf: fmtNum(summary.median_psf),
              count: fmtNum(summary.tx_count_12m),
              period: periodLabel
            })
          : m.area_faq_a_median_price_no_psf({
              district: districtName,
              price: fmtNum(summary.median_price),
              count: fmtNum(summary.tx_count_12m),
              period: periodLabel
            })
    });

    if (psfRank && aboveCitywideMedian != null) {
      faqItems.push({
        q: m.area_faq_q_expensive({ district: districtName }),
        a: aboveCitywideMedian
          ? m.area_faq_a_expensive_above({
              district: districtName,
              rank: String(psfRank.rank),
              total: String(psfRank.total)
            })
          : m.area_faq_a_expensive_below({
              district: districtName,
              rank: String(psfRank.rank),
              total: String(psfRank.total)
            })
      });
    }

    faqItems.push({
      q: m.area_faq_q_volume({ district: districtName }),
      a: m.area_faq_a_volume({
        district: districtName,
        count: fmtNum(summary.tx_count_12m),
        period: periodLabel,
        totalCount: fmtNum(summary.tx_count_all)
      })
    });

    if (summary.top_layouts.length) {
      faqItems.push({
        q: m.area_faq_q_layouts({ district: districtName }),
        a: m.area_faq_a_layouts({ district: districtName, layouts: summary.top_layouts.join(', ') })
      });
    }

    // Off-plan PSF year-over-year momentum — only present for districts with
    // enough off-plan activity to have a computed growth score (36 of 96).
    // Deliberately framed as off-plan-specific, not a general "price trend"
    // claim the data doesn't actually support. pct_change is null whenever
    // direction is "flat" (confirmed: no district pairs "flat" with a real
    // number) — gating on pct_change != null means only 'up'/'down' ever
    // reach the branches below, and a flat/unknown district correctly gets
    // no momentum claim at all rather than a fabricated "0.0%" one.
    if (offPlanMomentum && offPlanMomentum.pct_change != null) {
      const pctChange = offPlanMomentum.pct_change;
      faqItems.push({
        q: m.area_faq_q_momentum({ district: districtName }),
        a:
          offPlanMomentum.direction === 'up'
            ? m.area_faq_a_momentum_up({
                district: districtName,
                pct: pctChange.toFixed(1)
              })
            : m.area_faq_a_momentum_down({
                district: districtName,
                pct: Math.abs(pctChange).toFixed(1)
              })
      });
    }
  }

  // ── Structured data ──────────────────────────────────────────────────
  const datasetSchema = summary
    ? {
        '@context': 'https://schema.org',
        '@type': 'Dataset',
        name: `${districtName} Abu Dhabi Property Transactions`,
        description: summary.median_psf != null
          ? m.area_meta_description_with_data({
              count: fmtNum(summary.tx_count_12m),
              district: districtName,
              psf: fmtNum(summary.median_psf)
            })
          : m.area_meta_description_no_data({ district: districtName }),
        url: canonicalUrl,
        keywords: [districtName, 'Abu Dhabi', 'property transactions', 'real estate', 'ADREC'],
        creator: { '@type': 'Organization', name: 'ADInteract', url: 'https://adinteract.co' },
        isAccessibleForFree: true,
        temporalCoverage: '2019-01-01/..',
        spatialCoverage: {
          '@type': 'Place',
          name: `${districtName}, Abu Dhabi, United Arab Emirates`
        },
        variableMeasured: ['Median transaction price', 'Median price per square foot', 'Transaction volume']
      }
    : null;
  const datasetSchemaJson = datasetSchema ? JSON.stringify(datasetSchema) : null;

  const faqSchema = faqItems.length
    ? {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: faqItems.map((item) => ({
          '@type': 'Question',
          name: item.q,
          acceptedAnswer: { '@type': 'Answer', text: item.a }
        }))
      }
    : null;
  const faqSchemaJson = faqSchema ? JSON.stringify(faqSchema) : null;
</script>

<svelte:head>
  <title>{m.area_meta_title({ district: districtName })}</title>
  <meta
    name="description"
    content={summary
      ? m.area_meta_description_with_data({ count: fmtNum(summary.tx_count_12m), district: districtName, psf: fmtNum(summary.median_psf) })
      : m.area_meta_description_no_data({ district: districtName })}
  />
  <!-- Open Graph — district-specific, overrides global layout defaults -->
  <meta property="og:title" content={m.area_meta_title({ district: districtName })} />
  <meta
    property="og:description"
    content={summary
      ? m.area_og_description_with_data({ count: fmtNum(summary.tx_count_12m), district: districtName, psf: fmtNum(summary.median_psf) })
      : m.area_meta_description_no_data({ district: districtName })}
  />
  <meta property="og:url" content={canonicalUrl} />
  <meta property="og:type" content="website" />
  <!-- District-specific report-card image, generated at build time by scripts/generate_og_images.mjs -->
  <meta property="og:image" content={ogImageUrl} />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:type" content="image/png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content={ogImageUrl} />
  <!-- Canonical is the clean slug URL (locale-aware) — tells Google this is the authoritative page -->
  <link rel="canonical" href={canonicalUrl} />
  <!-- Dataset + FAQPage structured data — FAQ entries mirror the visible
       section below exactly (Google requires markup to match visible content) -->
  {#if datasetSchemaJson}
    {@html `<script type="application/ld+json">${datasetSchemaJson}</script>`}
  {/if}
  {#if faqSchemaJson}
    {@html `<script type="application/ld+json">${faqSchemaJson}</script>`}
  {/if}
</svelte:head>

<!-- ── Prose block ────────────────────────────────────────────────────────
     This HTML is baked in at build time and is the indexable landing page.
     Google reads it without running JS; users read it and click through to
     the interactive dashboard via the CTA below.
──────────────────────────────────────────────────────────────────────── -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-16">

  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-sm text-gray-500 mb-5">
    <a href="{base}/" class="hover:text-brand-600 transition-colors">{m.area_breadcrumb_overview()}</a>
    <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    <span class="font-medium text-gray-900">{districtName}</span>
  </nav>

  <h1 class="text-3xl font-bold text-navy mb-1">{districtName}</h1>
  <p class="text-sm text-gray-400 mb-4">
    {m.area_subtitle()}
  </p>

  <!-- Quick-answer lead sentence — first substantive sentence on the page,
       self-contained and quotable on its own, ahead of the Investment Score
       widget below. -->
  {#if leadSentence}
    <p class="text-base text-gray-800 font-medium mb-5 max-w-3xl">
      {leadSentence}
    </p>
  {/if}

  <!-- Investment Score -->
  <InvestmentScoreCard district={districtName} />

  {#if summary}
    <div class="rounded-xl border border-gray-100 bg-gray-50 px-6 py-5 text-sm text-gray-700 leading-relaxed max-w-3xl">
      <p>
        <strong>{districtName}</strong> {m.area_prose_recorded()}
        <strong>{m.area_prose_tx_count({ count: fmtNum(summary.tx_count_12m) })}</strong>
        {m.area_prose_in()} {periodLabel}.
        {#if summary.median_psf}
          {m.area_prose_median_price_is()} <strong>{m.area_prose_psf_value({ psf: fmtNum(summary.median_psf) })}</strong>
          {#if summary.p10_psf && summary.p90_psf}
            {m.area_prose_trading_range({ p10: fmtNum(summary.p10_psf), p90: fmtNum(summary.p90_psf) })}
          {:else}
            .
          {/if}
        {/if}
        {#if summary.median_price}
          {m.area_prose_median_value_is()} <strong>{m.area_prose_value_amount({ price: fmtNum(summary.median_price) })}</strong>.
        {/if}
        {#if summary.top_layouts.length}
          {m.area_prose_top_layouts_are()}
          <strong>{summary.top_layouts.join(', ')}</strong>.
        {/if}
      </p>
      <p class="mt-2 text-xs text-gray-400 flex flex-wrap items-center gap-2">
        <span>{m.area_footer_sourced({ totalCount: fmtNum(summary.tx_count_all), lastSale: summary.last_sale })}</span>
        <ConfidenceBadge count={summary.tx_count_12m} />
      </p>
    </div>

    <!-- CTA into the interactive dashboard, pre-filtered to this district -->
    <a
      href="{base}/?district={encodeURIComponent(districtName)}"
      class="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
    >
      {m.area_cta_explore({ district: districtName })}
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
      </svg>
    </a>
  {:else}
    <a
      href="{base}/?district={encodeURIComponent(districtName)}"
      class="mt-2 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
    >
      {m.area_cta_go_to({ district: districtName })}
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
      </svg>
    </a>
  {/if}

  <!-- PDF Lead Magnet -->
  <div class="mt-10">
    <PdfLeadMagnet />
  </div>

  <!-- FAQ — mirrors the FAQPage JSON-LD in <svelte:head> exactly. Each entry
       is backed by real, already-computed data (see the script block above);
       nothing here is fabricated to fill out the list. -->
  {#if faqItems.length}
    <section class="mt-12 max-w-3xl">
      <h2 class="text-xl font-bold text-navy mb-4">{m.area_faq_heading({ district: districtName })}</h2>
      <div class="space-y-4">
        {#each faqItems as item}
          <div class="rounded-lg border border-gray-100 bg-white px-5 py-4">
            <h3 class="text-sm font-semibold text-gray-900 mb-1">{item.q}</h3>
            <p class="text-sm text-gray-600 leading-relaxed">{item.a}</p>
          </div>
        {/each}
      </div>
    </section>
  {/if}

</div>
