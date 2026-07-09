import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type RiskPreference = 'yield' | 'balanced' | 'growth';

export interface InvestorProfile {
  budget_min: number | null;
  budget_max: number | null;
  target_yield_pct: number | null;
  investment_horizon_years: number | null;
  risk_preference: RiskPreference;
  preferred_layouts: string[];
  visa_interest: boolean;
}

const STORAGE_KEY = 'adinteract_investor_profile';

function load(): InvestorProfile | null {
  if (!browser) return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as InvestorProfile) : null;
  } catch {
    return null;
  }
}

export const investorProfile = writable<InvestorProfile | null>(load());

if (browser) {
  investorProfile.subscribe((v) => {
    try {
      if (v == null) localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, JSON.stringify(v));
    } catch {}
  });
}

export function saveProfile(profile: InvestorProfile): void {
  investorProfile.set(profile);
}

export function clearProfile(): void {
  investorProfile.set(null);
}

export function calcDistrictMatch(
  profile: InvestorProfile,
  district: {
    medianPsf: number | null;
    grossYieldPct: number | null;
    score_type?: string;
    common_layouts?: string[];
  }
): number {
  let score = 0;

  // Budget fit (25 pts): median price within range
  if (profile.budget_min != null || profile.budget_max != null) {
    const psf = district.medianPsf ?? 0;
    const estPrice = psf * 900; // rough 900 sqft avg unit
    const minOk = profile.budget_min == null || estPrice >= profile.budget_min;
    const maxOk = profile.budget_max == null || estPrice <= profile.budget_max;
    if (minOk && maxOk) score += 25;
  } else {
    score += 25;
  }

  // Yield fit (25 pts)
  if (profile.target_yield_pct != null && district.grossYieldPct != null) {
    const ratio = district.grossYieldPct / profile.target_yield_pct;
    score += Math.min(25, Math.round(ratio * 25));
  } else {
    score += 12;
  }

  // Risk fit (25 pts)
  const st = district.score_type;
  if (profile.risk_preference === 'yield' && st === 'yield_stability') score += 25;
  else if (profile.risk_preference === 'growth' && st === 'growth_early_cycle') score += 25;
  else if (profile.risk_preference === 'balanced' && st === 'both') score += 25;
  else if (profile.risk_preference === 'balanced') score += 12;
  else score += 5;

  // Layout fit (25 pts)
  if (profile.preferred_layouts.length > 0 && district.common_layouts && district.common_layouts.length > 0) {
    const overlap = profile.preferred_layouts.some((l) => district.common_layouts!.includes(l));
    if (overlap) score += 25;
  } else {
    score += 12;
  }

  return Math.min(100, score);
}
