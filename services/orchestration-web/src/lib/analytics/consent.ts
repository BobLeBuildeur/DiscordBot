import { browser } from '$app/environment';

/** Persisted choice for whether to show the banner again; PostHog opt-in is applied on load from this. */
export const ANALYTICS_CONSENT_KEY = 'orch_analytics_consent';
export const CONSENT_VERSION = '1';

export type StoredConsent = 'accepted' | 'declined';

export function readStoredConsent(): StoredConsent | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(ANALYTICS_CONSENT_KEY);
		if (raw === 'accepted' || raw === 'declined') return raw;
	} catch {
		/* private mode */
	}
	return null;
}

export function writeStoredConsent(value: StoredConsent): void {
	if (!browser) return;
	try {
		localStorage.setItem(ANALYTICS_CONSENT_KEY, value);
	} catch {
		/* ignore */
	}
}
