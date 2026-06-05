import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

export const prerender = false;

const TODAY = new Date().toISOString().split('T')[0]; // e.g. "2026-05-30"

const PROMPT = `You are a property data extraction assistant specialised in Abu Dhabi real estate.
Extract fields from the property listing image or document provided. Scan ALL visible pages/sections thoroughly.
Return ONLY a valid JSON object with exactly these keys (use null for anything you cannot confidently determine):

{
  "projectName": string | null,
  "developer": string | null,
  "district": string | null,
  "layout": string | null,
  "cost": number | null,
  "size": number | null,
  "yearsTillHandover": number | null,
  "serviceChargePsf": number | null
}

Rules:
- projectName: full development/tower name (e.g. "Rotana Residences Al Reem Island")
- developer: developer/builder name (e.g. "Royal Development Holding", "Aldar", "Imkan")
- district: Abu Dhabi area/district name. Examples: "Al Saadiyat Island", "Yas Island", "Al Reem Island", "Khalifa City", "Al Raha Beach", "Masdar City", "Fahid Island", "Al Hidayriyyat"
- layout: normalise to lowercase. Examples: "studio", "1 bed", "2 beds", "3 beds", "4 beds", "5 beds".
  Convert any of these formats → same output:
  "2BR", "2B", "2 Bedroom", "Two Bedroom", "2BR-2", "2B/2BR-2" → "2 beds"
  "1BR", "1B", "1 Bedroom", "One Bedroom", "1BR+S" → "1 bed"
  "Studio", "STU" → "studio"
  "3BR", "3B", "3 Bedroom", "Three Bedroom" → "3 beds"
- cost: the unit purchase/listing/sale price in AED as a plain number (no commas, no currency symbols).
  Look for labels like "Purchase Price", "Sale Price", "Unit Price", "Listing Price", "Price".
  If given in millions (e.g. "AED 2.825M") → 2825000
- size: the TOTAL unit area in square feet, including balcony if a total/gross figure is provided.
  Priority order: "Total Area" > "Gross Area" > "Net Area" > "Interior Area".
  If the document shows Interior + Balcony + Total, use the Total figure.
  If given in SQM, multiply by 10.7639 and round to nearest integer.
- yearsTillHandover: today is ${TODAY}. Calculate decimal years from today to the handover/completion date.
  Examples: "Q2 2028" from May 2026 → 2.1, "Q4 2027" → 1.4, "2026" → 0.5. Round to 1 decimal place.
- serviceChargePsf: annual service charge per square foot in AED. Only include if explicitly stated.
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

	// Validate supported media types
	const SUPPORTED = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
	if (!SUPPORTED.includes(mediaType)) {
		throw error(400, `Unsupported media type: ${mediaType}`);
	}

	const isPdf = mediaType === 'application/pdf';

	// Build the content block for the Anthropic API
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
				model: 'claude-opus-4-8',
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

	// Strip any accidental markdown code fences
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
