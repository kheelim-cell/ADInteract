/**
 * Compounds an annual rate over a horizon using a decaying schedule instead of a flat
 * exponent: full rate for yrs 1–2, half rate for yrs 3–4, flat (0%) from yr 5 onward.
 * Reflects that near-term market comps are trustworthy while multi-year forecasts
 * carry far more uncertainty (elevated further by regional conflict risk).
 * `years` may be fractional (e.g. 2.5); the partial year is compounded at whichever
 * tier it falls into.
 */
export function decayedGrowth(annualRatePct: number, years: number): number {
	if (years <= 0) return 1;
	let multiplier = 1;
	let remaining = years;
	let yearIndex = 1;
	while (remaining > 0) {
		const chunk = Math.min(1, remaining);
		const rate = yearIndex <= 2 ? annualRatePct : yearIndex <= 4 ? annualRatePct / 2 : 0;
		multiplier *= Math.pow(1 + rate / 100, chunk);
		remaining -= chunk;
		yearIndex += 1;
	}
	return multiplier;
}
