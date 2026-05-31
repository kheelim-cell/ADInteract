import type { PageLoad, EntryGenerator } from './$types';
import rawSummaries from '$lib/data/district_summaries.json';

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

const summaries = rawSummaries as Record<string, DistrictSummary>;

// Build a reverse map: slug → district name (e.g. "al-reem-island" → "Al Reem Island")
const slugToDistrict: Record<string, string> = {};
for (const [districtName, s] of Object.entries(summaries)) {
  slugToDistrict[s.slug] = districtName;
}

// Generate one prerendered page per district slug  (e.g. /area/al-reem-island)
export const entries: EntryGenerator = () =>
  Object.values(summaries).map(s => ({ district: s.slug }));

export const prerender = true;

export const load: PageLoad = ({ params }) => {
  const districtName = slugToDistrict[params.district] ?? params.district;
  const summary      = summaries[districtName] ?? null;
  return { districtName, summary };
};
