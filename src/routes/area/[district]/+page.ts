import type { PageLoad, EntryGenerator } from './$types';
import rawSummaries from '$lib/data/district_summaries.json';
import rawScores from '$lib/data/district_scores.json';

type DistrictSummary = {
  slug:          string;
  tx_count_all:  number;
  tx_count_12m:  number;
  median_psf:    number | null;
  p10_psf:       number | null;
  p90_psf:       number | null;
  median_price:  number | null;
  top_layouts:   string[];
  is_12m:        boolean;
  last_sale:     string;
};

// district_scores.json entries vary by score_type ("growth_early_cycle",
// "yield_stability", or "both") and only "gec"-bearing entries carry the
// specific off-plan-PSF-YoY momentum figure this page quotes (verified
// against the live rendered UI label "off-plan PSF YoY"). "yield_stability"
// entries have a differently-shaped "ys" momentum instead, which measures
// something else and isn't used here — gec is optional and genuinely absent
// for those, not a data error.
type GrowthScore = {
  gec?: {
    // pct_change is null when direction is "flat" (no other combination
    // appears in the data) — always check for null before formatting it.
    momentum: { pct_change: number | null; direction: 'up' | 'down' | 'flat' };
  };
};

const summaries = rawSummaries as Record<string, DistrictSummary>;
const scores    = rawScores as Record<string, GrowthScore>;

// Build a reverse map: slug → district name (e.g. "al-reem-island" → "Al Reem Island")
const slugToDistrict: Record<string, string> = {};
for (const [districtName, s] of Object.entries(summaries)) {
  slugToDistrict[s.slug] = districtName;
}

// Citywide rank by median AED/sqft, computed once from every district that
// actually has a median_psf — 7 of 96 currently don't, and are excluded from
// ranking rather than given a misleading position. Backs the FAQ's
// "is this district expensive" answer with a real, computable number instead
// of a fabricated neighbourhood comparison (no geographic-adjacency data
// exists anywhere in this dataset to answer that literally).
const psfRanked = Object.entries(summaries)
  .filter((entry): entry is [string, DistrictSummary & { median_psf: number }] => entry[1].median_psf != null)
  .sort(([, a], [, b]) => b.median_psf - a.median_psf);

const psfRankByDistrict: Record<string, { rank: number; total: number }> = {};
psfRanked.forEach(([name], i) => {
  psfRankByDistrict[name] = { rank: i + 1, total: psfRanked.length };
});

const citywideMedianPsf = (() => {
  const vals = psfRanked.map(([, s]) => s.median_psf); // already sorted desc
  if (!vals.length) return null;
  const mid = Math.floor(vals.length / 2);
  return vals.length % 2 === 0 ? (vals[mid - 1] + vals[mid]) / 2 : vals[mid];
})();

// Generate one prerendered page per district slug  (e.g. /area/al-reem-island)
export const entries: EntryGenerator = () =>
  Object.values(summaries).map(s => ({ district: s.slug }));

export const prerender = true;

// Override the global ssr=false: these pages exist FOR their prerendered HTML
// (SEO prose + og:image report cards). Without SSR the build emits empty shells.
export const ssr = true;

export const load: PageLoad = ({ params }) => {
  const districtName = slugToDistrict[params.district] ?? params.district;
  const summary      = summaries[districtName] ?? null;

  const psfRank = psfRankByDistrict[districtName] ?? null;
  const aboveCitywideMedian =
    summary?.median_psf != null && citywideMedianPsf != null
      ? summary.median_psf > citywideMedianPsf
      : null;

  // Off-plan PSF year-over-year momentum — only present for the 36 of 96
  // districts with enough off-plan activity to compute a growth score.
  // Deliberately NOT presented as a general "price trend" — it's specifically
  // an off-plan metric, and labeled as such wherever it's used.
  const offPlanMomentum = scores[districtName]?.gec?.momentum ?? null;

  return { districtName, summary, psfRank, aboveCitywideMedian, offPlanMomentum };
};
