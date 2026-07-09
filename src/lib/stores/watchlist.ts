import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type WatchlistItem =
  | { type: 'project'; id: string; project_name: string; district: string; added_at: string; note?: string }
  | { type: 'deal'; id: string; label: string; url: string; added_at: string };

const STORAGE_KEY = 'adinteract_watchlist';

function load(): WatchlistItem[] {
  if (!browser) return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as WatchlistItem[]) : [];
  } catch {
    return [];
  }
}

export const watchlist = writable<WatchlistItem[]>(load());

if (browser) {
  watchlist.subscribe((v) => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(v)); } catch {}
  });
}

export function addProject(project_name: string, district: string): void {
  const id = `project_${project_name}`;
  watchlist.update((list) => {
    if (list.some((i) => i.id === id)) return list;
    return [...list, { type: 'project', id, project_name, district, added_at: new Date().toISOString() }];
  });
}

export function addDeal(label: string, url: string): void {
  const id = `deal_${Date.now()}`;
  watchlist.update((list) => [...list, { type: 'deal', id, label, url, added_at: new Date().toISOString() }]);
}

export function removeItem(id: string): void {
  watchlist.update((list) => list.filter((i) => i.id !== id));
}

export function clearAll(): void {
  watchlist.set([]);
}

export function isProjectSaved(project_name: string): boolean {
  // Called reactively via $watchlist — this is a helper for derived checks
  return false; // use store subscription in components
}
