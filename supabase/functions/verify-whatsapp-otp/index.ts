import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
	if (req.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

	try {
		const { phone, otp } = await req.json();
		if (!phone || !otp) throw new Error('Phone number and OTP required');

		const normalized = phone.trim().replace(/\s+/g, '');
		if (!/^\+\d{7,15}$/.test(normalized)) throw new Error('Invalid phone number format');
		if (!/^\d{6}$/.test(otp)) throw new Error('OTP must be 6 digits');

		const supabaseAdmin = createClient(
			Deno.env.get('SUPABASE_URL')!,
			Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
			{ auth: { autoRefreshToken: false, persistSession: false } }
		);

		// 1. Find a valid, unused OTP for this number
		const { data: record, error: fetchErr } = await supabaseAdmin
			.from('whatsapp_otps')
			.select('id, otp_code, expires_at')
			.eq('phone_number', normalized)
			.eq('otp_code', otp)
			.eq('used', false)
			.gt('expires_at', new Date().toISOString())
			.order('created_at', { ascending: false })
			.limit(1)
			.maybeSingle();

		if (fetchErr) throw fetchErr;
		if (!record) throw new Error('Invalid or expired OTP');

		// 2. Mark OTP as used immediately (prevent replay)
		await supabaseAdmin
			.from('whatsapp_otps')
			.update({ used: true })
			.eq('id', record.id);

		// 3. Deterministic fake email identifier for this phone number
		const fakeEmail = `wa_${normalized.replace(/^\+/, '')}@adinteract.whatsapp`;

		// 4. Generate a magic-link token — creates the auth user on first sign-in,
		//    or reuses the existing one. The client exchanges this token for a session.
		const { data: linkData, error: linkErr } = await supabaseAdmin.auth.admin.generateLink({
			type: 'magiclink',
			email: fakeEmail,
			options: {
				shouldCreateUser: true,
				data: { whatsapp_number: normalized, auth_method: 'whatsapp' }
			}
		});

		if (linkErr) throw linkErr;

		const hashed_token = linkData?.properties?.hashed_token;
		if (!hashed_token) throw new Error('Failed to generate session token');

		// 5. Upsert profile row so we can look users up by phone later
		if (linkData?.user?.id) {
			await supabaseAdmin.from('profiles').upsert({
				id:              linkData.user.id,
				whatsapp_number: normalized,
				auth_method:     'whatsapp'
			});
		}

		return new Response(
			JSON.stringify({ success: true, hashed_token, email: fakeEmail }),
			{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		);
	} catch (e) {
		const msg = e instanceof Error ? e.message : 'Unknown error';
		return new Response(JSON.stringify({ error: msg }), {
			status:  400,
			headers: { ...corsHeaders, 'Content-Type': 'application/json' }
		});
	}
});
