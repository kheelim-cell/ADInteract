import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

export const prerender = false;

const PROMPT = `You are a property data extraction assistant specialised in Abu Dhabi real estate.
Extract fields from the ready property listing image or PDF provided (e.g. a screenshot from Bayut, PropertyFinder, or similar portal).
Return ONLY a valid JSON object with exactly these keys (use null for anything you cannot confidently determine):

{
  "district": string | null,
  "layout": string | null,
  "project": string | null,
  "price": number | null,
  "livingArea": number | null,
  "balconyArea": number | null,
  "serviceChargePsf": number | null,
  "annualRent": number | null
}

Rules:
- district: Abu Dhabi area/district name. Examples: "Al Reem Island", "Yas Island", "Al Saadiyat Island", "Khalifa City", "Al Raha Beach", "Masdar City", "Fahid Island", "Al Hidayriyyat"
- layout: normalise to lowercase. Examples: "studio", "1 bed", "2 beds", "3 beds", "4 beds", "5 beds". Convert "3BR", "3 Bedroom", "Three Bedroom" → "3 beds"
- project: the development/building name (e.g. "Reem Nine", "Mangrove Place", "Ansam"). Use the exact project name as shown on the listing, NOT the developer name.
- price: the asking/listing price in AED as a plain number (no commas, no currency symbols). If given in millions (e.g. "AED 1.35M") → 1350000
- livingArea: internal living area (BUA/built-up area) in square feet. If given in sqm, multiply by 10.7639 and round to nearest integer. Do NOT include balcony/terrace in this figure.
- balconyArea: balcony or terrace area in square feet. If given in sqm, multiply by 10.7639 and round. Use null if not stated separately.
- serviceChargePsf: annual service charge per square foot in AED. Only include if explicitly stated (e.g. "AED 16/sqft service charge", "SC: 14.5 AED/sqft"). Do NOT estimate.
- annualRent: the current annual rent in AED if the property is tenanted/rented. Only include if the listing explicitly states the unit is currently rented and shows the rent amount. Use null for vacant properties or if rent is not shown.
Return ONLY the JSON object. No markdown code fences. No explanation.`;

export const POST: RequestHandler = async ({ request }) => {
	const apiKey = env.ANTHROPIC_API_KEY;
	if (!apiKey) {
		throw error(
			500,
			'ANTHROPIC_API_KEY not set. Add ANTHROPIC_API_KEY=sk-ant-... to your .env.local file.'
		);
	}

	let body: { fileData: string; mediaType: string };
	try {
		body = await request.json();
	} catch {
		throw error(400, 'Request body must be valid JSON');
	}

	const { fileData, mediaType } = body;
	if (!fileData || !mediaType) {
		throw error(400, 'Both fileData (base64 string) and mediaType are required');
	}

	const SUPPORTED = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
	if (!SUPPORTED.includes(mediaType)) {
		throw error(400, `Unsupported media type: ${mediaType}`);
	}

	const isPdf = mediaType === 'application/pdf';

	const fileBlock = isPdf
		? {
				type: 'document',
				source: { type: 'base64', media_type: 'application/pdf', data: fileData }
		  }
		: {
				type: 'image',
				source: { type: 'base64', media_type: mediaType, data: fileData }
		  };

	let anthropicRes: Response;
	try {
		anthropicRes = await fetch('https://api.anthropic.com/v1/messages', {
			method: 'POST',
			headers: {
				'x-api-key': apiKey,
				'anthropic-version': '2023-06-01',
				'content-type': 'application/json'
			},
			body: JSON.stringify({
				model: 'claude-opus-4-6',
				max_tokens: 512,
				messages: [
					{
						role: 'user',
						content: [fileBlock, { type: 'text', text: PROMPT }]
					}
				]
			})
		});
	} catch (fetchErr) {
		throw error(502, `Failed to reach Anthropic API: ${String(fetchErr)}`);
	}

	if (!anthropicRes.ok) {
		const errText = await anthropicRes.text().catch(() => '');
		throw error(502, `Anthropic API returned ${anthropicRes.status}: ${errText.slice(0, 300)}`);
	}

	const result = await anthropicRes.json();
	const rawText: string = result.content?.[0]?.text ?? '';

	let extracted: Record<string, unknown>;
	try {
		const cleaned = rawText
			.replace(/^```(?:json)?\r?\n?/, '')
			.replace(/\r?\n?```$/, '')
			.trim();
		extracted = JSON.parse(cleaned);
	} catch {
		throw error(
			502,
			`Could not parse JSON from Claude response. Raw: ${rawText.slice(0, 300)}`
		);
	}

	return json({ success: true, data: extracted });
};
