import { error } from '@sveltejs/kit';
import { supabase } from '$lib/supabase';
import rawSummaries from '$lib/data/district_summaries.json';
import type { PageLoad } from './$types';

export const ssr = true;
export const prerender = false;

type DistrictSummary = {
	slug:          string;
	tx_count_12m:  number;
	median_psf:    number | null;
	median_price:  number | null;
	[key: string]: unknown;
};

const summaries = rawSummaries as Record<string, DistrictSummary>;

export const load: PageLoad = async ({ params }) => {
	if (!supabase) throw error(503, 'Service unavailable');

	const { data: broker, error: err } = await supabase
		.from('brokers')
		.select('*')
		.eq('slug', params.broker)
		.eq('active', true)
		.single();

	if (err || !broker) throw error(404, 'Broker page not found');

	const brokerDistricts = ((broker.districts as string[]) ?? [])
		.map((districtSlug: string) => {
			const entry = Object.entries(summaries).find(([, s]) => s.slug === districtSlug);
			if (!entry) return null;
			return { name: entry[0], ...entry[1] };
		})
		.filter((d): d is DistrictSummary & { name: string } => d !== null);

	return { broker, brokerDistricts };
};
