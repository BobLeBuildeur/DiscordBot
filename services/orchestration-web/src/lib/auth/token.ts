/**
 * Single owner for the analyst JWT used against the orchestration API (Bearer).
 * sessionStorage keeps the token out of default cross-tab leakage vs localStorage.
 * httpOnly cookies are a deployment follow-up when a BFF exists.
 */
const STORAGE_KEY = 'orchestration_access_token';

function decodePayload(token: string): { exp?: number } | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;
		const payload = parts[1];
		const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
		return JSON.parse(json) as { exp?: number };
	} catch {
		return null;
	}
}

export function getAccessToken(): string | null {
	if (typeof sessionStorage === 'undefined') return null;
	return sessionStorage.getItem(STORAGE_KEY);
}

export function setAccessToken(token: string): void {
	sessionStorage.setItem(STORAGE_KEY, token);
}

export function clearAccessToken(): void {
	sessionStorage.removeItem(STORAGE_KEY);
}

/** True when a non-expired JWT is stored (client-side exp check only). */
export function isAccessTokenValid(): boolean {
	const t = getAccessToken();
	if (!t) return false;
	const p = decodePayload(t);
	if (p?.exp === undefined) return false;
	return p.exp * 1000 > Date.now();
}
