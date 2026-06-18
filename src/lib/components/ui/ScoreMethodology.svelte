<script lang="ts">
  let { compact = false }: { compact?: boolean } = $props();
  let open = $state(!compact);
</script>

{#if compact}
  <button
    type="button"
    onclick={() => open = !open}
    class="flex items-center gap-1.5 text-xs text-brand-600 hover:text-brand-800 font-semibold mt-3 mb-1"
  >
    <svg class="w-3.5 h-3.5 transition-transform {open ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
    {open ? 'Hide' : 'How is this scored?'}
  </button>
{/if}

{#if open}
<div class="mt-4 space-y-6 text-sm text-gray-700">

  <!-- ── Section 1: Dual scoring ───────────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">1 · Dual scoring by market maturity</h3>
    <p class="text-sm text-gray-600 leading-relaxed mb-3">
      Abu Dhabi has two structurally different property market segments that cannot be scored on the same framework.
      Applying a mature-market index to a pre-completion freehold district penalises it for having no rental income or resale history —
      the very features that define an early-cycle opportunity. We therefore classify each district automatically using ADREC data and apply the appropriate model.
    </p>
    <div class="grid sm:grid-cols-2 gap-3">
      <div class="rounded-xl border-l-4 border-emerald-500 border border-gray-100 bg-gray-50 px-4 py-3">
        <p class="text-xs font-bold text-emerald-700 uppercase tracking-widest mb-1">Yield &amp; Stability</p>
        <p class="text-xs text-gray-600 leading-relaxed">
          Applied when <strong>&gt;60%</strong> of all-time ADREC transactions in the district are <em>ready/secondary-market</em> sales.
          These are established districts with active resale markets, rental benchmarks, and multi-year price history.
          The score mirrors MSCI/IPD total-return logic: income return (yield) and capital return (momentum), risk-adjusted.
        </p>
        <p class="text-xs text-gray-400 mt-1.5">Example districts: Khalifa City, Al Reem Island, Corniche, MBZ City</p>
      </div>
      <div class="rounded-xl border-l-4 border-blue-500 border border-gray-100 bg-gray-50 px-4 py-3">
        <p class="text-xs font-bold text-blue-700 uppercase tracking-widest mb-1">Growth &amp; Early-Cycle</p>
        <p class="text-xs text-gray-600 leading-relaxed">
          Applied when <strong>&lt;40%</strong> of all-time transactions are ready/resale — meaning the district is predominantly
          developer-launched, with most units not yet completed. The score mirrors CBRE/PGIM emerging market logic:
          demand velocity, developer confidence, and forward appreciation signal.
        </p>
        <p class="text-xs text-gray-400 mt-1.5">Example districts: Al Hidayriyyat, Al Jubail Island, new Saadiyat phases</p>
      </div>
    </div>
    <p class="text-xs text-gray-400 mt-3">
      Districts where 40–60% of transactions are ready receive both scores displayed side by side.
      Classification updates daily as new ADREC transactions are registered.
    </p>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 2: Factor tables ──────────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">2 · Factors, weights &amp; calculation logic</h3>

    <!-- Yield & Stability table -->
    <p class="text-xs font-semibold text-emerald-700 mb-2">Yield &amp; Stability (100 pts)</p>
    <div class="overflow-x-auto mb-4">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[22%]">Factor</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[10%]">Weight</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">Calculation</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Price momentum<br><span class="font-normal text-gray-400">ready txns only</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">30 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">% change in median AED/sqft for <em>ready/resale</em> transactions, last 12m vs prior 12m. Off-plan excluded — developer pricing is not market-driven. Capped at ±40% to prevent outlier distortion. Fewer than 5 ready txns in either window → neutral 15 pts.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Gross rental yield</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">25 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Median ADREC-registered annual rent ÷ median sale price × 100. Uses the latest full year of rental contracts (new + renewals). Scoring: &gt;8% → 25, 6–8% → 22, 4–6% → 16, 2–4% → 8, &lt;2% → 2. Fewer than 5 registered rents → neutral 12 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Liquidity<br><span class="font-normal text-gray-400">recency-weighted</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">20 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Ratio of transaction count in the last 3m vs the average 3m count over the prior 9m. Captures <em>current</em> market activity, not just historical size. Log-scaled to prevent one high-volume district dominating. A ratio &gt;1 signals a strengthening market.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Price stability<br><span class="font-normal text-gray-400">inverse CoV</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">15 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Inverse of the coefficient of variation (std ÷ mean) of quarterly median AED/sqft over 24 months. Lower price volatility scores higher — consistent with PGIM and JLL risk-adjusted return methodology. CoV ≤0.05 → 15 pts; &gt;0.30 → 2 pts. Fewer than 4 quarters of data → neutral 7 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Appreciation signal</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">10 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Ready-market median AED/sqft ÷ off-plan median AED/sqft (last 12m). Ratio &gt;1 = completed units trade above off-plan entry — investors who bought off-plan have seen appreciation. Only one sale type present → neutral 5 pts.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Growth & Early-Cycle table -->
    <p class="text-xs font-semibold text-blue-700 mb-2">Growth &amp; Early-Cycle (100 pts)</p>
    <div class="overflow-x-auto">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[22%]">Factor</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[10%]">Weight</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">Calculation</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Off-plan velocity</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">30 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Off-plan transaction count in the last 6m vs the prior 6m period. An accelerating ratio signals developer launches finding buyers, which is the primary demand signal in a pre-completion market. Ratio 3× or above → 30 pts. Prior period with zero off-plan sales but current activity → neutral 15 pts.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Off-plan momentum</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">25 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">% change in median AED/sqft for <em>off-plan</em> transactions, last 12m vs prior 12m. In early-cycle districts, developer pricing reflects future value expectations — rising off-plan PSF signals developer confidence in land appreciation. Same ±40% cap as yield model.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Appreciation signal<br><span class="font-normal text-gray-400">where available</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">20 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Same ready/off-plan ratio as Yield model, weighted higher (20 pts vs 10 pts). In early-cycle districts, any proven appreciation evidence is a strong signal — it shows the forward thesis is beginning to materialise. Absent data → neutral 10 pts.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Developer activity</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">15 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Ratio of unique project names with off-plan registrations in the last 12m vs the prior 12m. More developers entering or expanding a district signals confidence in its trajectory. Ratio ≥1.5 → 15 pts; ratio &lt;0.75 → 4 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Market entry momentum</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">10 pts</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Off-plan transactions in the last 3m vs the rolling 3m average over the prior 9m. Captures whether buyer interest is accelerating at the most recent point in time — the forward signal for near-term activity. Ratio ≥1.5 → 10 pts.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 3: Global benchmarks ──────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">3 · Factor coverage vs global benchmarks</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">Factor</th>
            <th class="text-center px-3 py-2 border border-gray-100 font-semibold text-gray-600">MSCI / IPD</th>
            <th class="text-center px-3 py-2 border border-gray-100 font-semibold text-gray-600">JLL GRETI</th>
            <th class="text-center px-3 py-2 border border-gray-100 font-semibold text-gray-600">Knight Frank PIRI</th>
            <th class="text-center px-3 py-2 border border-gray-100 font-semibold text-gray-600 bg-green-50">ADInteract (Y&amp;S)</th>
            <th class="text-center px-3 py-2 border border-gray-100 font-semibold text-gray-600 bg-blue-50">ADInteract (G&amp;EC)</th>
          </tr>
        </thead>
        <tbody>
          {#each [
            ['Capital growth / price momentum', '✓ core', '✓ core', '✓ primary', '✓ 30 pts', '✓ 25 pts'],
            ['Income return / rental yield',    '✓ core (50%)', '✓ included', '✗ excluded', '✓ 25 pts', '✗ pre-completion'],
            ['Liquidity / market depth',        '✓ bid-ask, DOM', '✓ vol.', '~ proxy', '✓ 20 pts', '✓ velocity 30 pts'],
            ['Risk / price volatility',         '✓ CoV, Sharpe', '✓ transparency', '✗ excluded', '✓ 15 pts', '~ not penalised'],
            ['Appreciation signal (off-plan→resale)', '✗ not used', '✗ not used', '✗ not used', '✓ 10 pts', '✓ 20 pts'],
            ['Developer / supply pipeline',     '✓ included', '✓ included', '✗ excluded', '✗ no ADREC data', '✓ 15 pts proxy'],
            ['Market entry / demand momentum',  '~ absorption', '~ pipeline', '✗ excluded', '✓ recency', '✓ 10 pts'],
            ['Macro / regulatory risk',         '✓ country', '✓ primary', '~ country', '✗ district N/A', '✗ district N/A'],
          ] as [factor, msci, jll, kf, ys, gec]}
            <tr class="even:bg-gray-50">
              <td class="px-3 py-2 border border-gray-100 font-medium">{factor}</td>
              <td class="px-3 py-2 border border-gray-100 text-center text-gray-600">{msci}</td>
              <td class="px-3 py-2 border border-gray-100 text-center text-gray-600">{jll}</td>
              <td class="px-3 py-2 border border-gray-100 text-center text-gray-600">{kf}</td>
              <td class="px-3 py-2 border border-gray-100 text-center text-gray-600 bg-green-50">{ys}</td>
              <td class="px-3 py-2 border border-gray-100 text-center text-gray-600 bg-blue-50">{gec}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="text-xs text-gray-400 mt-2">✓ covered &nbsp;·&nbsp; ~ partial proxy &nbsp;·&nbsp; ✗ absent</p>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 4: FAQs ───────────────────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">4 · Methodology FAQs</h3>
    <div class="space-y-4">

      <div>
        <p class="font-semibold text-gray-800 mb-1">Why did you add rental yield when it was missing from the original model?</p>
        <p class="text-gray-600 leading-relaxed">The original model was purely a capital gain proxy — it measured which districts had rising prices, not which were sound investments. MSCI/IPD, the most rigorous global property index, weights income return (yield) and capital return equally because total return is what actually reaches an investor's pocket. We have ADREC rental registration data covering all districts, so there was no data reason to exclude it. A district scoring well on price momentum but yielding 1.5% is a speculation, not an investment.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Why do you exclude off-plan transactions from the price momentum factor in Yield &amp; Stability?</p>
        <p class="text-gray-600 leading-relaxed">Off-plan pricing is set unilaterally by developers at launch — it reflects their margin expectations and marketing strategy, not what the market will pay. Knight Frank PIRI and Case-Shiller both use resale/secondary transactions only for their price series for this reason. Mixing developer-set prices into a median distorts the signal: a Aldar launch at a premium PSF would inflate an established district's apparent price trend even if the resale market had softened.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Doesn't penalising price volatility unfairly punish districts in their early appreciation phase?</p>
        <p class="text-gray-600 leading-relaxed">Yes — and that is precisely why we built two separate models. The price stability (inverse CoV) factor only appears in the Yield &amp; Stability score, which is applied to established districts where volatility is genuinely a risk signal. For Growth &amp; Early-Cycle districts, we deliberately omit the stability factor. Early-stage appreciation is inherently volatile — steep price jumps as the market discovers a new location are the upside, not a warning. Penalising Al Saadiyat Island's 2019–2022 CoV would have incorrectly labelled its strongest-return period as high-risk.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Are global indices like MSCI/IPD and JLL GRETI actually relevant to Abu Dhabi?</p>
        <p class="text-gray-600 leading-relaxed">Partially. These indices were calibrated on London, Singapore, and Tokyo — markets 30–50 years into their liquidity cycle, where the primary investment thesis is income return and capital gain is secondary. Abu Dhabi only opened freehold ownership to foreign nationals in Investment Zones from 2019 and more broadly from 2023. It is simultaneously building new geographies from scratch (artificial islands, master-planned communities) and developing a secondary resale market. The global indices' factor logic is correct; their weightings and which factors are appropriate depend entirely on where a district sits in its development cycle. Our dual-score model borrows the factor logic from MSCI/IPD (yield model) and CBRE/PGIM Emerging Markets (growth model) and applies each only where the data structure supports it.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Why is the off-plan → resale appreciation signal included in both models?</p>
        <p class="text-gray-600 leading-relaxed">It is the most Abu Dhabi-specific signal we can derive from ADREC data. When completed units trade above the off-plan entry price from the same district, it is direct evidence that buyers who purchased off-plan have seen real capital appreciation — the thesis for buying off-plan is validated. In the Yield &amp; Stability model it carries 10 pts as a supplementary signal (since resale market depth is the primary signal). In the Growth &amp; Early-Cycle model it carries 20 pts — it is the highest-quality signal available for a pre-completion district because it draws on any early completions or comparable ready stock nearby. It has no direct equivalent in global indices, which do not operate on a developer-pre-sale structure at district scale.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">What data sources power the scores, and how often do they update?</p>
        <p class="text-gray-600 leading-relaxed">All data is sourced exclusively from the Abu Dhabi Real Estate Centre (ADREC), published at dari.ae. Transaction data (sales price, AED/sqft, sale type, project name, district) is refreshed daily by ADInteract's automated scraper. Rental registration data (annual rent, property type, layout, district) is refreshed from ADREC's rental index. Scores are recomputed on every daily data refresh — the computed_at timestamp on each district reflects the exact moment of last calculation. ADInteract is independent and not affiliated with any developer, brokerage, or government body.</p>
      </div>

    </div>
  </div>

</div>
{/if}
