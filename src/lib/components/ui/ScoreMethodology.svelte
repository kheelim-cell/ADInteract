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
      Abu Dhabi's two market segments cannot be scored on the same framework. Applying a mature-market index to a pre-completion district penalises it for lacking rental income or resale history — the defining features of an early-cycle opportunity. Each district is classified automatically from ADREC data.
    </p>
    <div class="grid sm:grid-cols-2 gap-3">
      <div class="rounded-xl border-l-4 border-emerald-500 border border-gray-100 bg-gray-50 px-4 py-3">
        <p class="text-xs font-bold text-emerald-700 uppercase tracking-widest mb-1">Yield &amp; Stability</p>
        <p class="text-xs text-gray-600 leading-relaxed">Applied when <strong>&gt;60%</strong> of all-time transactions are ready/secondary-market. Established districts with active resale, rental benchmarks, and multi-year price history. Mirrors MSCI/IPD total-return logic: income (yield) + capital return (momentum), risk-adjusted.</p>
        <p class="text-xs text-gray-400 mt-1.5">e.g. Khalifa City, Al Reem Island, Corniche</p>
      </div>
      <div class="rounded-xl border-l-4 border-blue-500 border border-gray-100 bg-gray-50 px-4 py-3">
        <p class="text-xs font-bold text-blue-700 uppercase tracking-widest mb-1">Growth &amp; Early-Cycle</p>
        <p class="text-xs text-gray-600 leading-relaxed">Applied when <strong>&lt;40%</strong> of all-time transactions are ready — predominantly developer-launched, most units not yet completed. Mirrors CBRE/PGIM emerging market logic: demand velocity, developer confidence, forward appreciation.</p>
        <p class="text-xs text-gray-400 mt-1.5">e.g. Al Hidayriyyat, Al Jubail Island, new Saadiyat phases</p>
      </div>
    </div>
    <p class="text-xs text-gray-400 mt-2">Districts at 40–60% ready receive both scores side by side. Classification updates daily.</p>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 2: Factor tables ──────────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">2 · Factors, weights &amp; calculation</h3>

    <p class="text-xs font-semibold text-emerald-700 mb-2">Yield &amp; Stability (100 pts)</p>
    <div class="overflow-x-auto mb-4">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[22%]">Factor</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[10%]">Wt</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">How it's calculated</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Price momentum<br><span class="font-normal text-gray-400">ready only</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">30</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">% change in median AED/sqft for ready/resale transactions, last 12m vs prior 12m. Off-plan excluded (developer pricing ≠ market price). Capped ±40%. &lt;5 ready txns → neutral 15 pts.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Gross rental yield</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">25</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Median ADREC-registered annual rent ÷ median sale price × 100. &gt;8% → 25 pts · 6–8% → 22 · 4–6% → 16 · 2–4% → 8 · &lt;2% → 2. &lt;5 rents → neutral 12 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Liquidity</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">20</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Transactions last 3m ÷ avg 3m over prior 9m. Captures current activity, not historical size. Log-scaled to prevent volume outliers dominating.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Price stability<br><span class="font-normal text-gray-400">inverse CoV</span></td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">15</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Inverse of CoV (std ÷ mean) of quarterly median PSF over 24m. Lower volatility scores higher. CoV ≤0.05 → 15 pts; &gt;0.30 → 2 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Appreciation signal</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-emerald-700">10</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Ready median PSF ÷ off-plan median PSF (last 12m). Ratio &gt;1 = completed units trade above off-plan entry. One sale type only → neutral 5 pts.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-xs font-semibold text-blue-700 mb-2">Growth &amp; Early-Cycle (100 pts)</p>
    <div class="overflow-x-auto">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[22%]">Factor</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600 w-[10%]">Wt</th>
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">How it's calculated</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Off-plan velocity</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">30</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Off-plan txn count last 6m vs prior 6m. Accelerating ratio = developer launches finding buyers — primary demand signal in pre-completion markets. Ratio ≥3× → 30 pts.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Off-plan momentum</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">25</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">% change in off-plan median PSF, last 12m vs prior 12m. Rising developer pricing signals land appreciation confidence. Same ±40% cap as Y&amp;S.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Appreciation signal</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">20</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Same ready/off-plan ratio as Y&amp;S, weighted higher (20 vs 10 pts). Any proven appreciation in an early-cycle district is strong validation that the off-plan thesis is materialising.</td>
          </tr>
          <tr class="bg-gray-50">
            <td class="px-3 py-2 border border-gray-100 font-medium">Developer activity</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">15</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Unique projects with off-plan registrations last 12m vs prior 12m. More developers entering signals trajectory confidence. Ratio ≥1.5 → 15 pts; &lt;0.75 → 4 pts.</td>
          </tr>
          <tr>
            <td class="px-3 py-2 border border-gray-100 font-medium">Market entry momentum</td>
            <td class="px-3 py-2 border border-gray-100 font-semibold text-blue-700">10</td>
            <td class="px-3 py-2 border border-gray-100 text-gray-600">Off-plan txns last 3m vs rolling 3m avg over prior 9m. Forward signal for near-term buyer demand. Ratio ≥1.5 → 10 pts.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 3: Global benchmarks ──────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">3 · Coverage vs global benchmarks</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-xs border-collapse">
        <thead>
          <tr class="bg-gray-50">
            <th class="text-left px-3 py-2 border border-gray-100 font-semibold text-gray-600">Factor</th>
            <th class="text-center px-2 py-2 border border-gray-100 font-semibold text-gray-600">MSCI</th>
            <th class="text-center px-2 py-2 border border-gray-100 font-semibold text-gray-600">JLL</th>
            <th class="text-center px-2 py-2 border border-gray-100 font-semibold text-gray-600">KF</th>
            <th class="text-center px-2 py-2 border border-gray-100 font-semibold text-gray-600 bg-green-50">Y&amp;S</th>
            <th class="text-center px-2 py-2 border border-gray-100 font-semibold text-gray-600 bg-blue-50">G&amp;EC</th>
          </tr>
        </thead>
        <tbody>
          {#each [
            ['Price momentum',        '✓', '✓', '✓', '✓ 30', '✓ 25'],
            ['Rental yield',          '✓', '✓', '✗', '✓ 25', '✗'],
            ['Liquidity / depth',     '✓', '✓', '~', '✓ 20', '✓ 30'],
            ['Price stability',       '✓', '✓', '✗', '✓ 15', '~'],
            ['Off-plan appreciation', '✗', '✗', '✗', '✓ 10', '✓ 20'],
            ['Developer pipeline',    '✓', '✓', '✗', '✗',    '✓ 15'],
            ['Entry momentum',        '~', '~', '✗', '✓',    '✓ 10'],
          ] as [factor, msci, jll, kf, ys, gec]}
            <tr class="even:bg-gray-50">
              <td class="px-3 py-2 border border-gray-100 font-medium">{factor}</td>
              <td class="px-2 py-2 border border-gray-100 text-center text-gray-600">{msci}</td>
              <td class="px-2 py-2 border border-gray-100 text-center text-gray-600">{jll}</td>
              <td class="px-2 py-2 border border-gray-100 text-center text-gray-600">{kf}</td>
              <td class="px-2 py-2 border border-gray-100 text-center text-gray-600 bg-green-50">{ys}</td>
              <td class="px-2 py-2 border border-gray-100 text-center text-gray-600 bg-blue-50">{gec}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="text-xs text-gray-400 mt-2">✓ covered · ~ partial · ✗ absent</p>
  </div>

  <hr class="border-gray-100" />

  <!-- ── Section 4: FAQs ───────────────────────────────────────────── -->
  <div>
    <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">4 · FAQs</h3>
    <div class="space-y-4">

      <div>
        <p class="font-semibold text-gray-800 mb-1">Why add rental yield when the original model didn't include it?</p>
        <p class="text-gray-600 leading-relaxed">The original model was a pure capital gain proxy. MSCI/IPD weights income and capital return equally because total return is what reaches an investor's pocket. We have ADREC rental data for all districts, so there's no reason to exclude it. A district with rising prices but 1.5% yield is speculation, not investment.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Why exclude off-plan transactions from price momentum in Y&amp;S?</p>
        <p class="text-gray-600 leading-relaxed">Off-plan prices are set by developers at launch — they reflect margin expectations, not market clearing prices. Knight Frank PIRI and Case-Shiller use resale transactions only for this reason. Mixing developer pricing into the median distorts the signal: a premium-PSF launch would inflate an established district's trend even if the resale market had softened.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Doesn't penalising volatility unfairly punish early-appreciation districts?</p>
        <p class="text-gray-600 leading-relaxed">Yes — which is why we built two models. Stability (inverse CoV) only appears in Y&amp;S, applied to established districts where volatility is a genuine risk signal. G&amp;EC deliberately omits it. Early-stage appreciation is inherently volatile; those price jumps are the upside, not a warning.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">Are MSCI/IPD and JLL GRETI relevant to Abu Dhabi?</p>
        <p class="text-gray-600 leading-relaxed">Partially. Those indices were built on London, Singapore, and Tokyo — markets 30–50 years into their liquidity cycle. Abu Dhabi opened freehold to foreigners from 2019, and is still building new geographies from scratch. We borrow the factor logic from MSCI/IPD (Y&amp;S model) and CBRE/PGIM Emerging Markets (G&amp;EC model), applied only where the data supports it.</p>
      </div>

      <div>
        <p class="font-semibold text-gray-800 mb-1">What data powers the scores, and how often do they update?</p>
        <p class="text-gray-600 leading-relaxed">All data comes from ADREC (dari.ae) — transaction data (price, PSF, sale type, project, district) and rental registration data. Both are scraped daily; scores recompute on every refresh. ADInteract is independent and unaffiliated with any developer, brokerage, or government body.</p>
      </div>

    </div>
  </div>

</div>
{/if}
