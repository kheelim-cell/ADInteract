import { writable, derived } from 'svelte/store';
import type { User } from '@supabase/supabase-js';
import { browser } from '$app/environment';
import { base } from '$app/paths';
import { supabase, supabaseEnabled } from '$lib/supabase';

// ── Core auth state ───────────────────────────────────────────────────────────
export const user            = writable<User | null>(null);
export const authLoading     = writable(true);
export const isAuthenticated = derived(user, ($u) => $u !== null);

// ── Modal visibility ──────────────────────────────────────────────────────────
export const showSignInModal = writable(false);
export const openSignIn      = () => showSignInModal.set(true);
export const closeSignIn     = () => showSignInModal.set(false);

// ── Profile data collected before OAuth redirect ──────────────────────────────
export interface PendingProfile {
	name:     string;
	identity: string;
	whatsapp: string;
}

// ── Google OAuth ──────────────────────────────────────────────────────────────
export async function signInWithGoogle(profile?: PendingProfile) {
	if (!supabase) return;
	if (profile && browser) {
		localStorage.setItem('pending_profile', JSON.stringify(profile));
	}
	const redirectTo =
		typeof window !== 'undefined'
			? `${window.location.origin}${base}/`
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
async function upsertProfile(u: User, profile?: PendingProfile) {
	if (!supabase) return;
	try {
		await supabase.from('profiles').upsert(
			{
				id:              u.id,
				auth_method:     'google',
				email:           u.email ?? null,
				full_name:       profile?.name     ?? u.user_metadata?.full_name ?? u.email ?? null,
				identity:        profile?.identity ?? null,
				whatsapp_number: profile?.whatsapp ?? null,
				avatar_url:      u.user_metadata?.avatar_url ?? null,
				last_login_at:   new Date().toISOString()
			},
			{ onConflict: 'id' }
		);
	} catch {
		/* silently fail — auth still works */
	}
}

// ── Initialize on browser ─────────────────────────────────────────────────────
if (browser && supabaseEnabled && supabase) {
	supabase.auth.getSession().then(({ data: { session } }) => {
		user.set(session?.user ?? null);
		authLoading.set(false);
	});

	supabase.auth.onAuthStateChange((_event, session) => {
		const u = session?.user ?? null;
		user.set(u);
		authLoading.set(false);

		if (_event === 'SIGNED_IN' && u) {
			// Recover profile data stored before the OAuth redirect
			let pending: PendingProfile | undefined;
			try {
				const raw = localStorage.getItem('pending_profile');
				if (raw) {
					pending = JSON.parse(raw);
					localStorage.removeItem('pending_profile');
				}
			} catch { /* ignore */ }

			upsertProfile(u, pending);
			closeSignIn();
		}
	});
} else if (browser) {
	// No Supabase configured — immediately unblock the UI
	authLoading.set(false);
}
