import type { PageLoad, EntryGenerator } from './$types';
import rawSummaries from '$lib/data/district_summaries.json';

// Cast once so every consumer gets a typed object
const summaries = rawSummaries as Record<string, {
  tx_count_all:  number;
  tx_count_12m:  number;
  median_psf:    number | null;
  p10_psf:       number | null;
  p90_psf:       number | null;
  median_price:  number | null;
  top_layouts:   string[];
  is_12m:        boolean;
  last_sale:     string;
}>;

// Tell the static adapter which /area/[district] pages to generate.
// Reads from the generated JSON — no manual list to maintain.
export const entries: EntryGenerator = () =>
  Object.keys(summaries).map(district => ({ district }));

export const prerender = true;

export const load: PageLoad = ({ params }) => {
  const districtName = decodeURIComponent(params.district);
  return {
    districtName,
    summary: summaries[districtName] ?? null,
  };
};
