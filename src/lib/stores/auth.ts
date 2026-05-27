import { writable, derived, get } from 'svelte/store';
import type { User } from '@supabase/supabase-js';
import { browser } from '$app/environment';
import { supabase, supabaseEnabled } from '$lib/supabase';

// ── Core auth state ───────────────────────────────────────────────────────────
export const user         = writable<User | null>(null);
export const authLoading  = writable(true);
export const isAuthenticated = derived(user, ($u) => $u !== null);

// ── Modal visibility ──────────────────────────────────────────────────────────
export const showSignInModal = writable(false);
export const openSignIn  = () => showSignInModal.set(true);
export const closeSignIn = () => showSignInModal.set(false);

// ── Google OAuth ──────────────────────────────────────────────────────────────
export async function signInWithGoogle() {
	if (!supabase) return;
	const redirectTo =
		typeof window !== 'undefined'
			? window.location.origin + window.location.pathname.split('/').slice(0, -1).join('/') + '/'
			: '/';
	const { error } = await supabase.auth.signInWithOAuth({
		provider: 'google',
		options: { redirectTo }
	});
	if (error) throw error;
}

// ── Sign out ──────────────────────────────────────────────────────────────────
export async function signOut() {
	if (!supabase) return;
	await supabase.auth.signOut();
	user.set(null);
}

// ── Profile upsert (best-effort) ──────────────────────────────────────────────
async function upsertProfile(u: User, provider: 'google' | 'whatsapp') {
	if (!supabase) return;
	try {
		await supabase.from('profiles').upsert(
			{
				user_id:         u.id,
				provider,
				email:           u.email ?? null,
				display_name:    u.user_metadata?.full_name ?? u.email ?? null,
				whatsapp_number: u.user_metadata?.whatsapp_number ?? null,
				last_login_at:   new Date().toISOString()
			},
			{ onConflict: 'user_id' }
		);
	} catch {
		/* silently fail — auth still works */
	}
}

// ── Initialize on browser ────────────────────────────────────────────────────
if (browser && supabaseEnabled && supabase) {
	supabase.auth.getSession().then(({ data: { session } }) => {
		const u = session?.user ?? null;
		user.set(u);
		authLoading.set(false);
		if (u) upsertProfile(u, (u.app_metadata?.provider === 'google' ? 'google' : 'whatsapp'));
	});

	supabase.auth.onAuthStateChange((_event, session) => {
		const u = session?.user ?? null;
		user.set(u);
		authLoading.set(false);
		if (_event === 'SIGNED_IN' && u) {
			const provider = u.app_metadata?.provider === 'google' ? 'google' : 'whatsapp';
			upsertProfile(u, provider);
			closeSignIn();
		}
	});
} else if (browser) {
	// No Supabase configured — immediately mark as not loading, gate stays open
	authLoading.set(false);
}
