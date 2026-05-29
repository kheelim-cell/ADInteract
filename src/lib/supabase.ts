import { createClient } from '@supabase/supabase-js';

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL     as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/** True only when both env vars are configured. Site works fine without them (all data visible). */
export const supabaseEnabled = !!(supabaseUrl && supabaseAnonKey);

export const supabase = supabaseEnabled
	? createClient(supabaseUrl!, supabaseAnonKey!)
	: null;

/**
 * When true, the Investor page requires an active Pro subscription (is_pro = true).
 * When false, the Investor page is fully open — no gating at all.
 *
 * Toggle: GitHub repo → Settings → Secrets → VITE_INVESTOR_PRO_GATED → update value
 *         then manually trigger the Deploy workflow (~3 min).
 */
export const investorProGated =
	import.meta.env.VITE_INVESTOR_PRO_GATED === 'true';

/**
 * URL of the Stan Store checkout page for ADInteract Pro.
 * Shown on the "Upgrade to Pro" button.
 */
export const stanStoreUrl =
	(import.meta.env.VITE_STAN_STORE_URL as string | undefined) ?? '';
