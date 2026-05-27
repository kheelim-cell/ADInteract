import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
	if (req.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

	try {
		const { phone } = await req.json();
		if (!phone) throw new Error('Phone number required');

		// Normalize: strip spaces, ensure + prefix
		const normalized = phone.trim().replace(/\s+/g, '');
		if (!/^\+\d{7,15}$/.test(normalized)) throw new Error('Invalid phone number format');

		const supabase = createClient(
			Deno.env.get('SUPABASE_URL')!,
			Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
		);

		// Rate limit: block if an OTP was sent in the last 60 seconds for this number
		const { data: recent } = await supabase
			.from('whatsapp_otps')
			.select('created_at')
			.eq('phone_number', normalized)
			.eq('used', false)
			.gt('created_at', new Date(Date.now() - 60_000).toISOString())
			.limit(1)
			.maybeSingle();

		if (recent) throw new Error('Please wait 60 seconds before requesting a new OTP');

		// Generate 6-digit OTP
		const otp = String(Math.floor(100000 + Math.random() * 900000));
		const expiresAt = new Date(Date.now() + 5 * 60_000).toISOString(); // 5 min

		// Store OTP
		const { error: insertError } = await supabase.from('whatsapp_otps').insert({
			phone_number: normalized,
			otp_code:     otp,
			expires_at:   expiresAt
		});
		if (insertError) throw insertError;

		// Send via Twilio WhatsApp
		const twilioSid   = Deno.env.get('TWILIO_ACCOUNT_SID')!;
		const twilioToken = Deno.env.get('TWILIO_AUTH_TOKEN')!;
		const fromNumber  = Deno.env.get('TWILIO_WHATSAPP_FROM')!; // e.g. whatsapp:+14155238886

		const body = new URLSearchParams({
			From: fromNumber,
			To:   `whatsapp:${normalized}`,
			Body: `${otp} is your ADInteract verification code. For your security, do not share this code.`
		});

		const twilioRes = await fetch(
			`https://api.twilio.com/2010-04-01/Accounts/${twilioSid}/Messages.json`,
			{
				method:  'POST',
				headers: {
					'Content-Type':  'application/x-www-form-urlencoded',
					'Authorization': `Basic ${btoa(`${twilioSid}:${twilioToken}`)}`
				},
				body
			}
		);

		if (!twilioRes.ok) {
			const err = await twilioRes.json();
			throw new Error(err.message ?? 'Twilio error: failed to send WhatsApp message');
		}

		return new Response(JSON.stringify({ success: true }), {
			headers: { ...corsHeaders, 'Content-Type': 'application/json' }
		});
	} catch (e) {
		const msg = e instanceof Error ? e.message : 'Unknown error';
		return new Response(JSON.stringify({ error: msg }), {
			status:  400,
			headers: { ...corsHeaders, 'Content-Type': 'application/json' }
		});
	}
});
