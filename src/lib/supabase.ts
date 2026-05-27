import { createClient } from '@supabase/supabase-js';

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL     as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/** True only when both env vars are configured. Site works fine without them (all data visible). */
export const supabaseEnabled = !!(supabaseUrl && supabaseAnonKey);

export const supabase = supabaseEnabled
	? createClient(supabaseUrl!, supabaseAnonKey!)
	: null;
