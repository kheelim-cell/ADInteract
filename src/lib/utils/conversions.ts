export const SQM_TO_SQFT = 10.7639;

export function sqmToSqft(sqm: number | null | undefined): number | null {
	if (sqm == null || isNaN(sqm)) return null;
	return sqm * SQM_TO_SQFT;
}

export function sqftToSqm(sqft: number | null | undefined): number | null {
	if (sqft == null || isNaN(sqft)) return null;
	return sqft / SQM_TO_SQFT;
}

export function ratePerSqmToSqft(ratePerSqm: number | null | undefined): number | null {
	if (ratePerSqm == null || isNaN(ratePerSqm)) return null;
	return ratePerSqm / SQM_TO_SQFT;
}
